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
            kingstone['category_id'] = info['category_id']
            kingstone['title'] = info['title']
            kingstone['publish_date']= info['publish_date'].date()
            kingstone['author'] = info['author']
            kingstone['isbn_id'] = info['isbn_id']
            kingstone['ISBN'] = info['ISBN']
            kingstone['page'] = info['page']
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
            momo['price'] = ''
        if not eslite['price']:
            eslite['price'] = ''
        if not kingstone['price']:
            kingstone['price'] = ''

    pics = get_book_pics(isbn_id)
    pic_list = []
    i = 2
    for pic in pics:
        pic_list.append([pic['pics'], i])
        i += 1
    return render_template('product.html', nav_sec=nav_sec, 
                                        kingstone=kingstone, 
                                        eslite=eslite, 
                                        momo=momo, 
                                        pic_list=pic_list)



@app.route('/product/api/bookinfo/<isbn_id>')
def book_info(isbn_id=None):
    isbn_id = request.args.get('isbn_id', isbn_id)
    result = api_book_info(isbn_id)
    response = defaultdict(dict)
    for key in result:
        response['author_intro'] = key['author_intro']
        response['description'] = key['description']
        response['table_of_content'] = key['table_of_content']
    return response





@app.route('/login', methods=['GET', 'POST'])
def login():
    form = request.form
    if request.method == 'POST' and 'email' in form and 'password' in form:
        email = form['email']
        password = form['password']
        user = UserInfo.query.filter_by(email=email).first()
        if bcrypt.check_password_hash(user.password, password):
            print(email, user.password, password)
        if user:
            session['loggedin'] = True
            session['id'] = user.id
            session['email'] = user.email
            msg =  "Logged In, Welcome"
            return f"hi {user.id}"
        else:
            msg = "Oops! Incorrect email / password"
            return msg
    return render_template('login.html')



@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('email', None)
    session.pop('password', None)
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = request.form
    msg = ''
    if request.method == 'POST' and 'email' in form and 'password' in form:
        email = form['email']
        password = form['password']
        user = UserInfo.query.filter_by(email=email).first()
        if user:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', password):
            msg = 'Username must contain only characters and numbers!'
        elif not password or not email:
            msg = 'Please fill out the form!'
        else:
            password = bcrypt.generate_password_hash(password)
            user = UserInfo(email=email, password=password, username='test', source='native', token='')
            db.session.add(user)
            db.session.commit()
            return 'done'
        # return render_template('member.html', msg=msg)
    elif request.method == 'POST':
        msg = 'Please fill out the form'
    return render_template('signup.html', msg=msg) 




@app.route('/api/favorite', methods=['POST'])
def add_to_favorite(subcate=None, author=None, product=None):
    response = defaultdict(dict)
    if 'loggedin' in session:
        user_id = session['id']
        subcate = request.args.get('subcate', subcate)
        author = request.args.get('author', author)
        product = request.args.get('product', product)
        if subcate: 
            track_type = 1
            type_id = subcate
        elif product: 
            track_type = 2
            type_id = product
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