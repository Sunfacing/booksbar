import datetime
import os
from collections import defaultdict
from datetime import timedelta
import pymysql
import plotly.express as px
import plotly
from flask import render_template, request, redirect, session, jsonify
from flask.helpers import url_for
import re
from server import app, bcrypt
from server import db
import pytz

from server.models.product_model import *
from server.models.user_model import *




@app.route('/api/product/bookinfo/<isbn_id>')
def book_info(isbn_id=None):
    isbn_id = request.args.get('isbn_id', isbn_id)
    result = api_book_info(isbn_id)
    response = defaultdict(dict)
    for info in result:
        if info['table_of_content'] == 'None':
            response['table_of_content'] = "目前無目錄大綱"
        else:
            response['table_of_content'] = info['table_of_content']

        if not info['description']:
            response['description'] = "目前無內容簡介"
        else:
            response['description'] = info['description']

        if not info['author_intro']:
            response['author_intro'] = "目前無作者介紹"
        else:
            response['author_intro'] = info['author_intro']
    return response


@app.route('/api/login', methods=['POST'])
def login(email=None, pwd=None):
    email = request.args.get('email', email)
    password = request.args.get('pwd', pwd)
    response = defaultdict(dict)
    user = UserInfo.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        session['loggedin'] = True
        session['id'] = user.id
        session['username'] = user.username
        response['response'] = '登入成功'
        return response
    response['response'] = "帳號或密碼有誤, 請重新嘗試"
    return response

@app.route('/api/register', methods=['GET', 'POST'])
def register(email=None, pwd=None):
    email = request.args.get('email', email)
    password = request.args.get('pwd', pwd)
    username = email.split('@')[0]

    response = defaultdict(dict)
    response['response'] = "帳號或密碼有誤, 請重新嘗試"
    try:
        user = UserInfo.query.filter_by(email=email).first()
        if user:
            response['response'] = '此帳號已註冊'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            response['response'] = 'E-mail 格式有誤'
        elif not re.match(r'[A-Za-z0-9]+', password):
            response['response'] = '請勿使用空白建'
        elif not password or not email:
            response['response'] = '請完整填入E-mail與密碼'
        else:
            try:
                password = bcrypt.generate_password_hash(password)
                user = UserInfo(email=email, password=password, username=username, source='native', token='')
                db.session.add(user)
                db.session.commit()
                user = UserInfo.query.filter_by(email=email).first()
                session['loggedin'] = True
                session['id'] = user.id
                session['username'] = user.username
                response['response'] = '註冊成功'
            except Exception:
                response['response'] = '請勿包含空白鍵'
                return response
            return response
    except:
        response['response'] = '輸入格式有誤'
        return response
    return response

@app.route('/api/favorite', methods=['GET', 'POST'])
def add_to_favorite(subcate=None, author=None, price=None):
    response = defaultdict(dict)
    if 'loggedin' in session:
        user_id = session['id']
        subcate = request.args.get('subcate', subcate)
        author = request.args.get('author', author)
        price = request.args.get('price', price)
        if subcate:
            track_type = 1
            type_id = subcate
        elif price:
            track_type = 2
            type_id = price
        elif author:
            track_type = 3
            type_id = author
        user = db.session.execute("SELECT * FROM user_favorite\
                                    WHERE user_id={} AND track_type={} AND type_id={}"
                                    .format(user_id, track_type, type_id))
        for data in user:
            if data['user_id']:
                db.session.execute("DELETE FROM user_favorite\
                                    WHERE user_id={} AND track_type={} AND type_id={}"
                                    .format(user_id, track_type, type_id))
                db.session.commit()
                response['response'] = 'cancelled'
                return response
        db.session.add(UserFavorite(user_id=user_id, track_type=track_type, type_id=type_id))
        db.session.commit()
        response['response'] = 'added'
        return response
    response['response'] = 'no'
    return response