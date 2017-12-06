#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import math
import json
import sqlite3
import logging
import re
from configparser import ConfigParser
from bottle import Bottle, HTTPResponse, request

# TODO: refactoring

config = ConfigParser()
config.read('src/res/settings.ini')

logging.basicConfig(
    level=eval(config['logging']['level']),
    format=config['logging']['format'],
    filename=config['logging']['path'])
logger = logging.getLogger(__name__)

table_name = config['database']['tableName']

port = config['server']['port']
host = config['server']['host']
endpoint = config['server']['endpoint']

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
        self.category = row[2]
        self.key = row[3]
        self.value = row[4]
        self.description = row[5]
        self.updated = row[6]

    def to_dict(self) -> {}:
        """class Strings to dict converter
        :return: dict
        """
        return {'id': self.id,
                'language': self.language,
                'category': self.category,
                'key': self.key,
                'value': self.value,
                'description': self.description,
                'updated': self.updated}


class StringConverter:
    """
    """
    @staticmethod
    def ascii2native(args) -> str:
        """Ascii to Native code
        :param args:
        :return:
        """
        logger.debug("ascii2native")
        return bytes(args, 'utf-8').decode('unicode_escape')

    @staticmethod
    def native2ascii(args) -> str:
        """Native to Ascii code
        :param args:
        :return:
        """
        logger.debug("native2ascii")
        return bytes(args, 'unicode_escape').decode('utf-8')


class StringsDao(object):

    table_name = 'strings'

    def __init__(self):
        pass

    def find_all(self) -> []:
        """Return all records
        :return: list
        """
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
        """Validate http request
        :param record:
        :return:
        """
        err = 0
        key = record['key']
        value = record['value']
        language = record['language']
        category = record['category']

        # error check
        if language is None or len(language) == 0:
            err += 1
        if category is None or len(category) == 0:
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


@app.route('/categories')
def categories() -> HTTPResponse:
    """Return categories
    Please check the res/default.ini [categories] section.
    example
      { 'categories': ['none', 'default'] }
    none is default value in db.strings table.
    :return: HTTPResponse
    """
    values = config['categories']['values']
    languages = values.split(',')
    body = json.dumps({'categories': languages})

    return HttpResponse(body, HttpStatus.OK).response()


@app.route('/api', method='GET')
def main() -> HTTPResponse:
    """Return records
    Records example:
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
          category: 'none',
          key : 'key1',
          value : 'value1',
          description : 'desc1',
          updated : 12345
        }
        ,...
      ]
    }
    :return: HTTPResponse
    """
    logger.debug("GET /api")

    filter_param = request.query.filter
    where = ''
    if filter_param is not None and filter_param is not "":
        where = """AND (key LIKE '%%%s%%' OR value LIKE '%%%s%%' OR description LIKE '%%%s%%')
                """ % (filter_param, filter_param, filter_param)
        logger.debug(where)

    order_param = request.query.sort
    order_by = ''
    if order_param is not None and order_param is not "":
        column, sort_order = order_param.split('|')
        order_by = 'ORDER BY %s %s' % (column, sort_order, )

    page = request.query.page
    logger.debug(page is "")
    per_page = 15
    if page is None or page is "" or int(page) <= 0:
        page = 1
    else:
        page = int(page)

    offset = per_page * (page - 1)
    limit = per_page

    sql = 'SELECT count(id) FROM strings WHERE 1=1 %s' % (where, )
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

    sql = 'SELECT * FROM strings WHERE 1=1 %s %s LIMIT %d, %d' \
          % (where, order_by, offset, limit)
    logger.debug(sql)
    cur.execute(sql)
    row = cur.fetchone()
    while row:
        records['data'].append(Strings(tuple(row)).to_dict())
        row = cur.fetchone()
    body = json.dumps(records)

    return HttpResponse(body, HttpStatus.OK).response()


@app.route('/api/dl/<language>/<category>', method='GET')
def download(language, category) -> HTTPResponse:
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
        if category != record.category:
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
def upload(language) -> HTTPResponse:
    """Upload property file
    :return:
    """
    logger.debug("UPDATE")
    category = request.forms.get('category')
    uploaded_file = request.files.get('property_file')

    logger.debug(uploaded_file)
    logger.debug("filename: %s" % uploaded_file.filename)
    logger.debug(dir(uploaded_file.file).__str__())

    m = re.match("^message_([a-z]+).properties$", uploaded_file.filename)
    if m is not None:
        language = m.group(1)
    logger.debug("lang: %s" % language)

    patt = re.compile("^[^=]+=.+$")

    cur.executescript("BEGIN TRANSACTION")

    line = uploaded_file.file.readline()
    while line:
        line = line.decode('utf-8')
        logger.debug(line)

        match = patt.match(line)
        if match is None:
            line = uploaded_file.file.readline()
            continue
        logger.debug(match)

        key, value = line.split('=', 1)
        value = StringConverter.ascii2native(value[:-1])
        updated = int(time.time())

        logger.debug(key + "=" + value)

        q = "SELECT COUNT(id) FROM strings WHERE language=? AND category=? AND key=?"
        cur.execute(q, (language, category, key,))
        count = cur.fetchone()[0]
        if count == 0:
            sql = "INSERT INTO strings (language, category, key, value, updated) VALUES (?, ?, ?, ?, ?)"
            cur.execute(sql, (language, category, key, value, updated))
        else:
            sql = "UPDATE strings SET value=?, updated=? WHERE language=? AND category=? AND key=?"
            cur.execute(sql, (value, updated, language, category, key))
        line = uploaded_file.file.readline()

    try:
        conn.commit()
    except Exception as e:
        logger.error(e)
        return HttpResponse('{}', HttpStatus.InternalServerError).response(is_cors=True)

    return HttpResponse('{}', HttpStatus.OK).response(is_cors=True)


@app.route('/api', method='OPTIONS')
def check_cors() -> HTTPResponse:
    """For CORS
    :return: HTTPResponse
    """
    return HttpResponse('{}', HttpStatus.OK).response()


@app.route('/api', method='POST')
def update() -> HTTPResponse:
    """Update record
    Request JSON example:
    {
      'language' : {
        'category': {
          'key' : '',
          'value' : '',
          'description' : '',
        },
      },,,
    }
    :return: HTTPResponse
    """
    logger.debug(request.body.getvalue())
    json_string = request.body.getvalue().decode('utf-8')
    logger.debug("JSON Request: " + json_string)

    try:
        data = json.loads(json_string)
    except Exception as e:
        logger.error(e)
        return HttpResponse('{"result":"NG"}', HttpStatus.BadRequest).response()

    #cur.executescript("BEGIN TRANSACTION")

    for language in data.keys():
        category_with_record = data[language]
        for category in category_with_record.keys():
            record = category_with_record[category]
            record['category'] = category
            record['language'] = language

            category = record['category']
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
            q = "SELECT COUNT(id) FROM strings WHERE language=? AND category=? AND key=?"
            cur.execute(q, (language, category, key,))
            count = cur.fetchone()[0]
            if count == 0:
                sql = 'INSERT INTO strings (language, category, key, value, description, updated) ' \
                      'VALUES (?, ?, ?, ?, ?, ?)'
                cur.execute(sql, (language, category, key, value, description, updated))
            else:
                sql = 'UPDATE %s SET value=?, description=?, updated=? ' \
                      'WHERE language=? AND category=? AND key=?' % table_name
                cur.execute(sql, (value, description, updated, language, category, key))
            logger.debug(sql)

    try:
        conn.commit()
    except Exception as e:
        logger.error(e)

    body = '{"result":"OK"}'
    logger.info("Saved record.")

    return HttpResponse(body, HttpStatus.OK).response()


@app.route("/api", method='DELETE')
def delete() -> HTTPResponse:
    """Delete request id
    :return: HTTPResponse
    """
    logger.debug('DELETE')
    record_id = request.query.id
    try:
        complex(record_id)
    except ValueError as e:
        logger.error(e)
        HttpResponse('{"result":"NG"}', HttpStatus.BadRequest).response(is_cors=True)

    sql = "DELETE FROM strings WHERE id=?"
    cur.execute(sql, (record_id,))
    try:
        conn.commit()
    except Exception as e:
        logger.error(e)

    return HttpResponse('{"result":"OK"}', HttpStatus.OK).response(is_cors=True)


app.run(host=host, port=port, debug=True)
