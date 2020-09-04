import requests
import os
import json
import time
from flask import Flask, request, redirect, send_from_directory
import base64
from bs4 import BeautifulSoup
from hashlib import sha1
from termcolor import colored
import traceback

app = Flask(__name__)


def convert(text):
    html = BeautifulSoup(text, 'html.parser')
    html = html.find(id='sheets-viewport')
    if html == None:
        return None
    obj = {}
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
                if d[2].text == "":
                    continue
                arr.append(d[i].text)
            obj[d[0].text] = arr
    return obj


@app.route('/generate')
def gen():
    url = request.args.get('url')
    if url == None:
        return "400 (Bad Request)", 400
    if len(url) > 500:
        return "414 (Request-URI Too Long)", 414

    # Name of temp file storing the JS
    file = sha1(url.encode('utf-8')).hexdigest() + ".js"

    # Real path of the temp file
    path = 'cache/{}'.format(file)

    # Decode the spreadsheet URL
    url = base64.b64decode(url).decode('utf-8')

    # Verify URL
    if "https://docs.google.com/spreadsheets/" not in url or "/pubhtml" not in url:
        return "404 (Not Found)", 404

    # Check if cache already exists and that it has not been modified for more than 2 minutes
    if os.path.isfile(path):
        if(time.time() - os.path.getmtime(path)) > 120:
            os.remove(path)
        else:
            return "418 (I'm a teapot)", 418

    try:
        r = requests.get(url, stream=True, timeout=1)
    except Exception:
        return "400 (Bad request)", 400

    size = 0
    buff = b""

    for chunk in r.iter_content(1024):
        size += len(chunk)
        if size > 1024*1024:
            r.close()
            return "413 (Request Entity Too Large)", 413
        else:
            buff += chunk

    obj = convert(buff)

    if obj == None:
        return "404 (Not Found)", 404

    obj = "var db = " + json.dumps(obj) + ";"
    with open(path, 'a') as f:
        f.write(obj)
    return file


@app.errorhandler(Exception)
def catch(e):
    print(colored("\n[ERROR]", "red", attrs=["bold"]))
    print(traceback.print_exc())
    print("")
    return "400 (Bad request)", 400


@app.route('/<path:path>')
def static_files(path):
    if path.endswith('.js'):
        return send_from_directory('cache/', path)
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


if __name__ == '__main__':
    app.run(debug=True)
