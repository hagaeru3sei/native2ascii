#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import math
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
endpoint = 'http://' + host + ':' + str(port) + '/api'
app = Bottle()

# TODO: use plugin
# https://bottlepy.org/docs/dev/tutorial.html#route-specific-installation
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
    """
    """
    # TODO: refactoring
    content_type = 'application/json'
    response_body = ''
    headers = {}
    status = HttpStatus.NotFound
    http_response = None

    def __init__(self, response_body, status):
        self.headers = {}
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
            self.http_response.set_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
            self.http_response.set_header('Access-Control-Allow-Headers', 'Content-Type')
        logger.debug(self.http_response.headers)

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


class Validator:

    @staticmethod
    def validate(record) -> bool:
        err = 0
        key = record['key']
        value = record['value']
        language = record['language']

        # error check
        if language is None or len(language) == 0:
            err += 1
        if key is None or len(key) == 0:
            err += 1
        if value is None or len(value) == 0:
            err += 1

        if err > 0:
            return False
        return True


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
    {
      total: 0,
      per_page: 20,
      current_page: 0,
      last_page: 0,
      prev_page_url: 'http://localhost/api?page=1'
      next_page_url: 'http://localhost/api?page=2'
      data: [
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
    }
    """
    page = request.query.page
    logger.debug(page is "")
    per_page = 15
    if page is None or page is "" or int(page) <= 0:
        page = 1
    else:
        page = int(page)

    offset = per_page * (page - 1)
    limit = per_page

    sql = 'SELECT count(id) FROM strings'
    cur.execute(sql)
    total = cur.fetchone()[0]
    last_page = math.ceil(total/per_page)
    url = endpoint + '?page=%d'

    prev_url = ''
    if page > 1:
        prev_url = url % (page - 1)

    next_url = ''
    if page < last_page:
        next_url = url % (page + 1)

    logger.debug("GET /api")

    records = dict()
    records['total'] = total
    records['per_page'] = per_page
    records['current_page'] = page
    records['last_page'] = last_page
    records['prev_page_url'] = prev_url
    records['next_page_url'] = next_url
    records['from'] = offset
    records['to'] = 15
    records['data'] = []

    sql = 'SELECT * FROM strings WHERE 1=1 LIMIT %d, %d' % (offset, limit)
    logger.debug(sql)
    cur.execute(sql)
    row = cur.fetchone()
    while row:
        records['data'].append(Strings(tuple(row)).to_dict())
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
        .set_content_type('text/plain; charset=utf-8')\
        .add_header('Content-Length', str(len(body)))\
        .add_header('Content-Disposition', 'attachment; filename="message_%s.properties"' % language) \
        .response()


@app.route('/api/upload', method='POST')
@app.route('/api/upload/<language>', method='POST')
def upload(language='en') -> HTTPResponse:
    """Upload property file
    :return:
    """
    lang = request.forms.get('language')
    upload = request.files.get('property_file')

    logger.debug("lang: %s" % lang)
    logger.debug(upload)
    logger.debug("filename: %s" % upload.filename)

    return HttpResponse('{}', HttpStatus.OK).response(is_cors=True)


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
    logger.debug(request.body.getvalue())
    json_string = request.body.getvalue().decode('utf-8')
    logger.debug("JSON Request: " + json_string)

    try:
        data = json.loads(json_string)
    except Exception as e:
        logger.error(e)
        return HttpResponse('{"result":"NG"}', HttpStatus.BadRequest).response()

    for language in data.keys():
        record = data[language]
        record['language'] = language

        key = record['key']
        value = record['value']
        description = record['description']
        updated = int(time.time())

        # error check
        if Validator.validate(record) is False:
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
    logger.debug('DELETE')
    record_id = request.query.id
    try:
        complex(record_id)
    except ValueError as e:
        logger.error(e)
        HttpResponse('{"result":"NG"}', HttpStatus.BadRequest).response(is_cors=True)

    sql = "DELETE FROM strings WHERE id=?"
    try:
        conn.execute(sql, (record_id,))
    except Exception as e:
        logger.error(e)

    return HttpResponse('{"result":"OK"}', HttpStatus.OK).response(is_cors=True)


app.run(host=host, port=port, debug=True)
