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
    """
    """
    def __init__(self, response_body, status):
        self.response_body = response_body
        self.status = status

    def response(self) -> HTTPResponse:
        response = HTTPResponse(status=self.status, body=self.response_body)
        response.set_header('Content-type', 'application/json')
        response.set_header('Access-Control-Allow-Origin', '*')
        return response


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
                'value': StringConverter.ascii2native(self.value),
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


@app.route('/api')
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
    records = []

    logger.debug("GET /api")

    cur.execute('SELECT * FROM strings')
    row = cur.fetchone()
    while row:
        records.append(Strings(tuple(row)).to_dict())
        row = cur.fetchone()

    body = json.dumps(records)

    return HttpResponse(body, HttpStatus.OK).response()


@app.route('/api', method='POST')
def update() -> HTTPResponse:
    """
    """
    err = 0
    logger.debug(request.body)
    json_string = request.body.getvalue().decode('utf-8')
    logger.debug(json_string)

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
        cur.execute(sql, (language, key, value, description, updated))

    try:
        conn.commit()
    except Exception as e:
        logger.error(e)

    body = '{"result":"OK"}'
    logger.info("Saved record.")
    return HttpResponse(body, HttpStatus.OK).response()


app.run(host=host, port=port, debug=True)
