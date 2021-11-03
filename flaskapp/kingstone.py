import collections
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



def mongo_to_hashtable(collection, hashkey):
    data = collection.find()
    hashtable = defaultdict(dict)
    for each in data:
        hashtable[each[hashkey]] = each
    return hashtable



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
    ks_category_list = ks_category_list.find()
    cate_list = []
    for each in ks_category_list:
        section_id=each['section_code']
        if 'book' in section_id:
            category = CategoryList(section_id=section_id,
                                    section=each['section_nm'],
                                    category_id=each['category_code'],
                                    category=each['category_nm'],
                                    subcategory_id=each['subcate_code'],
                                    subcategory=each['subcate_nm'])
            cate_list.append(category)
    db.session.add_all(cate_list)
    db.session.commit()



    # Check if ISBN and platform exists
    







    """
    isbn = '0'
    ks_platform_id = 1
    book = db.session.execute('SELECT id, isbn, platform_id FROM book_info WHERE platform_id = {} AND isbn = "{}"'.format(ks_platform_id, isbn)).first()
    author_hash = create_hashtable('name', db.session.execute('SELECT id, name FROM author WHERE platform = {}'.format(ks_platform_id)))
    publisher_hash = create_hashtable('name', db.session.execute('SELECT id, name FROM publisher WHERE platform = {}'.format(ks_platform_id)))
    category_id = create_hashtable('subcategory_id', db.session.execute('SELECT id, subcategory_id FROM category_list WHERE subcategory_id LIKE "/book%"'))
    
    # print(len(author['d']), publisher)

    catalog = mongo_to_hashtable(catalog_today, 'kingstone_pid')
    product_info = mongo_to_hashtable(ks_product_info, 'kingstone_pid')
    product_list = []
    for pid, info in product_info.items():
        if len(catalog[pid]) > 0:
            subcate = info['subcate_id']
            subcate_id = category_id[subcate]
            try:
                author = catalog[pid]['author']
                author = author_hash[author]
            except: author = 1013197
            try:
                publisher = catalog[pid]['publisher']
                publisher = publisher_hash[publisher]
            except: 
                publisher = 1

            try: publish_date = catalog[pid]['publish_date']
            except: publish_date = ''

            try: product_url = catalog[pid]['product_url']
            except: product_url = ''
            
            try:description = str(info['description'])
            except:description = ''

            try: page = info['頁數']
            except: page = ''

            try:
                isbn = info['ISBN']
                if isbn == '':
                    continue
            except: 
                continue


            info = BookInfo(
                create_date = info['scrap_date'], 
                title = info['title'],
                author = author,
                publisher = publisher,
                publish_date = publish_date, 
                table_of_content = info['table_of_contents'],
                description = description,
                author_intro = info['author_description'],
                cover_photo = info['main_img'], 
                page = info['頁數'],
                product_url = product_url,
                e_book_url = info['e_book'],
                isbn = info['ISBN'],
                category_id = subcate_id,
                platform_id = 1
                )
            product_list.append(info)


    t = len(product_list)
    print(t)       
    products = [] 
    i = 0
    for each in product_list:
        products.append(each)
        if i % 10000 == 0 and i > 0:
            db.session.add_all(products)
            db.session.commit()
            products = []
            print(t - i, 'to go')
        i += 1
    db.session.add_all(products)
    db.session.commit()
    

    
    catalog = catalog_today.find({}).distinct('author')
    
    author_list = []
    for each in catalog:
        author_list.append(Author(name=each, platform=1))

    t = len(author_list)
    print(t)
    i = 0
    authors = []
    for author in author_list:
        authors.append(author)
        if i % 10000 == 0 and i > 0:
            db.session.add_all(authors)
            db.session.commit()
            authors = []
            print(t - i, 'to go')
        i += 1
    db.session.add_all(authors)
    db.session.commit()
    print('author done')


    print('publisher begin')
    catalog = catalog_today.find({}).distinct('publisher')
    publisher_list = []
    for each in catalog:
        publisher_list.append(Publisher(name=each, platform=1))
    t = len(publisher_list)
    print(t)
    i = 0
    publishers = []
    for publisher in publisher_list:
        publishers.append(publisher)
        if i % 10000 == 0 and i > 0:
            db.session.add_all(publishers)
            db.session.commit()
            publishers = []
            print(t - i, 'to go')
        i += 1
    db.session.add_all(publishers)
    db.session.commit()
    print('publisher done')
    """