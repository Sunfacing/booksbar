import collections
from sys import platform
import pymysql
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from user_model import *
from product_model import *
from collections import defaultdict
from datetime import date
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import datetime
import pytz
import time

# from testers import my_date

# print(my_date)



load_dotenv()
client = MongoClient('mongodb://{}:{}@{}/?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&directConnection=true&ssl=false'.format(os.getenv("mon_user"), os.getenv("mon_passwd"), os.getenv("mon_host")))
# client = MongoClient('localhost', 27017)

m_db = client.Bookstores
h_db = client.bookbar
ks_category_list = h_db.kingstone
ks_product_info = h_db.kingstone_product_info
mm_product_info = h_db.momo_product_info
TODAY = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y-%m-%d")

TODAY_FOR_COLLECTION_NAME = (datetime.datetime.now(pytz.timezone('Asia/Taipei'))).strftime("%m%d")
ks_catalog_today = h_db['kingstone_catalog_' + TODAY_FOR_COLLECTION_NAME]
mm_catalog_today = h_db['momo_catalog_' + TODAY_FOR_COLLECTION_NAME]
es_catalog_today = h_db['eslite_catalog_' + TODAY_FOR_COLLECTION_NAME]
timecounter = h_db.timecounter



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







def mongo_to_hashtable(collection, hashkey, duplicate_hashkey, date=None):
    if date is None:
        data = collection.find({'ISBN': {'$ne': ''}})
    else:
        data = collection.find({'track_date': date})
    hashtable = defaultdict(dict)
    duplicate_hash = defaultdict(dict)
    for information in data:
        product_id = information[hashkey]
        try:
            duplicate_id = information[duplicate_hashkey]
        except Exception as e:
            print(information[hashkey], e)
        if hashtable[product_id] or duplicate_hash[duplicate_id]:
            continue
        duplicate_hash[duplicate_hashkey] = 1
        hashtable[product_id] = information
    return hashtable

def get_products():
    products = CategoryList.query.filter()
    return [p.to_json() for p in products]

def create_hashtable(hashkey, data):
    hashtable = defaultdict(dict)
    for row in data:
        hashtable[row[hashkey]] = row['id']
    return hashtable

def mongo_hash(collection, hashkey, query=None):
    if query is None:
        data = collection.find()
    else:
        data = collection.find(query)
    hashtable = defaultdict(dict)
    for row in data:
        hashtable[row[hashkey]] = row
    return hashtable

def my_sql_isbn_hash():
    data = db.session.execute('SELECT * FROM isbn_catalog')
    isbn_hashtable = defaultdict(dict)
    for row in data:
        isbn = row['isbn']
        isbn_hashtable[isbn] = {'isbn_id': row['id'], 'platform': row['platform']}
    return isbn_hashtable

def register_picture(ks_product_info, date=TODAY):
    books = db.session.execute('SELECT platform_product_id, id FROM book_info WHERE platform = 1 and create_date = {}'.format(date))
    platform_id_hash = defaultdict(dict)
    for book in books:
        platform_id_hash[book['platform_product_id']] = book['id']
    pic_list = []
    product_info = ks_product_info.find({'track_date': date})
    i = 0
    for info in product_info:
        try:
            product_id = info['kingstone_pid']
            if product_id in platform_id_hash:
                book_id = platform_id_hash[product_id]
                for pic in info['images']:
                    pic_list.append(Picture(book_id=book_id, url=pic))
            if i % 5000 == 0 and i > 0:
                db.session.add_all(pic_list)
                db.session.commit()        
                print('create picture: ', i, 'done')         
            i += 1
        except:
            pass
    db.session.add_all(pic_list)
    db.session.commit()
    print('create picture: ', i, 'done, all finished')   

def register_author(catalog_today):
    # Create author full list
    print('begin register new author')
    start = time.time()
    catalog = catalog_today.find({}).distinct('author')
    registered = db.session.execute('SELECT id, name FROM author')
    registered_list = create_hashtable('name', registered)
    author_list = []
    for each in catalog:
        if not registered_list[each]:
            author_list.append(Author(name=each, platform=1))
    t = len(author_list)
    print('new author: ',t)
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
    end = time.time()
    step = PipelineTrack(date=TODAY, platform=1, step=7, minutes=round(((end - start) / 60), 1), quantity=i)
    db.session.add(step)
    db.session.commit()
    print('author done')
 
def register_publisher(catalog_today):
    # Create publisher full list
    print('begin register new publisher')
    start = time.time()
    registered = db.session.execute('SELECT id, name FROM publisher')
    registered_list = create_hashtable('name', registered)

    catalog = catalog_today.find({}).distinct('publisher')
    publisher_list = []
    for each in catalog:
        if not registered_list[each]:
            publisher_list.append(Publisher(name=each, platform=1))
    t = len(publisher_list)
    print('new publishers: ',t)
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
    end = time.time()
    step = PipelineTrack(date=TODAY, platform=1, step=8, minutes=round(((end - start) / 60), 1), quantity=i)
    db.session.add(step)
    db.session.commit()
    print('publisher done')    
    
def register_kingstone_user_comment(product_info, date=TODAY):
    # Create comment full list
    isbn_catalog = my_sql_isbn_hash()
    commment_from_product_info = product_info.find({'$and': [{'scrap_date': date}, {'reader_comments':{'$ne': None}}]})
    comment_list = []
    for each in commment_from_product_info:
        try: isbn = each['ISBN']
        except: continue
        if isbn_catalog[isbn]:
            for reader in each['reader_comments']:
                for date, comment in reader.items():
                    comment_list.append(UserComment(user_id=1, platform=1, date=date, isbn=isbn_catalog[isbn]['isbn_id'], comment=str(comment)))

    t = len(comment_list)
    print(t)
    i = 0
    comments = []
    for comment in comment_list:
        comments.append(comment)
        if i % 2000 == 0 and i > 0:
            db.session.add_all(comments)
            db.session.commit()
            comments = []
            print(t - i, 'to go')
        i += 1
    db.session.add_all(comments)
    db.session.commit()
    print('comment done')  

def register_isbn(ks_product_info, date=None):
    """
    This function is used for first time registration for kingstone
    """
    # Create isbn full list
    category_id = create_hashtable('subcategory_id', db.session.execute('SELECT id, subcategory_id FROM category_list'))
    products = mongo_to_hashtable(ks_product_info, 'kingstone_pid', 'ISBN', date=date)
    isbn_catalog = my_sql_isbn_hash()
    qty = len(products)
    print('new isbn:', qty)

    isbn_list = []
    i = 0
    duplicate_hash = defaultdict(dict)
    for product in products.values():

        try:
            if product['ISBN'] == '' or not category_id[product['subcate_id']]:
                continue
            isbn = product['ISBN']
            if not duplicate_hash[isbn] and not isbn_catalog[isbn]:
                duplicate_hash[isbn] = 1
                data = IsbnCatalog(isbn=product['ISBN'], category_id=category_id[product['subcate_id']], platform=1)
                isbn_list.append(data)
            else:
                continue
        except Exception as e:
            print(i, product, e)
    
        if i % 5000 == 0 and i > 0:
            db.session.add_all(isbn_list)
            db.session.commit()
            isbn_list = []
            print(qty - i, 'to go')    
        i += 1
    db.session.add_all(isbn_list)
    db.session.commit()  

def register_kingstone_from_catalog(ks_catalog):
    start = time.time()
    sql_isbn_hashtable = my_sql_isbn_hash()
    product_info = mongo_to_hashtable(ks_product_info,  'kingstone_pid', 'ISBN')
    author_hash = create_hashtable('name', db.session.execute('SELECT id, name FROM author'))
    publisher_hash = create_hashtable('name', db.session.execute('SELECT id, name FROM publisher'))
    category_id = create_hashtable('subcategory_id', db.session.execute('SELECT id, subcategory_id FROM category_list'))
    catalog = mongo_hash(ks_catalog  , 'kingstone_pid')
    already_in_book_info_list = create_platform_id_hashtable(1)   
    i = 0
    product_list = []
    for pid, info in product_info.items():
        try:
            isbn = info['ISBN']
        except:
            continue
        if sql_isbn_hashtable[isbn] and not already_in_book_info_list[pid]:
            i +=1 
            subcate = info['subcate_id']
            if not category_id[subcate]:
                print("['check']", pid, info)
                continue
            subcate_id = category_id[subcate]
            try:
                author = catalog[pid]['author']
                if author_hash[author]:
                    author = author_hash[author]
                else: author = 2
            except: 
                author = 2

            try:
                publisher = catalog[pid]['publisher']
                if publisher_hash[publisher]:
                    publisher = publisher_hash[publisher]
                else:
                    publisher = 1
            except: 
                publisher = 1

            try:  publish_date = catalog[pid]['publish_date']
            except: publish_date = '1900-01-01'

            try: product_url = catalog[pid]['product_url']
            except: product_url = ''
            
            try: description = str(info['description'])
            except: description = ''

            try: table_of_contents = info['table_of_contents']
            except: table_of_contents = ''

            try: author_description = info['author_description']
            except: author_description = ''

            try: size = info['商品規格']
            except: size = ''

            try: page = info['頁數']
            except:  page = ''

            try:
                isbn = info['ISBN']
                if isbn == '':
                    continue
            except: 
                continue

            info = BookInfo(
                isbn_id = sql_isbn_hashtable[isbn]['isbn_id'],
                create_date = info['track_date'], 
                title = info['title'],
                platform_product_id = pid,
                author = author,
                publisher = publisher,
                publish_date = publish_date, 
                table_of_content = table_of_contents,
                description = description,
                author_intro = author_description,
                cover_photo = info['main_img'], 
                size = size,
                page = page,
                product_url = product_url,
                platform = 1
                )
            product_list.append(info)

    t = len(product_list)
    print('new products', t)       
    products = [] 
    i = 0
    for each in product_list:
        products.append(each)
        if i % 5000 == 0 and i > 0:
            db.session.add_all(products)
            db.session.commit()
            products = []
            print('kingstone register catalog', i, 'done')
        i += 1
    db.session.add_all(products)
    db.session.commit()
    end = time.time()
    step = PipelineTrack(date=TODAY, platform=1, step=9, minutes=round(((end - start) / 60), 1), quantity=i)
    db.session.add(step)
    db.session.commit()
    print('kingstone register catalog', i, 'done, all finished')

def update_kingstone_price(catalog_today):
    start = time.time()
    products = catalog_today.find()
    books = db.session.execute('SELECT platform_product_id, id FROM book_info WHERE platform = 1')
    platform_id_hash = create_hashtable('platform_product_id', books)
    price_registered = db.session.execute('SELECT p.book_id, p.id FROM price_status_info AS p\
                                        INNER JOIN book_info AS b ON b.id = p.book_id\
                                        WHERE platform = 1 and survey_date = "{}"'.format(TODAY))
    registered_price_hash = create_hashtable('book_id', price_registered)
    price_list = []
    i = 0
    for product in products:
        product_id = product['kingstone_pid']
        book_id = platform_id_hash[product_id]
        if platform_id_hash[product_id] and not registered_price_hash[book_id]:
            if product['availability'] == '加入購物車': status = 1 
            else: status = 2
            price_list.append(PriceStatusInfo(book_id=book_id, price_type=1, status=status, price=product['price'], survey_date=TODAY))
            if i % 5000 == 0 and i > 0:
                db.session.add_all(price_list)
                db.session.commit()
                print('kingstone update price', i, 'done')
                price_list = []
            i += 1
    db.session.add_all(price_list)
    db.session.commit()
    end = time.time()
    step = PipelineTrack(date=TODAY, platform=1, step=10, minutes=round(((end - start) / 60), 1), quantity=i)
    db.session.add(step)
    db.session.commit()
    print('kingstone update price', i, 'done, all finished')

def isbn_hashtable():
    """
    Create hashtable with isbn as key, using kingstone's book info data
    as long as kingstone has the products, other platform can register too
    the columns returned are used for easier registering in book info
    """
    data = db.session.execute("""
    SELECT  i.isbn AS isbn,
		b.isbn_id AS isbn_id,
	    i.category_id AS category_id, 
		b.author AS author,
        b.publisher AS publisher
    FROM isbn_catalog AS i 
    INNER JOIN book_info AS b 
    ON b.isbn_id = i.id
    WHERE b.platform = 1""")
    hashtable = defaultdict(dict)
    for row in data:
        isbn = row['isbn']
        hashtable[isbn] = row
    return hashtable

def create_platform_id_hashtable(platform_id):
    """
    Create hashtable with platform_product_id as key, 
    if the new catalog product id can be found here,
    meaning it's not new, and will be ignored
    used for preventing duplicate insertion into mysql
    just in case scraping go wrong without knowing
    """
    data = db.session.execute("SELECT id, platform_product_id FROM book_info WHERE platform = {}".format(platform_id))
    hashtable = defaultdict(dict)
    for row in data:
        platform_product_id = row['platform_product_id']
        hashtable[platform_product_id] = 1
    return hashtable

def register_eslite_from_catalog(eslite_catalog):
    start = time.time()
    sql_isbn_hashtable = isbn_hashtable()
    products = eslite_catalog.find({'ISBN': {'$ne':''}})
    already_in_book_info_list = create_platform_id_hashtable(2)
    i = 0
    product_list = []
    for product in products:
        try:
            product_id = product['eslite_pid']
            eslite_isbn = product['ISBN']
            title = product['title']
        except Exception as e:
            print(product['eslite_pid'], e)
        if sql_isbn_hashtable[eslite_isbn] and not already_in_book_info_list[product_id]:
            product_list.append(BookInfo(isbn_id = sql_isbn_hashtable[eslite_isbn]['isbn_id'],
                                platform = 2,
                                platform_product_id = product_id,
                                create_date = TODAY,
                                title = title,
                                author = sql_isbn_hashtable[eslite_isbn]['author'],
                                publisher = sql_isbn_hashtable[eslite_isbn]['publisher'],
                                cover_photo = product['product_photo_url'] ,
                                product_url = product['product_url']))
            if i % 5000 == 0 and i > 0:
                db.session.add_all(product_list)
                db.session.commit()
                print('eslite register catalog', i, 'done')
                product_list = []
            i += 1
    db.session.add_all(product_list)
    db.session.commit()
    end = time.time()
    step = PipelineTrack(date=TODAY, platform=2, step=9, minutes=round(((end - start) / 60), 1), quantity=i)
    db.session.add(step)
    db.session.commit()
    print('eslite register catalog', i, 'done, all finished')

def update_eslite_price(eslite_catalog):
    start = time.time()
    products = eslite_catalog.find()
    books = db.session.execute('SELECT platform_product_id, id FROM book_info WHERE platform = 2')
    platform_id_hash = create_hashtable('platform_product_id', books)
    price_registered = db.session.execute('SELECT p.book_id, p.id FROM price_status_info AS p\
                                            INNER JOIN book_info AS b ON b.id = p.book_id\
                                            WHERE platform = 2 and survey_date = "{}"'.format(TODAY))
    registered_price_hash = create_hashtable('book_id', price_registered)
    price_list = []
    i = 0
    for product in products:
        product_id = product['eslite_pid']
        book_id = platform_id_hash[product_id]
        if platform_id_hash[product_id] and not registered_price_hash[book_id]:
            if product['status'] == 'add_to_shopping_cart': 
                status = 1 
            else: 
                status = 2
            try:
                product['price']
            except:
                continue
            price_list.append(PriceStatusInfo(book_id=book_id, price_type=1, status=status, price=product['price'], survey_date=TODAY))
            if i % 5000 == 0 and i > 0:
                db.session.add_all(price_list)
                db.session.commit()
                print('eslite update price', i, 'done')
                price_list = []
            i += 1
    db.session.add_all(price_list)
    db.session.commit()
    end = time.time()
    step = PipelineTrack(date=TODAY, platform=2, step=10, minutes=round(((end - start) / 60), 1), quantity=i)
    db.session.add(step)
    db.session.commit()
    print('eslite update price', i, 'done, all finished')

def register_momo_from_catalog(momo_catalog, momo_product_info):
    start = time.time()
    sql_isbn_hashtable = isbn_hashtable()
    products = momo_catalog.find({'ISBN': {'$ne':''}})
    product_info = mongo_hash(momo_product_info, 'momo_pid', query={'ISBN':{'$ne':""}})
    already_in_book_info_list = create_platform_id_hashtable(3)
    i = 0
    product_list = []
    error = 0
    for product in products:
        product_id = product['momo_pid']
        try:
            momo_isbn = product_info[product_id]['ISBN']
        except:
            error += 1
            continue
        if sql_isbn_hashtable[momo_isbn] and not already_in_book_info_list[product_id]:
            product_list.append(BookInfo(isbn_id = sql_isbn_hashtable[momo_isbn]['isbn_id'],
                                platform = 3,
                                platform_product_id = product_id,
                                create_date = TODAY,
                                title = product['title'],
                                author = sql_isbn_hashtable[momo_isbn]['author'],
                                publisher = sql_isbn_hashtable[momo_isbn]['publisher'],
                                cover_photo = product['pic_url'] ,
                                product_url = product['product_url']))
            if i % 5000 == 0 and i > 0:
                db.session.add_all(product_list)
                db.session.commit()
                print('momo register catalog', i, 'done')
                product_list = []
            i += 1
    db.session.add_all(product_list)
    db.session.commit()
    end = time.time()
    step = PipelineTrack(date=TODAY, platform=3, step=9, minutes=round(((end - start) / 60), 1), quantity=i)
    db.session.add(step)
    db.session.commit()
    print('momo register catalog', i, 'done, all finished')

def update_momo_price(momo_catalog):
    start = time.time()
    products = momo_catalog.find()
    books = db.session.execute('SELECT platform_product_id, id FROM book_info WHERE platform = 3')
    platform_id_hash = create_hashtable('platform_product_id', books)
    price_registered = db.session.execute('SELECT p.book_id, p.id FROM price_status_info AS p\
                                        INNER JOIN book_info AS b ON b.id = p.book_id\
                                        WHERE platform = 3 and survey_date = "{}"'.format(TODAY))
    registered_price_hash = create_hashtable('book_id', price_registered)
    price_list = []
    i = 0
    for product in products:
        product_id = product['momo_pid']
        book_id = platform_id_hash[product_id]
        if platform_id_hash[product_id] and not registered_price_hash[book_id]:
            try:
                price = int(product['price'])
            except:
                price = product['price'].replace(',', '')
                price = int(price)
            price_list.append(PriceStatusInfo(book_id=book_id, price_type=1, status=1, price=price, survey_date=TODAY))
            if i % 5000 == 0 and i > 0:
                db.session.add_all(price_list)
                db.session.commit()
                print('momo update price', i, 'done')
                price_list = []
            i += 1
    db.session.add_all(price_list)
    db.session.commit()
    end = time.time()
    step = PipelineTrack(date=TODAY, platform=3, step=10, minutes=round(((end - start) / 60), 1), quantity=i)
    db.session.add(step)
    db.session.commit()
    print('momo update price', i, 'done, all finished')



########################################################################################
# Update scraper result


def scraper_result_from_mongo():
    result = timecounter.find({'date': TODAY, 'quantity':{'$ne': ''}})
    final_list = []
    for doc in result:
        step = doc['step']
        platform = doc['platform']
        if platform == 'kingstone': platform = 1
        if platform == 'eslite': platform = 2
        if platform == 'momo': platform = 3
        if step == 'scrape catalog': step = 1
        if step == 'remove duplicates': step = 2
        if step == 'track change': step = 3
        if step == 'scrape product': step = 4
        if step == 'check unfound': step = 5
        if step == 'create catalog': 
            step = 6
            minutes = 0
        try:    
            step = PipelineTrack(date=doc['date'], platform=platform, step=step, minutes=round((doc['time'] / 60), 1), quantity=doc['quantity'])
            final_list.append(step)
            # print(doc['date'], platform, step, round((doc['time'] / 60), 1), doc['quantity'])
        except:
            pass
    db.session.add_all(final_list)
    db.session.commit()

# Update kingstone
def k_register_author():
    register_author(ks_catalog_today)

def k_register_publisher():
    register_publisher(ks_catalog_today)

def k_register_isbn():
    register_isbn(ks_product_info, date=TODAY)

def k_register_from_catalog():
    register_kingstone_from_catalog(ks_catalog_today)

def k_register_picture():
    register_picture(ks_product_info, date=TODAY)

def k_register_user_comment():
    register_kingstone_user_comment(ks_product_info)

def k_update_price():
    update_kingstone_price(ks_catalog_today)

# Update eslite
def eslite_register_from_catalog():
    register_eslite_from_catalog(es_catalog_today)
def eslite_update_price():
    update_eslite_price(es_catalog_today)

# Update momo
def momo_register_from_catalog():
    register_momo_from_catalog(mm_catalog_today, mm_product_info)

def momo_update_price():
    update_momo_price(mm_catalog_today)


with DAG(
dag_id='a_sql_writer',
schedule_interval='00 22 * * *',
start_date=datetime.datetime(2021, 11, 1),
catchup=False,
# default_args={'depends_on_past': True},
tags=['it_is_test'],
) as dag:

    task_1 = PythonOperator(task_id='scraper_result_from_mongo', python_callable=scraper_result_from_mongo)

    task_2 = PythonOperator(task_id='k_register_author', python_callable=k_register_author)
    task_3 = PythonOperator(task_id='k_register_publisher', python_callable=k_register_publisher)
    task_4 = PythonOperator(task_id='k_register_isbn', python_callable=k_register_isbn)
    task_5 = PythonOperator(task_id='k_register_from_catalog', python_callable=k_register_from_catalog)
    task_6 = PythonOperator(task_id='k_register_picture', python_callable=k_register_picture)
    task_7 = PythonOperator(task_id='k_register_user_comment', python_callable=k_register_user_comment)
    task_8 = PythonOperator(task_id='k_update_price', python_callable=k_update_price)

    task_9 = PythonOperator(task_id='eslite_register_from_catalog', python_callable=eslite_register_from_catalog)
    task_10 = PythonOperator(task_id='eslite_update_price', python_callable=eslite_update_price)

    task_11 = PythonOperator(task_id='momo_register_from_catalog', python_callable=momo_register_from_catalog)
    task_12 = PythonOperator(task_id='momo_update_price', python_callable=momo_update_price)

    task_1 >> task_2 >> task_3 >> task_4 >> task_5 >> task_6 >> task_7 >> task_8 >> task_9 >> task_10 >> task_11 >> task_12


