import pymysql
import os
import datetime
import plotly.express as px
import plotly
import json
from flask import Flask, render_template, request, redirect, send_from_directory, jsonify, abort, current_app
from flask.helpers import url_for
from flask_bcrypt  import Bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager


from dotenv import load_dotenv
from werkzeug.utils import secure_filename

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
                                WHERE category_id IN(32, 108, 112) AND b.platform = 1 and b.publish_date > '2021-11-01'
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
def section(section_nm='文學', category_nm='all', subcate_nm='all', type=None):
    section_nm = request.args.get('section_nm', section_nm)
    category_nm = request.args.get('category_nm', category_nm)
    subcate_nm= request.args.get('subcate_nm', subcate_nm)
    books = db.session.execute("SELECT * FROM bookbar.category_list")
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
        product_list = get_catalog_subcategory(subcate_nm)
        page = 'subcate.html'                                    
    elif category_nm != 'all' and subcate_nm == 'all':
        product_list = []   
        page = 'subcate.html'  
    else:
        return_list = get_catalog_section(section_nm)
        product_list = []
        for product in return_list:
            product_list.append(product)
        page = 'section.html'

    # print(product_list[:3])
    return render_template(page, nav_sec=nav_sec, 
                                cate_list=cate_list,
                                subcate_list=subcate_list,
                                current_sec = section_nm,
                                current_cate=category_nm,
                                current_sub=subcate_nm,
                                product_list=product_list)



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
    # print(TODAY)
    try:
        info_list = get_book_info(isbn_id=isbn_id, date='2021-11-06')
    except:
        info_list = get_book_info(isbn_id=isbn_id, date='2021-11-06')
    for info in info_list:
        platform = info['platform']

        if platform == 1:
            # info['author_intro'] = html.escape(info['author_intro'] )
            # @Html.Raw()
            # print( html.unescape(info['author_intro'] ))
            kingstone = info
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
    if len(pic_list) > 5:
        pic_list = pic_list[:5]

    return render_template('product.html', nav_sec=nav_sec, kingstone=kingstone, eslite=eslite, momo=momo, pic_list=pic_list)












