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


@app.route('/api')
def main():
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
    status = 200

    return HttpResponse(body, status).response()


@app.route('/api', method='POST')
def update():
    """
    """
    err = 0
    language = request.forms.get('language')
    key = request.forms.get('key')
    value = request.forms.get('value')
    description = request.forms.get('description')
    updated = int(time.time())

    # error check
    if len(language) == 0:
        err += 1
    if len(key) == 0:
        err += 1
    if len(value) == 0:
        err += 1
    if err > 0:
        logger.error("Invalid request. language:%s, key:%s, value:%s" % (language, key, value,))
        result = '{"result":"NG"}'
        status = 400
        return HttpResponse(result, status).response()

    # save database
    cur.executescript("BEGIN TRANSACTION")
    sql = 'INSERT INTO strings (language, key, value, description, updated) VALUES (?, ?, ?, ?, ?)'
    cur.execute(sql, (language, key, value, description, updated))
    conn.commit()

    body = '{"response":"OK"}'
    status = 200
    logger.info("Saved record.")
    return HttpResponse(body, status).response()


app.run(host=host, port=port, debug=True)
