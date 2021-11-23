from pymongo import MongoClient
from collections import defaultdict
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from data_processor import *
from scrapers import multi_scrapers
import requests
import time
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import date, timedelta
import datetime
import pytz


TODAY = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y-%m-%d")
TODAY_FOR_COLLECTION_NAME = (datetime.datetime.now(pytz.timezone('Asia/Taipei'))).strftime("%m%d")
DATE_SUBTRACT_1 = (datetime.datetime.now(pytz.timezone('Asia/Taipei')) - timedelta(days=1)).strftime("%m%d")
YESTERDAY_FOR_EORROR_CHECKER = ''.join(DATE_SUBTRACT_1)
DATE_SUBTRACT_7 = (datetime.datetime.now(pytz.timezone('Asia/Taipei')) - timedelta(days=7)).strftime("%m%d")
DATE_FOR_DELETE_COLLECTION_NAME = ''.join(DATE_SUBTRACT_7)

# client = MongoClient('localhost', 27017)
client = MongoClient('mongodb://bartender:books@ec2-3-17-181-14.us-east-2.compute.amazonaws.com:27017/?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&directConnection=true&ssl=false')
db = client.bookbar

# Set collection name with variable for auto addition / validation / deletion
catalog_today = db['momo_catalog_' + TODAY_FOR_COLLECTION_NAME]
catalog_yesterday = db['momo_catalog_' + YESTERDAY_FOR_EORROR_CHECKER]
catalog_last_7_days = db['momo_catalog_' + DATE_FOR_DELETE_COLLECTION_NAME]

category_list = db.momo  # Category List
catalog_tem_today = db.momo_catalog_tem_today
page_error = db.kingstone_page_error
category_error = db.momo_category_error
product_info = db.momo_product_info
product_error = db.momo_product_error
new_prodcut_catalog = db.momo_new_product_catalog
phase_out_product_catalog = db.momo_phase_out_catalog
unfound_product_catalog = db.momo_unfound_product_catalog
timecounter = db.timecounter

SECTION_URL = 'https://m.momoshop.com.tw/category.momo?cn=4000000000&cid=dir&oid=dir&imgSH=fourCardType'
CATALOG_URL = 'https://m.momoshop.com.tw/cateGoods.momo?cn={}&page={}&sortType=5&imgSH=itemizedType'
PRODUCT_URL = 'https://m.momoshop.com.tw//goods.momo?i_code='
HEADERS = {'User-Agent': UserAgent().random,'X-Requested-With': 'XMLHttpRequest'}



def category_path_finder(data, url):
    try:
        code = data.find('a')['subcatecode']
        page  = requests.get(url + code, headers = HEADERS)
        try:
            links = BeautifulSoup(page.content, 'html.parser').find('div', {'class': 'classificationList'}).find_all('dd')
        except:           
            try:
                links = BeautifulSoup(page.content, 'html.parser').find('article', {'class': 'pathArea'}).find_all('li')
            except:
                return None

    except:
        print(data, 'is failed')
        return None   

    return links

def get_category_list(url):
    path_url_prefix = 'https://m.momoshop.com.tw/category.momo?cn='
    nomenclature = []
    page  = requests.get(url, headers = HEADERS, timeout=60) 
    page.enconding = 'utf-8'
    section_links = BeautifulSoup(page.content, 'html.parser').find('div', {'class': 'classificationList'}).find_all('dd')
    for sec in section_links:
        category_links = category_path_finder(sec, path_url_prefix)

        for category in category_links:
            subcate_links = category_path_finder(category, path_url_prefix)

            for sub in subcate_links:
                sub_links = category_path_finder(sub, path_url_prefix)

                if sub_links is not None:
                    path = ['section', 'category', 'subcate']
                    i = 0
                    data = defaultdict(dict)
                    for li in sub_links[1:]:
                        try:
                            sub_code = li.find('a')['cn']
                            sub_nm = li.find('a').getText()
                            data[path[i] + '_code'] = sub_code
                            data[path[i] + '_nm'] = sub_nm
                        except:
                            continue
                        i += 1
                    nomenclature.append(data)
                    print(data)
                else:
                    print(sub, 'is failed')
    mongo_insert(category_list, nomenclature)

def get_product_list(url, subcate_code):
    i = 1
    product_list = []
    error_pages = []
    while True:
        try:
            catalog_url = url.format(subcate_code, i)
            try:
                page  = requests.get(catalog_url, headers = HEADERS, timeout=60)
            except:
                print('something went wrong with {} at page {}, try again in 10 seconds'.format(subcate_code, i))
                time.sleep(10)
                try:
                    page  = requests.get(catalog_url, headers = HEADERS, timeout=60)                
                except:
                    error_pages.append({'subcate_code': subcate_code, 'page': i, 'fail_date': TODAY})
            page.enconding = 'utf-8'
            category_links = BeautifulSoup(page.content, 'html.parser').find_all('a', {'class': 'productInfo'})
            publisher_author_links = BeautifulSoup(page.content, 'html.parser').find('p', {'class': 'publishInfo'})
            if len(category_links) == 0:
                print(subcate_code, 'is done at page', i-1)
                break

            for link in category_links:
                
                try:
                    title = link['title']
                except:
                    title = ''

                try:
                    price_discount = link.find('p', {'class': 'prdEvent'}).getText().strip()
                    price = link.find('b', {'class': 'price'}).getText().strip()
                except:
                    price = ''

                try:
                    publish_date = link.find('span', {'class': 'publishDate'}).getText()
                except:
                    publish_date = ''

                try:
                    author = str(publisher_author_links.find('a', {'class': 'writer'}).getText()).strip()
                except:
                    author = ''

                try:
                    publisher = str(publisher_author_links.find('a', {'class': 'publishing'}).getText()).strip()
                except:
                    publisher = ''

                try:
                    pic_url = link.find('img', {'class': 'goodsImg lazy lazy-loaded'})['data-original']
                    product_url = 'https://m.momoshop.com.tw/' + link['href']
                    momo_pid = product_url.split('i_code=')[-1].split('&')[0]
                except:
                    pic_url = ''
                    product_url = ''

                product_list.append({'momo_pid': momo_pid,
                                    'subcate_code': subcate_code, 
                                    'title': title, 
                                    'price_discount': price_discount, 
                                    'price': price, 
                                    'publish_date': publish_date, 
                                    'author': author,
                                    'publisher': publisher,
                                    'product_url': product_url, 
                                    'pic_url': pic_url})

        except Exception as e:
            print('now is {} at page {}'.format(subcate_code, i), 'with result', len(category_links))
            error_pages.append({'subcate_code': subcate_code, 'page': i, 'fail_date': TODAY})
        i += 1
    if len(error_pages) > 0:
        mongo_insert(page_error, error_pages)
    return product_list

def get_product_info(url_to_scrape, sliced_list, target_id_key):
    info_list = []
    not_found_list = []
    i = 0
    for product in sliced_list:       
        data = defaultdict(dict)
        data['subcate_code'] = product['subcate_code']
        url = url_to_scrape + product[target_id_key]
        print(i, url)
        try:
            page  = requests.get(url, headers = HEADERS, timeout=60)
        except:
            print('{} fetching data failed, try again in 10 seconds'.format(data['subcate_code']))
            time.sleep(10)
            try:
                page  = requests.get(url, headers = HEADERS, timeout=60)
            except:
                not_found_list.append({'subcate_id': product['subcate_code'], 'product_id': product[target_id_key], 'track_date': TODAY})
        page.enconding = 'utf-8'
        page_content = BeautifulSoup(page.content, 'html.parser')
        try:
            title = page_content.find('p', {'class': 'fprdTitle'}).getText()
        except:
            title = ''
        try:
            product_info = page_content.find('div', {'class': 'Area101'})
            for info in product_info:
                try:
                    info = info.split('：')
                    label = info[0]
                    value = info[1]
                    if '作者' in label:
                        data['author'] = value
                    elif len(info) > 1:
                        data[label] = value.strip()
                except:
                    data[label] = ''
        except:
            not_found_list.append({'subcate_id': product['subcate_code'], 'product_id': product[target_id_key], 'track_date': TODAY})
        data['momo_pid'] = url.split('i_code=')[-1].split('&')[0]
        data['title'] = title
        data['track_date'] = TODAY
        i += 1
        info_list.append(data)
    return info_list

def phased_out_checker(url_to_scrape, sliced_list, target_id_key):
    current_product_list = []
    phased_out_list = []
    i = 0
    for product in sliced_list: 
        if i % 10 == 0:
            time.sleep(1)
        momo_pid = product[target_id_key]     
        product_url = url_to_scrape + product[target_id_key]
        print(i, product_url)
        try:
            page  = requests.get(product_url, headers = HEADERS, timeout=60)
        except:
            print('{} fetching data failed, try again in 10 seconds'.format(momo_pid))
            time.sleep(10)
            try:
                page  = requests.get(product_url, headers = HEADERS, timeout=60)
            except:
                pass
        page.enconding = 'utf-8'
        page_content = BeautifulSoup(page.content, 'html.parser')
        try:
            product.pop('_id')
            price = page_content.find('p', {'class': 'priceTxtArea'}).find('b').getText()
            product['price'] = price
            current_product_list.append(product)
        except Exception as e:
            print(product_url, e)
            phased_out_list.append(product)
        i += 1
    if len(phased_out_list) > 0:
        phase_out_product_catalog.insert_many(phased_out_list)
    return current_product_list





def mm_scrap_category():     
    # Step 2. Scrap daily to get the price and looking for new items record error into [error_catalog] 
    start = time.time()
    start_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    for i in range(2):
        list_to_scrape = scan_category_for_scraping(catalog_tem_today, 'subcate_code', category_list, {}, 'subcate_code')
        multi_scrapers(
            worker_num = 10, 
            list_to_scrape = list_to_scrape, 
            url_to_scrape = CATALOG_URL, 
            target_id_key = 'subcate_code', 
            db_to_insert = catalog_tem_today, 
            scraper_func = get_product_list, 
            insert_func = mongo_insert
        )
    
    unfinished_list = scan_category_for_scraping(catalog_tem_today, 'subcate_code', category_list, {}, 'subcate_code')
    if len(unfinished_list) > 0:
        unfinished_category_list = create_new_field(unfinished_list, error_date=TODAY)
        mongo_insert(category_error, unfinished_category_list)
    end = time.time()
    end_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    raw_number = catalog_tem_today.count_documents({})
    timecounter.insert_one({'date': TODAY, 'platform': 'momo', 'step': 'scrape catalog', 'time': end - start, 'start': start_time, 'end': end_time, 'quantity': raw_number})

def mm_remove_duplicates():  
    # Step 3. The raw catalog contains duplicate products; remove them from [catalog_tem_today] 
    #         and copy cleaned catalog to [catalog_today] then delete [catalog_tem_today]
    start = time.time()
    start_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    copy_to_collection(catalog_tem_today, catalog_today, 'momo_pid')
    end = time.time()
    end_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    duplicate = catalog_tem_today.count_documents({}) - catalog_today.count_documents({})
    today_quantity = catalog_today.count_documents({})
    db.drop_collection(catalog_tem_today)
    timecounter.insert_one({'date': TODAY, 'platform': 'momo', 'step': 'remove duplicates', 'time': end - start, 'start': start_time, 'end': end_time, 'quantity': duplicate})
    timecounter.insert_one({'date': TODAY, 'platform': 'momo', 'step': 'create_catalog', 'quantity': today_quantity})



def mm_checking_new_unfound_products():
    # Step 4. Mutually compare[catalog_today] with [catalog_yesterday], 
    #         phase out product in [phase_out_product_catalog]
    #         new product in [new_prodcut_catalog]
    start = time.time()
    start_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    daily_change_tracker(catalog_today, catalog_yesterday, 'momo_pid', new_prodcut_catalog, unfound_product_catalog)
    end = time.time()
    end_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    unfound = unfound_product_catalog.count_documents({})
    timecounter.insert_one({'date': TODAY, 'platform': 'momo', 'step': 'track change', 'time': end - start, 'start': start_time, 'end': end_time, 'quantity': unfound}) 

def mm_scrap_new_products():
    # Step 5. Use [new_prodcut_catalog] to request single product's api and insert into product_info
    start = time.time()
    start_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    product_catalog = new_prodcut_catalog.find({'track_date': TODAY})
    product_list = convert_mongo_object_to_list(product_catalog)
    multi_scrapers(
        worker_num = 5, 
        list_to_scrape = product_list, 
        url_to_scrape = PRODUCT_URL, 
        target_id_key = 'momo_pid', 
        db_to_insert = product_info, 
        scraper_func = get_product_info, 
        insert_func = mongo_insert,
        slicing=True
    )
    end = time.time()
    end_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    new_product = product_info.count_documents({'track_date': TODAY})
    timecounter.insert_one({'date': TODAY, 'platform': 'momo', 'step': 'scrape product', 'time': end - start, 'start': start_time, 'end': end_time, 'quantity': new_product})
    
def mm_scrap_unfound_products():
    # Step 6: Reading [unfound_product_catalog], add current back to [catalog_today], phased out to [phase_out_product_catalog]
    #         Delete after finishing scraping
    start = time.time()    
    start_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    product_catalog = unfound_product_catalog.find()
    product_list = convert_mongo_object_to_list(product_catalog)
    multi_scrapers(
        worker_num = 5, 
        list_to_scrape = product_list, 
        url_to_scrape = PRODUCT_URL, 
        target_id_key = 'momo_pid', 
        db_to_insert = catalog_today, 
        scraper_func = phased_out_checker, 
        insert_func = mongo_insert,
        slicing=True
    )
    db.drop_collection(unfound_product_catalog)
    end = time.time()
    end_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    phase_out = phase_out_product_catalog.count_documents({'track_date': TODAY})
    timecounter.insert_one({'date': TODAY, 'platform': 'momo', 'step': 'check unfound', 'time': end - start, 'start': start_time, 'end': end_time, 'quantity': phase_out})

def mm_drop_old_collection():
    # Step 7. Delete catalog of 7 days age, EX: today is '2021-10-26', so delete '2021-10-19'
    db.drop_collection(catalog_last_7_days)
       


# with DAG(
# dag_id='a_m_scraper',
# schedule_interval='40 17 * * *',
# start_date=datetime.datetime(2021, 11, 1),
# catchup=False,
# # default_args={'depends_on_past': True},
# tags=['it_is_test'],
# ) as dag:
#     task_1 = PythonOperator(task_id='scrap_category', python_callable=mm_scrap_category)
#     task_2 = PythonOperator(task_id='remove_duplicates', python_callable=mm_remove_duplicates)
#     task_3 = PythonOperator(task_id='checking_new_unfound_products', python_callable=mm_checking_new_unfound_products)
#     task_4 = PythonOperator(task_id='scrap_new_products', python_callable=mm_scrap_new_products)
#     task_5 = PythonOperator(task_id='scrap_unfound_products', python_callable=mm_scrap_unfound_products)
#     task_6 = PythonOperator(task_id='drop_old_collection', python_callable=mm_drop_old_collection)
#     task_1 >> task_2 >> task_3 >> task_4 >> task_5 >> task_6