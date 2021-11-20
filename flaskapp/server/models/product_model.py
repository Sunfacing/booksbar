from collections import defaultdict
from server import db
from sqlalchemy import ForeignKey
from sqlalchemy.schema import UniqueConstraint, Index
import random

class CategoryList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.String(30))
    section = db.Column(db.String(30))
    category_id = db.Column(db.String(30))
    category = db.Column(db.String(30))
    subcategory_id = db.Column(db.String(30))
    subcategory = db.Column(db.String(30))


class Platform(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    platform = db.Column(db.String(30), primary_key=True)


class IsbnCatalog(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True) 
    isbn = db.Column(db.String(30), primary_key=True)
    category_id = db.Column(db.Integer, ForeignKey('category_list.id'), nullable=False)
    platform = db.Column(db.Integer, ForeignKey('platform.id'), nullable=False)
    __table_args__ = (UniqueConstraint('isbn', name='isbn'),)


class BookInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True) 
    isbn_id = db.Column(db.Integer, ForeignKey('isbn_catalog.id'), nullable=False)
    platform = db.Column(db.Integer, ForeignKey('platform.id'), nullable=False)
    platform_product_id = db.Column(db.String(255), primary_key=True, nullable=False)
    create_date = db.Column(db.DateTime, nullable=False) 
    title = db.Column(db.String(255), nullable=False, index = True)
    author = db.Column(db.Integer, ForeignKey('author.id'))
    publisher = db.Column(db.Integer, ForeignKey('publisher.id'))
    size = db.Column(db.String(30))
    publish_date = db.Column(db.DateTime)
    table_of_content = db.Column(db.Text)
    description = db.Column(db.Text)
    author_intro = db.Column(db.Text)
    cover_photo = db.Column(db.String(255))
    page = db.Column(db.Integer)
    product_url = db.Column(db.String(255))
    __table_args__ = (Index('title', title, mysql_prefix='FULLTEXT', mysql_with_parser="ngram"),)



class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(100))
    platform = db.Column(db.Integer, ForeignKey('platform.id'))
    __table_args__ = (Index('name', name, mysql_prefix='FULLTEXT', mysql_with_parser="ngram"),)


class Publisher(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(100))
    platform = db.Column(db.Integer, ForeignKey('platform.id'))


class Picture(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    book_id = db.Column(db.Integer, ForeignKey('book_info.id')) 
    url = db.Column(db.String(255))


class PriceStatusInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    book_id = db.Column(db.Integer, ForeignKey('book_info.id')) 
    price_type = db.Column(db.Integer, ForeignKey('price_type.id')) 
    status = db.Column(db.Integer, ForeignKey('status.id'))
    price = db.Column(db.Integer)
    survey_date = db.Column(db.Date)

class PriceType(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    price_type = db.Column(db.String(30))     

class Status(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    status = db.Column(db.String(30))   

class PipelineStep(db.Model):
    step = db.Column(db.String(30))
    id = db.Column(db.Integer, primary_key=True) 

class PipelineTrack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    platform = db.Column(db.Integer, ForeignKey('platform.id'))
    step = db.Column(db.Integer, ForeignKey('pipeline_step.id'))
    quantity = db.Column(db.Integer)
    minutes = db.Column(db.Integer)


class HotItemRecom(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    book_id = db.Column(db.Integer, ForeignKey('book_info.id'))




def homepage_by_track(period, today, month_ago, user_id):
    if period == 'month':
        books = db.session.execute("""
                SELECT isbn_id, i.category_id, c.category ,b.title, b.description, b.cover_photo, b.publish_date, b.product_url, a.name AS author  FROM user_favorite AS u
                INNER JOIN category_list AS c
                ON u.type_id = c.id
                INNER JOIN isbn_catalog AS i
                ON c.id = i.category_id
                INNER JOIN book_info AS b
                ON i.id = b.isbn_id
                INNER JOIN author AS a
                ON b.author = a.id
                WHERE u.user_id = {} AND u.track_type = 1 AND b.platform = 1 and b.publish_date BETWEEN '{}' AND '{}'
                ORDER BY publish_date DESC""".format(user_id, month_ago, today))
    else:
        books = db.session.execute("""
                SELECT isbn_id, i.category_id, c.category ,b.title, b.description, b.cover_photo, b.publish_date, b.product_url, a.name AS author  FROM user_favorite AS u
                INNER JOIN category_list AS c
                ON u.type_id = c.id
                INNER JOIN isbn_catalog AS i
                ON c.id = i.category_id
                INNER JOIN book_info AS b
                ON i.id = b.isbn_id
                INNER JOIN author AS a
                ON b.author = a.id
                WHERE u.user_id = {} AND u.track_type = 1 AND b.platform = 1 and b.publish_date > '{}'
                ORDER BY publish_date DESC""".format(user_id, today))
    print(books)
    return books



def homepage_by_all(period, today, month_ago):
    random.sample(range(900), 10)
    data = tuple(random.sample(range(900), 40))
    if period == 'month':
        books = db.session.execute("""SELECT isbn_id, category_id, b.title, b.description, b.cover_photo, b.publish_date, b.product_url, a.name AS author FROM isbn_catalog AS i
                                    INNER JOIN book_info AS b
                                    ON i.id = b.isbn_id
                                    INNER JOIN author AS a
                                    ON b.author = a.id
                                    WHERE category_id IN {} AND b.platform = 1 and b.publish_date BETWEEN '{}' AND '{}'
                                    ORDER BY publish_date DESC
                                    LIMIT 20""".format(data, month_ago, today))
    else:
        books = db.session.execute("""SELECT isbn_id, category_id, b.title, b.description, b.cover_photo, b.publish_date, b.product_url, a.name AS author FROM isbn_catalog AS i
                                    INNER JOIN book_info AS b
                                    ON i.id = b.isbn_id
                                    INNER JOIN author AS a
                                    ON b.author = a.id
                                    WHERE b.platform = 1 and b.publish_date > '{}'
                                    LIMIT 20""".format(today))
    return books














def get_catalog_section(section, date_1, date_2):
    product_list =db.session.execute("""
        SELECT b.isbn_id,
            b.id AS book_id,
            publish_date,
            title,
            description,
            cover_photo,
            a.name AS author,
            p.name AS publisher
        FROM category_list AS c 
        INNER JOIN isbn_catalog AS i
        ON i.category_id = c.id
        INNER JOIN book_info AS b
        ON b.isbn_id = i.id
        INNER JOIN author AS a
        ON b.author = a.id
        INNER JOIN publisher AS p
        ON b.publisher = p.id
        WHERE b.platform = 1 AND c.section = '{}'  
        AND publish_date BETWEEN '{}' AND '{}'
        ORDER BY publish_date DESC LIMIT 9""".format(section, date_1, date_2))
    return product_list


def get_catalog_subcategory(subcategory, page):
    # Page begins at 1, so must deduct to 1 to get the fisrt 20 books
    offset = (int(page) - 1) * 20
    product_list =db.session.execute("""
        SELECT b.isbn_id,
                b.id AS book_id,
                DATE_FORMAT(publish_date,'%Y-%m-%d') AS publish_date,
                title,
                description,
                cover_photo,
                a.name AS author,
                p.name AS publisher
            FROM category_list AS c 
            INNER JOIN isbn_catalog AS i
            ON i.category_id = c.id
            INNER JOIN book_info AS b
            ON b.isbn_id = i.id
            INNER JOIN author AS a
            ON b.author = a.id
            INNER JOIN publisher AS p
            ON b.publisher = p.id
            WHERE b.platform = 1 and c.subcategory = '{}'  
            ORDER BY publish_date DESC 
            LIMIT 20 offset {}""".format(subcategory, offset))
    return product_list


def get_subcate_book_counts(subcategory):
    book_counts = db.session.execute("""
        SELECT COUNT(i.category_id)
        FROM category_list AS c 
        INNER JOIN isbn_catalog AS i
        ON i.category_id = c.id
        WHERE c.subcategory = '{}'""".format(subcategory))
    return book_counts






def get_book_info(isbn_id, date):
    info_list = db.session.execute("""
    SELECT title, a.name AS author, a.id AS author_id, u.name AS publisher, u.id AS publisher_id,
        DATE_FORMAT(publish_date,'%Y-%m-%d') AS publish_date, i.category_id AS category_id, 
        c.section, c.category, c.subcategory, isbn_id, i.isbn AS ISBN, b.platform, size, page, 
        p.status, p.price, product_url, cover_photo
    FROM book_info AS b
    INNER JOIN isbn_catalog AS i
    ON i.id = b.isbn_id
    INNER JOIN category_list AS c
    ON i.category_id = c.id
    LEFT JOIN price_status_info AS p
    ON b.id = p.book_id 
    INNER JOIN author AS a
    ON a.id = b.author
    INNER JOIN publisher AS u
    ON u.id = b.publisher
    WHERE isbn_id = {} AND survey_date='{}'""".format(isbn_id, date))
    return info_list



def get_book_pics(isbn_id):
    pic_list = db.session.execute("""
    SELECT b.cover_photo, p.url AS pics FROM book_info AS b
    INNER JOIN picture AS p
    ON b.id = p.book_id
    WHERE isbn_id = {} and platform = 1""".format(isbn_id))
    return pic_list



def get_book_comments(isbn_id):
    comment_list = db.session.execute("""
    SELECT * FROM bookbar.user_comment WHERE isbn = {}""".format(isbn_id))
    return comment_list




def api_book_info(isbn_id):
    result = db.session.execute("""
    SELECT table_of_content, description, author_intro
    FROM book_info AS b
    LEFT JOIN price_status_info AS p
    ON b.id = p.book_id 
    INNER JOIN author AS a
    ON a.id = b.author
    WHERE isbn_id = {} and b.platform = 1""".format(isbn_id))

    return result


def search_by_term(term):
    result = db.session.execute("""
    SELECT c.category, isbn_id, title, cover_photo, a.name AS author, description 
    FROM book_info AS b
    INNER JOIN isbn_catalog AS i
    ON b.isbn_id = i.id
    INNER JOIN category_list AS c
    ON i.category_id = c.id
    INNER JOIN author AS a
    ON b.author = a.id
	WHERE MATCH (title) AGAINST('{}' IN boolean mode ) AND b.platform = 1""".format(term))

    return result


def search_by_author(name):
    result = db.session.execute("""
    SELECT c.category, isbn_id, title, cover_photo, a.name AS author, description 
    FROM book_info AS b
    INNER JOIN isbn_catalog AS i
    ON b.isbn_id = i.id
    INNER JOIN category_list AS c
    ON i.category_id = c.id
    INNER JOIN author AS a
    ON b.author = a.id
	WHERE b.platform = 1 AND a.name = '{}'""".format(name))
    return result









def daily_result(date):
    result = db.session.execute("""
    SELECT t.step, s.step, t.*, p.platform 
    FROM pipeline_step AS s
    LEFT JOIN pipeline_track AS t
    ON t.step = s.id
    LEFT JOIN platform AS p
    ON t.platform = p.id
    WHERE p.platform not IN ('original', 'promotional')""".format(date))
    return result


