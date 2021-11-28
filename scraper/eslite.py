import time
import requests
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import date, timedelta
from fake_useragent import UserAgent
from data_processor import *
from scrapers import multi_scrapers
from ip_list import ip_list
import random
import datetime
import pytz
# from airflow import DAG
# from airflow.operators.python_operator import PythonOperator

CETEGORY_URL = 'https://athena.eslite.com/api/v1/categories' 
MAIN_CAMPAIGN_URL = 'https://athena.eslite.com/api/v1/headers'
MAIN_RECO_ITEM_URL = 'https://athena.eslite.com/api/v1/banners/L1Page/{}/big_b,recommend_new_products,editor_recommend'
CATALOG_URL = 'https://athena.eslite.com/api/v2/search?final_price=0,&sort=manufacturer_date+desc&size=100&start={}&categories=[{}]' # Main api to get product price, use with paging, category id
PRODUCT_PAGE = 'https://athena.eslite.com/api/v1/products/' # Single product page prefix url, must add item code at the end
USER_AGENT = UserAgent().random
TODAY = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y-%m-%d")
TODAY_FOR_COLLECTION_NAME = (datetime.datetime.now(pytz.timezone('Asia/Taipei'))).strftime("%m%d")
DATE_SUBTRACT_1 = (datetime.datetime.now(pytz.timezone('Asia/Taipei')) - timedelta(days=1)).strftime("%m%d")
YESTERDAY_FOR_EORROR_CHECKER = ''.join(DATE_SUBTRACT_1)
DATE_SUBTRACT_7 = (datetime.datetime.now(pytz.timezone('Asia/Taipei')) - timedelta(days=7)).strftime("%m%d")
DATE_FOR_DELETE_COLLECTION_NAME = ''.join(DATE_SUBTRACT_7)




# client = MongoClient('localhost', 27017)
load_dotenv()
client = MongoClient('mongodb://{}:{}@{}/?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&directConnection=true&ssl=false'.format(os.getenv("mon_user"), os.getenv("mon_passwd"), os.getenv("mon_host")))


db = client.bookbar
# Set collection name with variable for auto addition / validation / deletion
catalog_today = db['eslite_catalog_' + TODAY_FOR_COLLECTION_NAME]
catalog_yesterday = db['eslite_catalog_' + YESTERDAY_FOR_EORROR_CHECKER]
catalog_last_7_days = db['eslite_catalog_' + DATE_FOR_DELETE_COLLECTION_NAME]
catalog_tem_today = db.eslite_catalog_tem_today
category_list = db.eslite  # Category List
main_campaign = db.eslite_L1_campaign  # Main Page Campaign List
category_error = db.eslite_category_error
product_info = db.eslite_product_info
product_error = db.eslite_product_error
new_product_catalog = db.eslite_new_product_catalog
unfound_product_catalog = db.eslite_unfound_product_catalog
phase_out_product_catalog = db.eslite_phase_out_catalog
timecounter = db.timecounter

    
def create_category_list(url):
    """ Get all category/subcate id """
    data = requests.get(url, headers= {'user-agent': USER_AGENT }).json()
    cate_list = []
    for cate in data:
        cate_list.append(cate)

    # Create list for Category / Subcategory Level
    nomenclature = []
    for section in cate_list:
        nomenclature.append({'id': section['id'], 
                            'depth': section['depth'], 
                            'description': section['description'],
                            'path': section['path']
                            })
        for cate in section['children']:
            nomenclature.append({'id': cate['id'], 
                                'depth': cate['depth'], 
                                'description': cate['description'],
                                'path': cate['path']
                                })
            for subcate in cate['children']:
                if '新書' not in subcate['description']:
                    nomenclature.append({'id': subcate['id'], 
                                        'depth': subcate['depth'], 
                                        'description': subcate['description'],
                                        'path': subcate['path']
                                        })
    mongo_insert(category_list, nomenclature)

def get_product_list(url, category_id):
    paging = 0
    pause_count = 0
    catalog = []
    while True:
        print('============== start', category_id, 'with paging:', paging, '==============')
        if pause_count % 10 == 0:
            time.sleep(1)
        pause_count += 1
        try:
            ip = random.choice(ip_list)
            data = requests.get(url.format(paging, category_id), headers= {'user-agent': USER_AGENT }, timeout=120).json()
        except Exception as e:
            ip = random.choice(ip_list)
            print('category {} fetching data at paging {} has error, try again in 2 seconds'.format(category_id, paging))
            print(e)
            time.sleep(2)
            data = requests.get(url.format(paging, category_id), headers= {'user-agent': USER_AGENT }, timeout=120).json()

        if len(data['hits']['hit']) == 0:
            print('category {} at page {} has no more'.format(category_id, paging))
            break
        product_list = data['hits']['hit']
        for each in product_list:
            field = each['fields']
            catalog.append({
                'category_id': category_id,
                'eslite_pid': each['id'],
                'discount_type': field['discount_type'], 
                'create_date': field['create_date'], 
                'title': field['name'], 
                'description': field['description'],
                'status': field['status'], 
                'price': field['final_price'], 
                'original_price': field['mprice'], 
                'product_url': field['url'], 
                'product_photo_url': 'https://s.eslite.dev' + field['product_photo_url'], 
                'stock': field['stock'], 
                'discount': field['discount'], 
                'eslite_sn': field['eslite_sn'], 
                'isbn': field['isbn'], 
                'isbn10': field['isbn10'], 
                'ISBN': field['ean'], 
                'original_name': field['original_name'], 
                'origin_subtitle': field['origin_subtitle'], 
                'author': field['author'][0], 
                'manufacturer': field['manufacturer'][0], 
                'discount_range': field['discount_range'], 
                'publish_date': field['manufacturer_date'], 
                'is_book': field['is_book']
            })
        paging += 1
    return catalog

def get_product_info(url_to_scrape, sliced_list, target_id_key):
    i = 0
    product_info = []
    not_found_list = []
    for each in sliced_list:   
        product_url = url_to_scrape + each['eslite_pid']
        isbn = each['ISBN']
        try:
            data = requests.get(product_url, headers= {'user-agent': USER_AGENT}, timeout=120).json()
        except:
            # Eslite api sometimes won't response, so try second time
            print('{} fetching data failed, try again in 10 seconds'.format(target_id_key))
            time.sleep(10)
            data = requests.get(product_url, headers= {'user-agent': USER_AGENT}, timeout=120).json()
        try: 
            product_info.append({
                'name': data['name'],
                'publish_date': data['manufacturer_date'],
                'final_price': data['final_price'],
                'retail_price': data['retail_price'],
                'stock': data['stock'],
                'eslite_pid': data['product_guid'],
                'ISBN': isbn,
                'photos': data['photos'],
                'supplier': data['supplier'],
                'author': data['auth'],
                'descriptions': data['descriptions'],
                'product_specifications': data['product_specifications'],
                'is_book': data['is_book'],
                'product_type': data['product_type'],
                'product_attachments': data['product_attachments'],
                'range': data['range'],
                'level1': data['level1'],
                'level2': data['level2'],
                'level3': data['level3'],
                'activities': data['activities'],
                'track_date': TODAY
                })
        except Exception as e:
            try:
                print('item {} : {}'.format(product_url, data['message']))
                not_found_list.append({
                    'eslite_pid': each['eslite_pid'], 
                    'product_url': each['product_url'],
                    'track_date': TODAY,
                    'type': "phase_out_from_scrape"})
            except:
                print('check {} with error message: {}'.format(data, e))
                not_found_list.append({
                    'eslite_pid': '', 
                    'product_url': '',
                    'track_date': TODAY,
                    'type': "unexpected_error",
                    'message': e})                
        i += 1
    if len(not_found_list) > 0:
        mongo_insert(product_error, not_found_list)
    return product_info

def phased_out_checker(url_to_scrape, sliced_list, target_id_key):
    i = 0
    product_info = []
    phased_out_list = []
    for product in sliced_list:
        if i % 10 == 0: 
            time.sleep(1) 

        product_url = url_to_scrape + product['eslite_pid']
        try:
            data = requests.get(product_url, headers= {'user-agent': USER_AGENT}, timeout=60).json()
        except Exception as e:
            # Eslite api sometimes won't response, so try second time
            print('{} fetching data failed, try again in 10 seconds'.format(target_id_key))
            print(e)
            time.sleep(10)
            data = requests.get(product_url, headers= {'user-agent': USER_AGENT}, timeout=60).json()
        try:
            product.pop('_id')
            product['final_price'] = data['final_price']
            product['retail_price'] = data['retail_price']
            product['stock'] = data['stock']
            product_info.append(product)
        except:
            phased_out_list.append(product)
        i += 1
    if len(phased_out_list) > 0:
        phase_out_product_catalog.insert_many(phased_out_list)
    return product_info


# Step 1: Build up category list if not exists for later scrapping, it's one time set up
# if not category_list.find_one():
#     create_category_list(CETEGORY_URL)

# Step 2. Scrap daily to get the price and looking for new items record error into [error_catalog]
def scrap_category():
    start = time.time()
    start_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    for i in range(2):
        category_query = {'depth':"3"}
        list_to_scrape = scan_category_for_scraping(catalog_tem_today, 'category_id', category_list, category_query, 'id')
        multi_scrapers(
            worker_num = 5, 
            list_to_scrape = list_to_scrape, 
            url_to_scrape = CATALOG_URL, 
            target_id_key = 'id', 
            db_to_insert = catalog_tem_today, 
            scraper_func = get_product_list, 
            insert_func = mongo_insert
        )
    unfinished_list = scan_category_for_scraping(catalog_tem_today, 'category_id', category_list, category_query, 'id')
    if len(unfinished_list) > 0:
        unfinished_category_list = create_new_field(unfinished_list, error_date=TODAY)
        mongo_insert(category_error, unfinished_category_list)
    end = time.time()
    end_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    raw_number = catalog_tem_today.count_documents({})
    timecounter.insert_one({'date': TODAY, 'platform': 'eslite', 'step': 'scrape catalog', 'time': end - start, 'start': start_time, 'end': end_time, 'quantity': raw_number})


# Step 3. The raw catalog contains duplicate products; remove them from [catalog_tem_today] 
#         and copy cleaned catalog to [catalog_today] then delete [catalog_tem_today]
def remove_duplicates():
    start = time.time()
    start_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    copy_to_collection(catalog_tem_today, catalog_today, 'eslite_pid')
    end = time.time()
    end_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    duplicate = catalog_tem_today.count_documents({}) - catalog_today.count_documents({})
    today_quantity = catalog_today.count_documents({})
    db.drop_collection(catalog_tem_today)
    timecounter.insert_one({'date': TODAY, 'platform': 'eslite', 'step': 'remove duplicates', 'time': end - start, 'start': start_time, 'end': end_time, 'quantity': duplicate})
    timecounter.insert_one({'date': TODAY, 'platform': 'eslite', 'step': 'create_catalog', 'quantity': today_quantity})

# Step 4. Mutually compare[catalog_today] with [catalog_yesterday], 
#         phase out product in [phase_out_product_catalog]
#         new product in [new_prodcut_catalog]
def checking_new_unfound_products():    
    start = time.time()
    start_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    daily_change_tracker(catalog_today, catalog_yesterday, 'eslite_pid', new_product_catalog, unfound_product_catalog)
    end = time.time()
    end_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    unfound = unfound_product_catalog.count_documents({})
    timecounter.insert_one({'date': TODAY, 'platform': 'eslite', 'step': 'track change', 'time': end - start, 'start': start_time, 'end': end_time, 'quantity': unfound}) 


# Step 5. Use [new_prodcut_catalog] to request single product's api and insert into product_info
def scrap_new_products():
    start = time.time()
    start_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    product_catalog = new_product_catalog.find({'track_date': TODAY})
    product_list = convert_mongo_object_to_list(product_catalog)
    if len(product_list) > 0:
        multi_scrapers(
            worker_num = 10, 
            list_to_scrape = product_list, 
            url_to_scrape = PRODUCT_PAGE, 
            target_id_key = 'eslite_pid', 
            db_to_insert = product_info, 
            scraper_func = get_product_info, 
            insert_func = mongo_insert,
            slicing=True
        )  
    end = time.time()
    end_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    new_product = product_info.count_documents({'track_date': TODAY})
    timecounter.insert_one({'date': TODAY, 'platform': 'eslite', 'step': 'scrape product', 'time': end - start, 'start': start_time, 'end': end_time, 'quantity': new_product})


# Step 6: Reading [unfound_product_catalog], add current back to [catalog_today], phased out to [phase_out_product_catalog]
#         Delete after finishing scraping
def scrap_unfound_products():
    start = time.time()
    start_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    product_catalog = unfound_product_catalog.find()
    product_list = convert_mongo_object_to_list(product_catalog)
    if len(product_list) > 0:
        multi_scrapers(
            worker_num = 20, 
            list_to_scrape = product_list, 
            url_to_scrape = PRODUCT_PAGE, 
            target_id_key = 'eslite_pid', 
            db_to_insert = catalog_today, 
            scraper_func = phased_out_checker, 
            insert_func = mongo_insert,
            slicing=True
        )
        db.drop_collection(unfound_product_catalog)
    end = time.time()
    end_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    phase_out = phase_out_product_catalog.count_documents({'track_date': TODAY})
    timecounter.insert_one({'date': TODAY, 'platform': 'eslite', 'step': 'check unfound', 'time': end - start, 'start': start_time, 'end': end_time, 'quantity': phase_out})

# Step 7. Delete catalog of 7 days age, EX: today is '2021-10-26', so delete '2021-10-19'
def drop_old_collection():
    db.drop_collection(catalog_last_7_days)
