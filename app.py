import requests
import os
import json
import time
from flask import Flask, request, redirect, send_from_directory
import base64
from bs4 import BeautifulSoup
from hashlib import sha1

urls = {}
app = Flask(__name__)


@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('static/', path)


@app.route('/')
def index():
    return send_from_directory('static/', 'index.html')


@app.route('/index.html')
def redirectNoFile():
    return redirect('/')


@app.errorhandler(404)
def not_found(e):
    return redirect('/')


@app.route('/generate')
def gen():
    url = request.args.get('url')
    if url == None:
        return "400 (Bad Request)", 400
    if len(url) > 500:
        return "414 (Request-URI Too Long)", 414

    path = 'static/cache/{}.js'.format(sha1(url.encode('utf-8')).hexdigest())
    url = base64.b64decode(url).decode('utf-8')

    if "/pubhtml" not in url:
        return "404 (Not Found)", 404

    if os.path.isfile(path):
        if(time.time() - os.path.getmtime(path)) > 120:
            os.remove(path)
        else:
            return "418 (I'm a teapot)", 418

    response = requests.get(url)
    html = BeautifulSoup(response.text, 'html.parser').find(
        id='sheets-viewport')
    obj = {}
    if html == None:
        return "404 (Not Found)", 404
    for r in html.findAll('tr'):
        d = r.findAll('td')
        if len(d) == 2:
            obj[d[0].text] = d[1].text
        elif len(d) in range(3, 20):
            if d[2].text == "":
                obj[d[0].text] = d[1].text
                continue
            arr = []
            for i in range(1, len(d)):
                arr.append(d[i].text)
            obj[d[0].text] = arr

    obj = "var db = " + json.dumps(obj) + ";"
    with open(path, 'a') as f:
        f.write(obj)
    return path[7:]


if __name__ == '__main__':
    app.run(debug=True)
