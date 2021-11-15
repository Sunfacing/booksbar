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
from collections import defaultdict


from server.models.product_model import *
from server.models.user_model import *
from datetime import timedelta
import datetime
import html



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
TODAY = datetime.datetime.today().strftime('%Y-%m-%d')
BUCKET = 'stylishproject'



@app.route('/')
def index():
    books = db.session.execute("""SELECT isbn_id, category_id, b.title, b.cover_photo, b.publish_date, b.product_url, a.name AS author FROM isbn_catalog AS i
                                INNER JOIN book_info AS b
                                ON i.id = b.isbn_id
                                INNER JOIN author AS a
                                ON b.author = a.id
                                WHERE category_id IN(138, 90, 84) AND b.platform = 1 and b.publish_date > '2021-10-01'
                                ORDER BY publish_date DESC
                                LIMIT 8""")
    collections = []
    row = []
    i = 0
    for book in books:
        if i % 4 == 0 and i > 1:
            collections.append(row)
            row = []
        row.append(book)
        i += 1
    collections.append(row)
    return render_template('index.html', collections=collections)
    

@app.route('/<section_nm>', methods=['GET'])
def section(section_nm='文學', category_nm='all', subcate_nm='all', page=1):
    section_nm = request.args.get('section_nm', section_nm)
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
    if category_nm != 'all' and subcate_nm != 'all':
        product_list = get_catalog_subcategory(subcate_nm, page=page)
        html_page = 'subcate.html'                                    
    elif category_nm != 'all' and subcate_nm == 'all':
        product_list = []   
        html_page = 'subcate.html'  
    else:
        return_list = get_catalog_section(section_nm)
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





@app.route('/product/<isbn_id>')
def product(isbn_id=None):
    try:
        isbn_id = request.args.get('isbn_id', isbn_id)
        books = db.session.execute("SELECT * FROM bookbar.category_list")
        cate_list = defaultdict(list)
        nav_sec = defaultdict(dict)
        for book in books:
            section = book['section']
            nav_sec[section] = section

        eslite = defaultdict(dict)
        kingstone = defaultdict(dict)
        momo = defaultdict(dict)
        TODAY = datetime.datetime.now().strftime("%Y-%m-%d") 
        try:
            info_list = get_book_info(isbn_id=isbn_id, date='2021-11-06')
        except:
            info_list = get_book_info(isbn_id=isbn_id, date='2021-11-06')
        for info in info_list:
            platform = info['platform']
            if platform == 1:
                kingstone['section'] = info['section']
                kingstone['category'] = info['category']
                kingstone['subcategory'] = info['subcategory']
                kingstone['category_id'] = info['category_id']
                kingstone['title'] = info['title']
                kingstone['publish_date']= info['publish_date'].date()
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
    for key in result:
        
        response['author_intro'] = key['author_intro']

        response['description'] = key['description']
        response['table_of_content'] = key['table_of_content']
        if key['table_of_content'] == 'None':
            response['table_of_content'] = ''

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







@app.route('/login', methods=['GET', 'POST'])
def login():
    form = request.form
    if request.method == 'POST' and 'email' in form and 'password' in form:
        email = form['email']
        password = form['password']
        try:
            user = UserInfo.query.filter_by(email=email).first()
        except Exception as e:
            print(e)

        if user and bcrypt.check_password_hash(user.password, password):
            session['loggedin'] = True
            session['id'] = user.id
            session['username'] = user.username
            return redirect(url_for('index'))
        else:
            msg = "帳號或密碼有誤, 請重新嘗試"
            return render_template('login.html', msg=msg)
    return render_template('login.html', msg='')



@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('email', None)
    session.pop('password', None)
    return redirect(url_for('index'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = request.form
    msg = ''
    if request.method == 'POST' and 'email' in form and 'password' in form:
        email = form['email']
        username = email.split('@')[0]
        password = form['password']
        user = UserInfo.query.filter_by(email=email).first()
        if user:
            msg = '此帳號已註冊'
        else:
            password = bcrypt.generate_password_hash(password)
            user = UserInfo(email=email, password=password, username=username, source='native', token='')
            db.session.add(user)
            db.session.commit()
            session['id'] = user.id
            session['username'] = user.username
            return redirect(url_for('index'))
    return render_template('signup.html', msg=msg) 




@app.route('/favorite', methods=['POST'])
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


@app.route('/api/product')
def search(search=None):
    term = request.args.get('search', search)
    result = search_by_term(term)
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
    return render_template('search.html', product_list=product_list, term=term, count=count)