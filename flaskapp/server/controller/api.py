from collections import defaultdict
import re

from flask import request, redirect, session
from flask.helpers import url_for

from server import app, bcrypt
from server import db
from server.models.product_model import *
from server.models.user_model import *
from server.controller.util import *



@app.route('/api/product/bookinfo/<isbn_id>')
def book_info(isbn_id=None):
    isbn_id = request.args.get('isbn_id', isbn_id)
    result = api_book_info(isbn_id)
    response = defaultdict(dict)
    for info in result:
        response['table_of_content'] = introduction_checker(info['table_of_content'], "目前無目錄大綱")
        response['description'] = introduction_checker(info['description'], "目前無內容簡介")
        response['author_intro'] = introduction_checker(info['author_intro'], "目前無作者介紹")
    return response


@app.route('/api/login', methods=['POST'])
def login(email=None, pwd=None):
    email = request.args.get('email', email)
    password = request.args.get('pwd', pwd)
    response = defaultdict(dict)
    user = UserInfo.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        store_user_session(user)
        response['response'] = '登入成功'
        return response
    response['response'] = "帳號或密碼有誤, 請重新嘗試"
    return response


@app.route('/api/register', methods=['POST'])
def register(email=None, pwd=None):
    email = request.args.get('email', email)
    password = request.args.get('pwd', pwd)
    username = email.split('@')[0]
    response = defaultdict(dict)
    user = UserInfo.query.filter_by(email=email).first()
    if user:
        response['response'] = '此帳號已註冊'
    elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
        response['response'] = 'E-mail 格式有誤'
    elif not re.match(r'[A-Za-z0-9]+', email):
        response['response'] = '請勿使用空白建'
    elif not password or not email:
        response['response'] = '請完整填入E-mail與密碼'
    else:
        password = bcrypt.generate_password_hash(password)
        user = UserInfo(email=email, password=password, username=username, source='native', token='')
        create_data(user)
        user = UserInfo.query.filter_by(email=email).first()
        store_user_session(user)
        response['response'] = '註冊成功'
    return response


@app.route('/api/favorite', methods=['GET', 'POST', 'DELETE'])
def add_to_favorite(subcate=None, author=None, price=None):
    response = defaultdict(dict)
    if 'loggedin' not in session:
        response['message'] = 'no'
        return response
    else:
        user_id = session['id']
        subcate = request.args.get('subcate', subcate)
        author = request.args.get('author', author)
        price = request.args.get('price', price)
        if subcate:
            track_type = TrackType.FAVORITE_CATEGORY.value
            type_id = subcate
        elif price:
            track_type = TrackType.FAVORITE_BOOK.value
            type_id = price
        elif author:
            track_type = Platform.KINGSTONE.value
            type_id = author
        user = check_user_favorite(user_id, track_type, type_id)
        for data in user:
            user_id = data['user_id']
        if user_id and request.method == 'DELETE':
            delete_user_favorite(user_id, track_type, type_id)
            response['message'] = 'cancelled'
        if user_id and request.method == 'POST':
            added_favorite = UserFavorite(user_id=user_id, track_type=track_type, type_id=type_id)        
            create_data(added_favorite)
            response['message'] = 'added'
        return response


@app.route('/api/logout')
def logout():
    session.pop('id', None)
    session.pop('username', None)
    session.pop('loggedin', None)
    return redirect(url_for('index'))