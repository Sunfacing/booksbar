import pymysql
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from server.models.product_model import *
from collections import defaultdict
from datetime import date

client = MongoClient('localhost', 27017)
m_db = client.Bookstores
ks_category_list = m_db.kingstone
ks_product_info = m_db.kingstone_product_info
TODAY_FOR_COLLECTION_NAME = date.today().strftime("%m%d")
catalog_today = m_db['kingstone_catalog_' + TODAY_FOR_COLLECTION_NAME]




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













def get_products():
    products = CategoryList.query.filter()
    return [p.to_json() for p in products]


def create_hashtable(hashkey, data):
    hashtable = defaultdict(dict)
    for row in data:
        hashtable[row[hashkey]] = row['id']
    return hashtable


if __name__ == '__main__':

    # Set up category list
    # ks_category_list = ks_category_list.find()
    # cate_list = []
    # for each in ks_category_list:
    #     category = CategoryList(section_id=each['section_code'],
    #                             section=each['section_nm'],
    #                             category_id=each['category_code'],
    #                             category=each['category_nm'],
    #                             subcategory_id=each['subcate_code'],
    #                             subcategory=each['subcate_nm'])
    #     cate_list.append(category)
    # db.session.add_all(cate_list)
    # db.session.commit()
    from sqlalchemy import select
    # Check if ISBN and platform exists
    isbn = '0'
    ks_platform_id = 1
    book = db.session.execute('SELECT id, isbn, platform FROM book_info WHERE platform = {} AND isbn = "{}"'.format(ks_platform_id, isbn)).first()
    author = create_hashtable('name', db.session.execute('SELECT id, name FROM author WHERE platform = {}'.format(ks_platform_id)))
    publisher = create_hashtable('name', db.session.execute('SELECT id, name FROM publisher WHERE platform = {}'.format(ks_platform_id)))
    category_id = create_hashtable('subcategory_id', db.session.execute('SELECT id, subcategory_id FROM category_list WHERE subcategory_id LIKE "/book%"'))
    
    print(len(author['d']), publisher)

    """
    if book is None:
        # Register new item
        pass
         
    else:
        pass
    """
    catalog = catalog_today.find({}, {'author': 1, 'publisher': 1})
    author_list = []
    publisher_list = []
    for each in catalog:
        if each['author'] not in author_list:
            author_list.append(each['author'])
        if each['publisher'] not in publisher_list:
            publisher_list.append(each['publisher'])

    t = len(author_list)
    print(t)
    i = 0
    authors = []
    for author in author_list:
        authors.append(Author(name=author, platform=1))
        if i % 5000 == 0 and i > 0:
            db.session.add_all(authors)
            db.session.commit()
        i += 1
        print(t - i, 'to go')


    t = len(publisher_list)
    print(t)
    i = 0
    publishers = []
    for publisher in publisher_list:
        publishers.append(Publisher(name=publisher, platform=1))
        if i % 5000 == 0 and i > 0:
            db.session.add_all(publishers)
            db.session.commit()
        i += 1
        print(t - i, 'to go')