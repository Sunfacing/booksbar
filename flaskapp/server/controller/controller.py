import pymysql
import os
import datetime
import plotly.express as px
import plotly
import json
from flask import Flask, render_template, request, redirect, session, jsonify
from flask.helpers import url_for
from flask_bcrypt  import Bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager


from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import re
import redis
from server import app, bcrypt
from server import db
import boto3
from collections import UserList, defaultdict


from server.models.product_model import *
from server.models.user_model import *
from datetime import timedelta
import datetime
import pytz
import random


client = boto3.client('s3', region_name='us-east-2')


connection = pymysql.connect(
    host = os.getenv('host'),
    user = os.getenv('user'),
    passwd = os.getenv('passwd'),
    database = os.getenv('database'),
    port = int(os.getenv('port')),
    cursorclass = pymysql.cursors.DictCursor,
    autocommit=True
)
cursor = connection.cursor()

r= redis.Redis.from_url('redis://flaskproject.gtlinm.0001.use2.cache.amazonaws.com:6379')


ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'jfif'])
EXPIRE = 3600
# TODAY = datetime.datetime.now(pytz.timezone('US/Pacific')).strftime("%Y-%m-%d")
TODAY = '2021-11-06'
YESTERDAY = (datetime.datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
# BUCKET = 'stylishproject'
MONTH_AGO = (datetime.datetime.now(pytz.timezone('Asia/Taipei')) - timedelta(days=15)).strftime("%Y-%m-%d")


@app.route('/', methods=['GET', 'POST'])
def index(period='month', user_id='0'):
    period = request.args.get('period', period)
    user_id = request.args.get('user_id', user_id)
    if user_id != '0':
        books = homepage_by_track(period, TODAY, MONTH_AGO, user_id)
    else:
        books = homepage_by_all(period, TODAY, MONTH_AGO)

    category_hash = get_category()
    try:
        product_list = defaultdict(dict)
        for book in books:
            subcate_id = book['category_id']
            cate_nm = category_hash[subcate_id]['category']
            subcate_nm = category_hash[subcate_id]['subcategory']
            data = {'isbn_id': book['isbn_id'],
                    'subcategory': subcate_nm,
                    'title': book['title'],
                    'cover_photo': book['cover_photo'],
                    'description': book['description'],
                    'publish_date': book['publish_date'],
                    'author': book['author']
            }
            if not product_list[cate_nm]: product_list[cate_nm] = [data]
            else: product_list[cate_nm].append(data)
    except Exception as e:
        print(e)
    return render_template('index.html', product_list=product_list, period=period, user_id=user_id)


@app.route('/<section_nm>', methods=['GET', 'POST'])
def section(section_nm='文學', category_nm='all', subcate_nm='all', page=1):
    section_nm = request.args.get('section_nm', section_nm)
    
    checker = CategoryList.query.filter_by(section=section_nm).first()  
    if checker is None:
        return render_template('404.html'), 404
    category_nm = request.args.get('category_nm', category_nm)
    subcate_nm = request.args.get('subcate_nm', subcate_nm)
    books = db.session.execute("SELECT * FROM bookbar.category_list")
    page = request.args.get('page', page) 
    cate_list = defaultdict(list)
    nav_sec = defaultdict(dict)
    for book in books:
        section = book['section']
        nav_sec[section] = section
        if section == section_nm:
            category = book['category']
            subcategory = book['subcategory']
            cate_list[category].append(subcategory)
    subcate_list = cate_list[category_nm]
    if category_nm != 'all':
        product_list = get_catalog_subcategory(subcate_nm, page=page)
        html_page = 'subcate.html'                                    
  
    else:
        return_list = get_catalog_section(section_nm, MONTH_AGO, TODAY)
        product_list = []
        for product in return_list:
            product_list.append(product)
        html_page = 'section.html'

    book_counts = get_subcate_book_counts(subcate_nm)
    ttl_pages = 0
    shown_pages = defaultdict(dict)
    for book in book_counts:
        ttl_pages = (book[0] / 20) 
    if int(page) - 1 == 0:
        shown_pages['pre'] = -1
    else:
        shown_pages['pre'] = int(page) - 1

    if ttl_pages - int(page) < 0 :
        shown_pages['next'] = -1
    else:
        shown_pages['next'] = int(page) + 1

    shown_pages['current'] = page

    return render_template(html_page, nav_sec=nav_sec, 
                                cate_list=cate_list,
                                subcate_list=subcate_list,
                                current_sec=section_nm,
                                current_cate=category_nm,
                                current_sub=subcate_nm,
                                product_list=product_list,
                                shown_pages=shown_pages)





@app.route('/product/<isbn_id>', methods=['GET', 'POST'])
def product(isbn_id=None):
    try:
        isbn_id = request.args.get('isbn_id', isbn_id)
        books = db.session.execute("SELECT * FROM bookbar.category_list")
        nav_sec = defaultdict(dict)
        for book in books:
            section = book['section']
            nav_sec[section] = section

        eslite = defaultdict(dict)
        kingstone = defaultdict(dict)
        momo = defaultdict(dict)
        try:
            info_list = get_book_info(isbn_id=isbn_id, date=TODAY)
        except:
            info_list = get_book_info(isbn_id=isbn_id, date=YESTERDAY)
        for info in info_list:
            platform = info['platform']
            if platform == 1:
                kingstone['section'] = info['section']
                kingstone['category'] = info['category']
                kingstone['subcategory'] = info['subcategory']
                kingstone['category_id'] = info['category_id']
                kingstone['title'] = info['title']
                kingstone['publish_date']= info['publish_date']
                kingstone['author'] = info['author']
                kingstone['author_id'] = info['author_id']
                kingstone['isbn_id'] = info['isbn_id']
                kingstone['ISBN'] = info['ISBN']
                kingstone['page'] = info['page']
                kingstone['publisher_id'] = info['publisher_id']
                kingstone['publisher'] = info['publisher']
                kingstone['size'] = info['size']
                kingstone['price'] = info['price']
                kingstone['cover_photo'] = info['cover_photo']
                kingstone['product_url'] = info['product_url']
            elif platform == 2:
                eslite  = info
            else:
                momo = info       
            if not momo['price']:
                momo['price'] = 0
            if not eslite['price']:
                eslite['price'] = 0
            if not kingstone['price']:
                kingstone['price'] = 0

        pics = get_book_pics(isbn_id)
        pic_list = []
        i = 2
        for pic in pics:
            pic_list.append([pic['pics'], i])
            i += 1

        comment_list = get_book_comments(isbn_id)
        comments = []
        for each in comment_list:       
            comments.append([each['date'].date(), each['comment']])

        if 'loggedin' in session:
            user_id = session['id']
            isbn_id = kingstone['isbn_id'] 
            db.session.add(UserFavorite(user_id=user_id, track_type=4, type_id=isbn_id))
            db.session.commit()
            tracking_hash = check_user_track_by_product(user_id, kingstone['category_id'], isbn_id, kingstone['author_id'])
        else:
            tracking_hash = {}
    except Exception as e:
        print(e)


    return render_template('product.html', nav_sec=nav_sec, 
                                        kingstone=kingstone, 
                                        eslite=eslite, 
                                        momo=momo, 
                                        pic_list=pic_list,
                                        comment_list=comments,
                                        tracking_hash=tracking_hash)



@app.route('/api/product/bookinfo/<isbn_id>')
def book_info(isbn_id=None):
    isbn_id = request.args.get('isbn_id', isbn_id)
    result = api_book_info(isbn_id)
    response = defaultdict(dict)


    for info in result:
        if info['table_of_content'] == 'None': response['table_of_content'] = "目前無目錄大綱"
        else: response['table_of_content'] = info['table_of_content']

        if not info['description']: response['description'] = "目前無內容簡介"
        else: response['description'] = info['description']

        if not info['author_intro']: response['author_intro'] = "目前無作者介紹"
        else: response['author_intro'] = info['author_intro']
    

    return response


@app.route('/member')
def member(track_type=0):
    if 'loggedin' in session:
        user_id = session['id']
        track_type = request.args.get('track_type', track_type)
        if track_type == '1':
            cate_list = defaultdict(dict)
            result = get_user_favor_category(user_id)
            for cate in result:
                section = cate['section']
                categroy = cate['category']
                subcategory = cate['subcategory']
                if not cate_list[section]: cate_list[section] = [[categroy, subcategory]]
                else: cate_list[section].append([categroy, subcategory])
            return render_template('favor_cate.html', cates=cate_list)
        elif track_type == '2':
            user_id = session['id'] 
            date = '2021-11-06'
            books = get_user_favor_book(user_id, date)
            book_list = defaultdict(dict)
            final_list = defaultdict(dict)
            for book in books:
                category = book['category']
                try:
                    isbn_id = book['isbn_id']
                    if book['platform'] == 1:                        
                        book_list[isbn_id]['title'] = book['title']
                        book_list[isbn_id]['cover_photo'] = book['cover_photo']
                        book_list[isbn_id]['ks_product_url'] = book['product_url']
                        book_list[isbn_id]['ks_price'] = int(book['price'])
                        if not book['price']:
                            book_list[isbn_id]['ks_price'] = 0
                    if book['platform'] == 2:
                        book_list[isbn_id]['es_product_url'] = book['product_url']
                        book_list[isbn_id]['es_price'] = int(book['price'])
                        if not book_list[isbn_id]['es_price']:
                            book_list[isbn_id]['es_price'] = 0
                    if book['platform'] == 3:
                        book_list[isbn_id]['mm_product_url'] = book['product_url']
                        book_list[isbn_id]['mm_price'] = int(book['price'])
                        if not book_list[isbn_id]['mm_price']:
                            book_list[isbn_id]['mm_price'] = 0
                    final_list[category][isbn_id] = book_list[isbn_id]
                    
                except Exception as e:
                    print(e)
            return render_template('favor_book.html', books=final_list)

        elif track_type == '3':
            authors = get_user_favor_author(user_id)
            author_list = defaultdict(dict)
            for author in authors:
                isbn_id = author['isbn_id']
                name = author['name']
                title = author['title']
                publish_date = author['publish_date'].date()
                if not author_list[name]: author_list[name] = [[isbn_id, title, publish_date]]
                else: author_list[name].append([isbn_id, title, publish_date])
            return render_template('favor_author.html', authors=author_list)
        
        else:
            activity_counts = summerize_user_activity(user_id)
            browse_history = check_user_browsing_history(user_id)
            return render_template('member.html', activity_counts=activity_counts, browse_history=browse_history)
    else:
        return redirect(url_for('login'))




@app.route('/api/login', methods=['POST'])
def login(email=None, pwd=None):
    
    email = request.args.get('email', email)
    password = request.args.get('pwd', pwd)
    print(email, password)
    response = defaultdict(dict)
    try:
        user = UserInfo.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):           
            session['loggedin'] = True
            session['id'] = user.id
            session['username'] = user.username
            response['response'] = '登入成功'
            return response
        else: 
            response['response'] = "帳號或密碼有誤, 請重新嘗試"
            return response

    except:
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
            


@app.route('/logout')
def logout():
    session.pop('id', None)
    session.pop('username', None)
    session.pop('loggedin', None)
    return redirect(url_for('index'))




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

        user = db.session.execute("SELECT * FROM user_favorite WHERE user_id={} AND track_type={} AND type_id={}".format(user_id, track_type, type_id))
        for data in user:
            if data['user_id']:
                db.session.execute("DELETE FROM user_favorite WHERE user_id={} AND track_type={} AND type_id={}".format(user_id, track_type, type_id))
                db.session.commit()
                response['response'] = 'cancelled'
                return response
        db.session.add(UserFavorite(user_id=user_id, track_type=track_type, type_id=type_id))
        db.session.commit()
        response['response'] = 'added'
        return response

    else:
        response['response'] = 'no'
        return response


# @app.route('/keyword', methods=['GET', 'POST'])
# def search(search=None):
#     term = request.args.get('search', search)
#     result = search_by_term(term)
#     product_list = defaultdict(dict)
#     count = 0
#     for product in result:
#         categroy = product['category']
#         data = {
#         'isbn_id': product['isbn_id'],
#         'title': product['title'],
#         'cover_photo': product['cover_photo'],
#         'author': product['author'],
#         'description': product['description'],
#         }
#         if not product_list[categroy]: product_list[categroy] = [data]
#         else: product_list[categroy].append(data)
#         count += 1
#     return render_template('search.html', product_list=product_list, term=term, count=count)



@app.route('/keyword', methods=['GET', 'POST'])
def search(search=None):
    term = request.args.get('search', search)
    keyword_result = search_by_term(term)
    product_list = defaultdict(dict)

    duplicate_hash = defaultdict(dict)

    count = 0
    for product in keyword_result:
        isbn_id = product['isbn_id']
        categroy = product['category']
        data = {
        'isbn_id': isbn_id,
        'title': product['title'],
        'cover_photo': product['cover_photo'],
        'author': product['author'],
        'description': product['description'],
        }
        if not product_list[categroy]: product_list[categroy] = [data]
        else: product_list[categroy].append(data)

        duplicate_hash[isbn_id] = 1
        count += 1

    author_result = search_by_author(term)
    for each in author_result:
        isbn_id = each['isbn_id']
        if not duplicate_hash[isbn_id]:
            categroy = each['category']
            data = {
            'isbn_id': isbn_id,
            'title': each['title'],
            'cover_photo': each['cover_photo'],
            'author': each['author'],
            'description': each['description'],
            }
            if not product_list[categroy]: product_list[categroy] = [data]
            else: product_list[categroy].append(data)
            count += 1


    return render_template('search.html', product_list=product_list, term=term, count=count)














@app.route('/author', methods=['GET', 'POST'])
def author(name=None):
    name = request.args.get('name', name)
    try:
        result = search_by_author(name)
        product_list = defaultdict(dict)
        count = 0
        for product in result:
            categroy = product['category']
            data = {
            'isbn_id': product['isbn_id'],
            'title': product['title'],
            'cover_photo': product['cover_photo'],
            'author': product['author'],
            'description': product['description'],
            }
            if not product_list[categroy]: product_list[categroy] = [data]
            else: product_list[categroy].append(data)
            count += 1
    except Exception as e:
        print(e)
    return render_template('search.html', product_list=product_list, term=name, count=count)