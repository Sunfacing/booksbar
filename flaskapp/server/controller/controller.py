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


TODAY = (datetime.datetime.now(pytz.timezone('Asia/Taipei')) - timedelta(hours=8)).strftime("%Y-%m-%d")
YESTERDAY = (datetime.datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
MONTH_AGO = (datetime.datetime.now(pytz.timezone('Asia/Taipei')) - timedelta(days=15)).strftime("%Y-%m-%d")


@app.route('/', methods=['GET'])
def index(period='month', user_id=None):
    period = request.args.get('period', period)
    user_id = request.args.get('user_id', user_id)
    if user_id is not None:
        books = homepage_by_track(period, TODAY, MONTH_AGO, user_id)
    else:
        books = homepage_by_all(period, TODAY, MONTH_AGO)
        user_id = 0

    cate_list = get_cate_list()
    category_hash = get_category(cate_list)
    product_list = defaultdict(dict)

    for book in books:
        subcate_id = book['category_id']
        sec_nm = category_hash[subcate_id]['section']
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
        if not product_list[sec_nm]:
            product_list[sec_nm] = [data]
        else:
            product_list[sec_nm].append(data)
    print(period, user_id)
    return render_template('index.html', product_list=product_list, period=period, user_id=user_id)


@app.route('/<section_nm>', methods=['GET'])
def section(section_nm='文學', category_nm='all', subcate_nm='all', page=1):
    section_nm = request.args.get('section_nm', section_nm)
    checker = CategoryList.query.filter_by(section=section_nm).first()
    if checker is None:
        return render_template('404.html'), 404
    category_nm = request.args.get('category_nm', category_nm)
    subcate_nm = request.args.get('subcate_nm', subcate_nm)
    books = get_cate_list()
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
        product_list = [product for product in return_list]
        html_page = 'section.html'

    book_counts = get_subcate_book_counts(subcate_nm)
    page = request.args.get('page', page)
    shown_pages = show_paging(page, book_counts, books_per_page=20)

    return render_template(html_page,
                           nav_sec=nav_sec,
                           cate_list=cate_list,
                           subcate_list=subcate_list,
                           current_sec=section_nm,
                           current_cate=category_nm,
                           current_sub=subcate_nm,
                           product_list=product_list,
                           shown_pages=shown_pages)


@app.route('/product/<isbn_id>', methods=['GET'])
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
            eslite = info
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
    i = 2 # i represents the slide show number, and cover photo is at 1, so starts at 2
    for pic in pics:
        pic_list.append([pic['pics'], i])
        i += 1
    comment_list = get_book_comments(isbn_id)
    comments = []
    for each in comment_list:
        comments.append([each['date'].date(), each['comment']])
    if 'loggedin' in session:
        user_id = session['id']
        create_data(UserFavorite(user_id=user_id, track_type=TrackType.ACTIVITY_HISTORY.value, type_id=isbn_id))
        tracking_hash = check_user_track_by_product(user_id=user_id,
                                                    category_id=kingstone['category_id'],
                                                    author_id=isbn_id,
                                                    isbn_id=kingstone['author_id'])
    else:
        tracking_hash = {}
    return render_template('product.html',
                           nav_sec=nav_sec,
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
        result = get_user_favor_categories(user_id)
        return_list = create_dict_list(result, 'category', 'subcategory', main_key='section')
        return render_template('favor_cate.html', cates=return_list)

    # Render user's favorite books
    elif track_type == TrackType.FAVORITE_BOOK.value:
        books = get_user_favor_books(user_id, TODAY)
        return_list = defaultdict(dict)
        final_list = defaultdict(dict)
        for book in books:
            category = book['category']
            isbn_id = book['isbn_id']
            if book['platform'] == Platform.KINGSTONE.value:
                return_list[isbn_id]['title'] = book['title']
                return_list[isbn_id]['cover_photo'] = book['cover_photo']
                platform = 'ks'
            elif book['platform'] == Platform.ESLITE.value:
                platform = 'es'
            else:
                platform = 'mm'
            return_list[isbn_id][platform + '_product_url'] = book['product_url']
            return_list[isbn_id][platform + '_price'] = int(book['price'])
            if not return_list[isbn_id][platform + '_price']:
                return_list[isbn_id][platform + '_price'] = 0
            final_list[category][isbn_id] = return_list[isbn_id]
        return render_template('favor_book.html', books=final_list)

    # Render user's favorite authors
    elif track_type == TrackType.FAVORITE_AUTHOR.value:
        authors = get_user_favor_authors(user_id)
        return_list = create_dict_list(authors, 'isbn_id', 'title', 'publish_date', main_key='name')
        return render_template('favor_author.html', authors=return_list)

    # Render user's activity history
    else:
        activity_counts = summerize_user_activity(user_id)
        browse_history = check_user_browsing_history(user_id)
        return render_template('member.html', activity_counts=activity_counts, browse_history=browse_history)


@app.route('/keyword', methods=['GET'])
def search(search=None, only_author=False):
    term = request.args.get('search', search)
    only_author = request.args.get('only_author', only_author)
    author_result = search_by_author(term)
    if only_author:
        product_list = create_booslist_by_category(author_result)
        return render_template('search.html', product_list=product_list[0], term=term, count=product_list[1])
    keyword_result = search_by_term(term)
    product_list = create_booslist_by_category(keyword_result, author_result)
    return render_template('search.html', product_list=product_list[0], term=term, count=product_list[1])


@app.route('/logout')
def logout():
    session.pop('id', None)
    session.pop('username', None)
    session.pop('loggedin', None)
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard(date=TODAY):
    date = request.values.get('date', date)
    if date > TODAY:
        date = TODAY
    scrap_result = web_scrap_result(date)
    kingstone = defaultdict(dict)
    eslite = defaultdict(dict)
    momo = defaultdict(dict)
    for result in scrap_result:
        step = result['step']
        minutes = result['minutes']
        quantity = result['quantity']
        if result['platform'] == 'kingstone':
            kingstone[step] = [minutes, quantity]
        elif result['platform'] == 'eslite':
            eslite[step] = [minutes, quantity]      
        else:
            momo[step] = [minutes, quantity]

    return render_template('dashboard.html',
                           kingstone=kingstone,
                           eslite=eslite,
                           momo=momo,
                           date=date)
