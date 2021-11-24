import datetime
from collections import defaultdict
from datetime import timedelta

import plotly.express as px
import plotly
import pytz
from flask import render_template, request, redirect, session
from flask.helpers import url_for

from server import app
from server import db
from server.models.product_model import *
from server.models.user_model import *
from server.controller.util import *

EXPIRE = 3600
# TODAY = datetime.datetime.now(pytz.timezone('US/Pacific')).strftime("%Y-%m-%d")
TODAY = '2021-11-21'
YESTERDAY = (datetime.datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
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
    product_list = defaultdict(dict)
    for book in books:
        subcate_id = book['category_id']
        cate_nm = category_hash[subcate_id]['category']
        subcate_nm = category_hash[subcate_id]['subcategory']
        data = {
            'isbn_id': book['isbn_id'],
            'subcategory': subcate_nm,
            'title': book['title'],
            'cover_photo': book['cover_photo'],
            'description': book['description'],
            'publish_date': book['publish_date'],
            'author': book['author']
        }
        if not product_list[cate_nm]:
            product_list[cate_nm] = [data]
        else:
            product_list[cate_nm].append(data)
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

    cate_list = defaultdict(list)
    nav_sec = defaultdict(dict)
    for book in books:
        section = book['section']
        nav_sec[section] = section
        if section == section_nm:
            category = book['category']
            subcategory = book['subcategory']
            cate_list[category].append(subcategory)
    print(cate_list)
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

    page = request.args.get('page', page)
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
        return render_template('404.html'), 404

    for info in info_list:
        platform = info['platform']
        if platform == Platform.KINGSTONE.value:
            kingstone = info
        elif platform == Platform.ESLITE.value:
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
        create_data(UserFavorite(user_id=user_id, track_type=TrackType.ACTIVITY_HISTORY.value, type_id=isbn_id))
        tracking_hash = check_user_track_by_product(user_id, kingstone['category_id'], isbn_id, kingstone['author_id'])
    else:
        tracking_hash = {}
    return render_template('product.html', nav_sec=nav_sec,
                                        kingstone=kingstone,
                                        eslite=eslite,
                                        momo=momo,
                                        pic_list=pic_list,
                                        comment_list=comments,
                                        tracking_hash=tracking_hash)


@app.route('/member')
def member(track_type=TrackType.ACTIVITY_HISTORY.value):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    user_id = session['id']
    track_type = request.args.get('track_type', track_type)

    # Render user's favorite cateogory page by Section -> Category -> Subcategory
    if track_type == TrackType.FAVORITE_CATEGORY.value:
        cate_list = defaultdict(dict)
        result = get_user_favor_categories(user_id)
        for cate in result:
            section = cate['section']
            category = cate['category']
            subcategory = cate['subcategory']
            if not cate_list[section]:
                cate_list[section] = [[category, subcategory]]
            else:
                cate_list[section].append([category, subcategory])
        return render_template('favor_cate.html', cates=cate_list)

    # Render user's favorite books
    elif track_type == TrackType.FAVORITE_BOOK.value:
        user_id = session['id']
        books = get_user_favor_books(user_id, TODAY)
        book_list = defaultdict(dict)
        final_list = defaultdict(dict)
        for book in books:
            category = book['category']
            isbn_id = book['isbn_id']
            if book['platform'] == Platform.KINGSTONE.value:   
                book_list[isbn_id]['title'] = book['title']
                book_list[isbn_id]['cover_photo'] = book['cover_photo']
                platform = 'ks'
            elif book['platform'] == Platform.ESLITE.value:
                platform = 'es'
            else:
                platform = 'mm'
            book_list[isbn_id][platform + '_product_url'] = book['product_url']
            book_list[isbn_id][platform + '_price'] = int(book['price'])
            if not book_list[isbn_id][platform + '_price']:
                book_list[isbn_id][platform + '_price'] = 0
            final_list[category][isbn_id] = book_list[isbn_id]
        return render_template('favor_book.html', books=final_list)

    # Render user's favorite authors
    elif track_type == TrackType.FAVORITE_AUTHOR.value:
        authors = get_user_favor_authors(user_id)
        author_list = defaultdict(dict)
        for author in authors:
            isbn_id = author['isbn_id']
            name = author['name']
            title = author['title']
            publish_date = author['publish_date']
            if not author_list[name]:
                author_list[name] = [[isbn_id, title, publish_date]]
            else:
                author_list[name].append([isbn_id, title, publish_date])
        return render_template('favor_author.html', authors=author_list)

    # Render user's activity history
    else:
        activity_counts = summerize_user_activity(user_id)
        browse_history = check_user_browsing_history(user_id)
        return render_template('member.html', activity_counts=activity_counts, browse_history=browse_history)


@app.route('/keyword', methods=['GET'])
def search(search=None):
    term = request.args.get('search', search)
    keyword_result = search_by_term(term)
    author_result = search_by_author(term)
    product_list = create_booslist_by_category(keyword_result, author_result)
    return render_template('search.html', product_list=product_list[0], term=term, count=product_list[1])


@app.route('/author', methods=['GET'])
def author(name=None):
    name = request.args.get('name', name)
    returned_booklist = search_by_author(name)
    product_list = create_booslist_by_category(returned_booklist)
    return render_template('search.html', product_list=product_list[0], term=name, count=product_list[1])



