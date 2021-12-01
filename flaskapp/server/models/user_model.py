from collections import defaultdict
from server import db
from sqlalchemy import ForeignKey
from server.models.product_model import *
from server.controller.util import cleanhtml

class UserInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    email = db.Column(db.String(255)) 
    password = db.Column(db.String(255)) 
    username = db.Column(db.String(255))
    source = db.Column(db.String(255)) 
    token = db.Column(db.Text)


class UserFavorite(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    user_id = db.Column(db.Integer, ForeignKey('user_info.id'))
    track_type = db.Column(db.Integer, ForeignKey('track_type.id'))
    type_id = db.Column(db.Integer) 


class TrackType(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    track_type = db.Column(db.String(255)) 



class UserComment(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    user_id = db.Column(db.Integer, ForeignKey('user_info.id')) 
    date = db.Column(db.DateTime)
    isbn = db.Column(db.Integer)
    platform = db.Column(db.Integer, ForeignKey('platform.id'))
    comment = db.Column(db.Text)


def get_user_favor_categories(user_id):
    result = db.session.execute("""
    SELECT section, category, subcategory FROM user_favorite AS u 
    INNER JOIN category_list AS c
    ON u.type_id = c.id
    WHERE track_type = 1 AND user_id = {}
    ORDER BY section, category, subcategory;  
    """.format(user_id))
    return result



def get_user_favor_authors(user_id):
    result = db.session.execute("""
    SELECT isbn_id, 
        name, 
        title, 
        DATE_FORMAT(publish_date,'%Y-%m-%d') AS publish_date 
    FROM user_favorite AS u 
    INNER JOIN author AS a
    ON u.type_id = a.id
    INNER JOIN book_info AS b
    ON b.author = a.id
    WHERE track_type= 3 AND b.platform = 1 AND user_id = {}
    ORDER BY publish_date DESC, name""".format(user_id))
    return result


def get_user_favor_books(user_id, date):
    result = db.session.execute("""
    SELECT c.category,
        isbn_id,
        title,
        cover_photo,
        product_url,
        price,
        b.platform 
    FROM user_favorite AS u
    INNER JOIN book_info AS b
    ON u.type_id = b.isbn_id
    INNER JOIN isbn_catalog AS i
    ON b.isbn_id = i.id
    INNER JOIN category_list AS c
    ON i.category_id = c.id
    INNER JOIN price_status_info AS p
    ON b.id = p.book_id
    WHERE track_type = 2 AND p.survey_date = '{}' AND user_id = {}
    ORDER BY platform""".format(date, user_id))
    return result


def check_user_track_by_product(user_id, category_id, author_id, isbn_id):
    print(user_id, category_id, type(author_id), isbn_id)
    result = db.session.execute("""
    SELECT track_type, type_id
    FROM bookbar.user_favorite
    WHERE track_type= 1 AND type_id = {} AND user_id = {}
    OR track_type= 3 AND type_id = {} AND user_id = {}
    OR track_type= 2 AND type_id = {} AND user_id = {}
    """.format(category_id, user_id, author_id, user_id, isbn_id, user_id))
    hash_table = defaultdict(dict)
    for each in result:
        print(each)
        hash_table[each['track_type']] = each['type_id']
    return hash_table



def summerize_user_activity(user_id):
    result = db.session.execute("""
    SELECT 
    CASE
	WHEN track_type = 1 THEN '追蹤分類' 
	WHEN track_type = 2 THEN '追蹤書籍' 
	WHEN track_type = 3 THEN '追蹤作者' 
	WHEN track_type = 4 THEN '閱覽紀錄' 
    END AS type_name, 
    COUNT(DISTINCT(type_id)) AS counts
    FROM user_favorite
    WHERE user_id = {}
    GROUP BY type_name 
    ORDER BY type_name DESC""".format(user_id))
    hash_table = defaultdict(dict)
    for each in result:
        hash_table[each['type_name']] = each['counts']
    return hash_table


def check_user_browsing_history(user_id):
    result = db.session.execute("""
    SELECT DISTINCT(type_id) AS isbn_id, 
        b.title,
        b.cover_photo,
        b.description
    FROM user_favorite AS u
    INNER JOIN book_info AS b
    ON b.isbn_id = u.type_id
    WHERE user_id = {} AND track_type = 4 AND b.platform = 1
    ORDER BY u.id DESC
    LIMIT 20""".format(user_id))
    hash_table = defaultdict(dict)
    for each in result:
        hash_table[each['isbn_id']] = {'title': each['title'], 'cover_photo': each['cover_photo'], 'description': cleanhtml(each['description'])}
    return hash_table


def check_user_favorite(user_id, track_type, type_id):
    favorite_record = db.session.execute("SELECT * FROM user_favorite\
                        WHERE user_id={} AND track_type={} AND type_id={}"
                        .format(user_id, track_type, type_id))
    return favorite_record

def delete_user_favorite(user_id, track_type, type_id):
    db.session.execute("DELETE FROM user_favorite\
                    WHERE user_id={} AND track_type={} AND type_id={}"
                    .format(user_id, track_type, type_id))
    db.session.commit()

