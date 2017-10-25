#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import json
import sqlite3
import logging
from configparser import ConfigParser
from bottle import Bottle, HTTPResponse, request

# TODO: refactoring

config = ConfigParser()
config.read('src/res/default.ini')
logging.basicConfig(
    level=eval(config['logging']['level']),
    format=config['logging']['format'],
    filename=config['logging']['path'])
logger = logging.getLogger(__name__)
port = 8800
host = 'localhost'
app = Bottle()

conn = sqlite3.connect('var/db/native2ascii.db', timeout=5)
cur = conn.cursor()


class HttpStatus:
    # Success
    OK = 200

    # Redirection
    NotModified = 304

    # Client Error
    BadRequest = 400
    Forbidden = 403
    NotFound = 404

    # Server Error
    InternalServerError = 500


class HttpResponse(object):
    """TODO: refactoring
    """
    content_type = 'application/json'
    response_body = ''
    headers = {}
    status = HttpStatus.NotFound
    http_response = None

    def __init__(self, response_body, status):
        self.response_body = response_body
        self.status = status
        self.set_content_type(self.content_type)
        self.http_response = HTTPResponse(status=self.status, body=self.response_body)

    def add_header(self, name, value):
        self.headers[name] = value
        return self

    def set_content_type(self, content_type):
        self.headers['Content-type'] = content_type
        return self

    def response(self, is_cors=True) -> HTTPResponse:
        """
        :param is_cors: boolean
        :return:
        """
        for k in self.headers.keys():
            self.http_response.set_header(k, self.headers[k])
        if is_cors:
            self.http_response.set_header('Access-Control-Allow-Origin', '*')
            self.http_response.set_header('Access-Control-Allow-Headers', 'Content-Type')
        logger.debug(self.headers)

        return self.http_response


class Strings(object):
    """
    """
    def __init__(self, row):
        self.id = row[0]
        self.language = row[1]
        self.key = row[2]
        self.value = row[3]
        self.description = row[4]
        self.updated = row[5]

    def to_dict(self) -> {}:
        """class Strings to dict converter
        :return: dict
        """
        return {'id': self.id,
                'language': self.language,
                'key': self.key,
                'value': self.value,
                'description': self.description,
                'updated': self.updated}


class StringConverter:
    """
    """
    @staticmethod
    def ascii2native(args) -> str:
        """"""
        logger.debug("ascii2native")
        return bytes(args, 'utf-8').decode('unicode_escape')

    @staticmethod
    def native2ascii(args) -> str:
        """"""
        logger.debug("native2ascii")
        return bytes(args, 'unicode_escape').decode('utf-8')


class StringsDao(object):

    table_name = 'strings'

    def __init__(self):
        pass

    def find_all(self) -> []:
        records = []
        cur.execute('SELECT * FROM %s' % self.table_name)
        row = cur.fetchone()
        while row:
            records.append(Strings(tuple(row)))
            row = cur.fetchone()
        return records


@app.route('/lang')
def lang() -> HTTPResponse:
    """Return languages for this application.
    Please check the res/default.ini [languages] section.
    example return value:
      { 'languages': ['en', 'ja'] }
    :return: HTTPResponse
    """
    values = config['languages']['values']
    languages = values.split(',')
    body = json.dumps({'languages': languages})

    return HttpResponse(body, HttpStatus.OK).response()


@app.route('/api', method='GET')
def main() -> HTTPResponse:
    """Records example:
    [
      {
        id : 1,
        language : 'ja',
        key : 'key1',
        value : 'value1',
        description : 'desc1',
        updated : 12345
      }
      ,...
    ]
    """
    logger.debug("GET /api")
    records = []
    cur.execute('SELECT * FROM strings')
    row = cur.fetchone()
    while row:
        records.append(Strings(tuple(row)).to_dict())
        row = cur.fetchone()
    body = json.dumps(records)

    return HttpResponse(body, HttpStatus.OK).response()


@app.route('/api/dl/<language>', method='GET')
def download(language) -> HTTPResponse:
    """Download property file.
    :return:
    """
    languages = config['languages']['values']
    if language not in languages.split(','):
        return HttpResponse('', HttpStatus.BadRequest).response()

    records = StringsDao().find_all()
    lines = []
    for record in records:
        if language != record.language:
            continue
        k = record.key
        v = StringConverter.native2ascii(record.value)
        lines.append(k + '=' + v)

    body = '\n'.join(lines)

    return HttpResponse(body, HttpStatus.OK)\
        .set_content_type('text/plain')\
        .add_header('Content-Length', str(len(body)))\
        .add_header('Content-Disposition', 'attachment; filename=message_%s.properties' % language)\
        .response()


@app.route('/api', method='OPTIONS')
def check_cors() -> HTTPResponse:
    """For CORS
    :return: HTTPResponse
    """
    return HttpResponse('{}', HttpStatus.OK).response()


@app.route('/api', method='POST')
def update() -> HTTPResponse:
    """
    """
    err = 0
    logger.debug(request.body.getvalue())
    json_string = request.body.getvalue().decode('utf-8')
    logger.debug("JSON Request: " + json_string)

    try:
        data = json.loads(json_string)
    except Exception as e:
        logger.error(e)
        return HttpResponse('{"result":"NG"}', HttpStatus.BadRequest).response()

    for lang_code in data.keys():
        language = lang_code
        record = data[language]

        key = record['key']
        value = record['value']
        description = record['description']
        updated = int(time.time())

        # error check
        if language is None or len(language) == 0:
            err += 1
        if key is None or len(key) == 0:
            err += 1
        if value is None or len(value) == 0:
            err += 1
        if err > 0:
            logger.error("Invalid request. language:%s, key:%s, value:%s" % (language, key, value,))
            result = '{"result":"NG"}'
            return HttpResponse(result, HttpStatus.BadRequest).response()

        if description is None:
            description = ''

        # save database
        cur.executescript("BEGIN TRANSACTION")
        sql = 'INSERT INTO strings (language, key, value, description, updated) VALUES (?, ?, ?, ?, ?)'
        try:
            cur.execute(sql, (language, key, value, description, updated))
        except Exception as e:
            logger.error(e)

    try:
        conn.commit()
    except Exception as e:
        logger.error(e)

    body = '{"result":"OK"}'
    logger.info("Saved record.")

    return HttpResponse(body, HttpStatus.OK).response()


@app.route("/api", method='DELETE')
def delete() -> HTTPResponse:
    sql = "DELETE FROM strings"
    try:
        conn.execute(sql)
    except Exception as e:
        logger.error(e)

    return HttpResponse('{"result":"OK"}', HttpStatus.OK).response()


app.run(host=host, port=port, debug=True)
