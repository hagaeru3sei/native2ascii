#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import sqlite3
from collections import OrderedDict
from bottle import Bottle, HTTPResponse

port = 8800
host = 'localhost'
app = Bottle()

## TODO: refactoring

class HttpResponse(object):
    """
    """
    def __init__(self, response_body, status):
        self.response_body = response_body
        self.status = status

    def response(self):
        response = HTTPResponse(status=200, body=self.response_body)
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

    def to_dict(self):
        """class Strings to dict converter
        :return: dict
        """
        r = {}
        r['id'] = self.id
        r['language'] = self.language
        r['key'] = self.key
        r['value'] = self.value
        r['description'] = self.description
        r['updated'] = self.updated
        return r


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

    conn = sqlite3.connect('var/db/native2ascii.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM strings')
    row = cur.fetchone()
    while row:
        records.append(Strings(touple(row)).to_dict())
        row = cur.fetchone()
    cur.close()
    conn.close()

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
    if len(language) == 0: err += 1
    if len(key) == 0: err += 1
    if len(value) == 0: err += 1
    if err > 0:
        result = '{"result":"NG"}'
        status = 400
        return HttpResponse(result, status).response()

    # save database
    conn = sqlite3.connect('var/db/native2ascii.db')
    cur = conn.cursor()
    sql = 'INSERT INTO strings (language, key, value, description, updated) VALUES (?, ?, ?, ?, ?)'
    cur.execute(sql, (language, key, value, description, updated))
    conn.commit()
    cur.close()
    conn.close()
    
    body = '{"response":"OK"}'
    status = 200
    return HttpResponse(body, status).response()


app.run(host=host, port=port, debug=True)

