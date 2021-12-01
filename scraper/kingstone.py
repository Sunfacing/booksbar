from pymongo import MongoClient
from collections import defaultdict
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from .data_processor import *
from .scrapers import multi_scrapers
from .ip_list import ip_list, back_up_ip_list
import requests
import random
import os
from dotenv import load_dotenv
# from airflow import DAG
# from airflow.operators.python_operator import PythonOperator
from datetime import date, timedelta
import datetime
import pytz
import time
# client = MongoClient('localhost', 27017)
# client = MongoClient(f'mongodb://{os.getenv("mon_user")}:{os.getenv("mon_passwd")}@{os.getenv("mon_host")}/?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&directConnection=true&ssl=false')
load_dotenv()
client = MongoClient('mongodb://{}:{}@{}/?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&directConnection=true&ssl=false'.format(os.getenv("mon_user"), os.getenv("mon_passwd"), os.getenv("mon_host")))
db = client.bookbar

TODAY = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y-%m-%d")
TODAY_FOR_COLLECTION_NAME = (datetime.datetime.now(pytz.timezone('Asia/Taipei'))).strftime("%m%d")
DATE_SUBTRACT_1 = (datetime.datetime.now(pytz.timezone('Asia/Taipei')) - timedelta(days=1)).strftime("%m%d")
YESTERDAY_FOR_EORROR_CHECKER = ''.join(DATE_SUBTRACT_1)
DATE_SUBTRACT_7 = (datetime.datetime.now(pytz.timezone('Asia/Taipei')) - timedelta(days=7)).strftime("%m%d")
DATE_FOR_DELETE_COLLECTION_NAME = ''.join(DATE_SUBTRACT_7)

# Set collection name with variable for auto addition / validation / deletion
catalog_today = db['kingstone_catalog_' + TODAY_FOR_COLLECTION_NAME]
catalog_yesterday = db['kingstone_catalog_' + YESTERDAY_FOR_EORROR_CHECKER]
catalog_last_7_days = db['kingstone_catalog_' + DATE_FOR_DELETE_COLLECTION_NAME]
catalog_tem_today = db.kingstone_tem_today

category_list = db.kingstone
category_error = db.kingstone_category_error
page_error = db.kingstone_page_error
product_info = db.kingstone_product_info
product_error = db.kingstone_product_error
new_prodcut_catalog = db.kingstone_new_product_catalog
unfound_product_catalog = db.kingstone_unfound_product_catalog
phase_out_product_catalog = db.kingstone_phase_out_catalog
timecounter = db.timecounter



CATALOG_URL = 'https://www.kingstone.com.tw{}?sort=pu_desc&&page={}'
PRODUCT_PAGE = 'https://www.kingstone.com.tw/basic/'
DIVISION = [['book', '中文'], ['english', '英文']]
HEADERS = {'User-Agent': UserAgent().random}




def get_category_list(div):
    url_prefix = 'https://www.kingstone.com.tw/'
    url_to_division = url_prefix + div[0]
    page  = requests.get(url_to_division, headers = HEADERS) 
    page.enconding = 'utf-8'
    section_links = BeautifulSoup(page.content, 'html.parser')\
                    .find('nav', {'class': 'navcolumn_classlevel'}).find_all('li')
    nomenclature = []

    # Go to first layer under 中文/外文 [Section Level]
    for sec in section_links:
        sec_link = sec.find('a')['href']
        sec_nm = sec.find('a').getText()
        url_to_sec = url_prefix + sec_link
        page  = requests.get(url_to_sec, headers = HEADERS)
        category_links  = BeautifulSoup(page.content, 'html.parser')\
                        .find('nav', {'class': 'navcolumn_classlevel'}).find_all('li')

        # Go to second layer under 中文/外文 -> 心理勵志 [Category Level]
        for category in category_links:
            if category.find('ul') is not None:
                cate_list = category.find('ul').find_all('li')
                for cate in cate_list:
                    cate_link = cate.find('a')['href']
                    cate_nm = cate.getText()
                    url_to_cate = url_prefix + cate_link
                    page  = requests.get(url_to_cate, headers = HEADERS)
                    subcategory_links  = BeautifulSoup(page.content, 'html.parser')\
                                        .find('nav', {'class': 'navcolumn_classlevel'}).find_all('li')

                    # Go to third layer under 中文/外文 -> 心理勵志 -> 心理學各論 [Subcategory Level]
                    for subcate in subcategory_links:
                        if subcate.find('ul') is not None:
                            sub_list = subcate.find('ul').find_all('li')
                            for sub in sub_list:
                                if sub.find('ul') is not None:
                                    sub_extracted_list = sub.find('ul').find_all('a')
                                    for each in sub_extracted_list:
                                        subcate_link = each['href']
                                        subcate_nm = each.getText()
                                        nomenclature.append({'division_code': div[0], 'division_nm': div[1],
                                                            'section_code': sec_link, 'section_nm': sec_nm, 
                                                            'category_code': cate_link, 'category_nm': cate_nm, 
                                                            'subcate_code': subcate_link, 'subcate_nm': subcate_nm})
                                        print({'division_code': div[0], 'division_nm': div[1],
                                                'section_code': sec_link, 'section_nm': sec_nm, 
                                                'category_code': cate_link, 'category_nm': cate_nm, 
                                                'subcate_code': subcate_link, 'subcate_nm': subcate_nm})                                 
    return nomenclature

def create_category_list():
    for i in range(len(DIVISION)):
        result = get_category_list(DIVISION[i])
        mongo_insert(category_list, result)

def get_product_list(url, subcate_code):
    i = 1
    catalog = []
    error_pages = []
    while True:
        ip = random.choice(ip_list)
        product_url = url.format(subcate_code, i)
        try:
            try:
                page = requests.get(product_url, headers= HEADERS, proxies={"http": ip, "https": ip}, timeout=60)
            except:
                # Eslite api sometimes won't response, so try second time
                print('{} fetching data failed, try again in 10 seconds'.format(subcate_code))
                time.sleep(10)
                try:
                    ip = random.choice(back_up_ip_list)
                    page = requests.get(product_url, headers= HEADERS, proxies={"http": ip, "https": ip}, timeout=60)
                except:
                    error_pages.append({'subcate_code': subcate_code, 'page': i, 'fail_date': TODAY})
            page.enconding = 'utf-8'
            category_links = BeautifulSoup(page.content, 'html.parser').find_all('li', {'class': 'displayunit'})
            print('now is {} at page {}'.format(subcate_code, i), 'with result', len(category_links)) 
            if len(category_links) == 0:
                print(subcate_code, 'is done at page', i-1)
                break
            for product in category_links:
                cover_img_url = product.find('div', {'class': 'coverbox'}).find('img')['data-src']
                title = product.find('div', {'class': 'coverbox'}).find('img')['title']
                product_url = 'https://www.kingstone.com.tw/' + product.find('h3', {'class': 'pdnamebox'}).find('a')['href']
                product_code = product_url.split('/')[-1].split('?')[0]
                # subcate_code = product_url.split('_')[-1]
                try:
                    author = product.find('span', {'class': 'author'}).find('a').getText()
                except:
                    author = ''

                try:        
                    publisher = product.find('span', {'class': 'publish'}).find('b').getText()
                except:
                    publisher = ''

                try:
                    publish_date = product.find('span', {'class': 'pubdate'}).find('b').getText()
                except:
                    publish_date = ''

                try:
                    price_info = product.find('div', {'class': 'buymixbox'}).find_all('b')
                    discount = price_info[0].getText()
                except:
                    discount = 0

                try:
                    price = price_info[1].getText()
                except:
                    price = discount
                    discount = 0

                try:
                    availability = product.find('div', {'class': 'btnbuyset'}).find('span').getText()
                except:
                    availability = 'Unknown'

                catalog.append({'subcate_id': subcate_code,
                                'kingstone_pid': product_code, 
                                'title': title,
                                'author': author,
                                'publisher': publisher,
                                'publish_date': publish_date,
                                'product_url': product_url,
                                'img_url': cover_img_url,
                                'price': price,
                                'discount': discount,
                                'availability': availability
                                })
        except:
            print('now is {} at page {}'.format(subcate_code, i), 'with result', len(category_links))
            error_pages.append({'subcate_code': subcate_code, 'page': i, 'fail_date': TODAY})
        i += 1
        # if i < 300:
        #     time.sleep(1)
    if len(error_pages) > 0:
        mongo_insert(page_error, error_pages)
    return catalog



def get_product_info(url_to_scrape, sliced_list, target_id_key):
    product_info = []
    not_found_list = []
    i = 0
    for each in sliced_list:
        # ip = random.choice(ip_list)
        product_id = each[target_id_key]
        subcate_id = each['subcate_id']
        print('starting {}'.format(product_id))
        product_url = url_to_scrape + product_id
        print(product_url)
        # In case website block connection, pause 10 seconds
        try:
            ip = random.choice(ip_list)
            page  = requests.get(product_url, headers=HEADERS, proxies={"http": ip, "https": ip}, timeout=60)
        except:
            print('{} fetching data {} failed, try again in 10 seconds'.format(subcate_id, product_url))
            time.sleep(10)
            try:
                # ip = random.choice(back_up_ip_list)
                page  = requests.get(product_url, headers=HEADERS, proxies={"http": ip, "https": ip}, timeout=60)
            except:
                not_found_list.append({'subcate_id': subcate_id, 'product_id': product_id, 'track_date': TODAY})
        # This try block will ignore single item failure, and continue    
        try: 
            if page is None:
                print(subcate_id, 'gets None, go check')
                continue
            page.enconding = 'utf-8'
            page_content = BeautifulSoup(page.content, 'html.parser')
            data = defaultdict(dict)
            
            # Product_id and Title
            data['subcate_id'] = subcate_id
            data['kingstone_pid'] = product_id
            title = page_content.find('h1', {'class': 'pdname_basic'}).getText()
            data['title'] = title

            # Cover photo, kingstone has fixed api to get
            data['main_img'] = 'https://cdn.kingstone.com.tw/book/images/product/{}/{}/{}b.jpg'.format(product_id[:5], product_id, product_id)

            # Content photos, some photos are broken, which will be omitted
            imgs = page_content.find_all('li', {'class': 'swiper-slide'})
            img_collection = []
            for img in imgs:
                try: 
                    img_collection.append(img.find('img')['data-src'])
                    data['images'] = img_collection
                except: 
                    data['images'] = ''
            
            # Original price, ex: 170元 -> 170
            original_price = page_content.find('div', {'class': 'basicfield'}).find('b').getText()
            if original_price is not None: data['original_price'] = original_price

            # Content description, this contains html tag, so store in text
            description = page_content.find('div', {'class': 'pdintro_txt1field panelCon'})
            data['description'] = str(description)
                    
            # For author description, same as content description, saving html tag in text
            author_description = page_content.find('div', {'class': 'authorintrofield panelCon'})   
            data['author_description'] = str(author_description)

            # Same, this has html tag
            table_of_contents = page_content.find('div', {'class': 'catalogfield panelCon'})
            data['table_of_contents'] = str(table_of_contents)

            # This area contains two information in the same row, must seperate to save
            detail_info = page_content.find('ul', {'class': 'table_1col_deda'})
            if detail_info is not None:
                for each in detail_info.find_all('ul', {'class': 'table_2col_deda'}):
                    name = each.find('li', {'class': 'table_th'}).getText()
                    value = each.find('li', {'class': 'table_td'}).getText()
                    name2 = each.find('li', {'class': 'table_th'}).findNext('li', {'class': 'table_th'}).getText()
                    value2 = each.find('li', {'class': 'table_td'}).findNext('li', {'class': 'table_td'}).getText()
                    data[name] = value
                    data[name2] = value2

            # Save in list if there's any
            reader_comments = page_content.find_all('li', {'class': 'comment1unit'})
            comments = []
            if len(reader_comments) > 0:
                for each in reader_comments:
                    date = each.find('span', {'class': 'date_cmt1'}).getText()
                    comment = each.find('div', {'class': 'td_comment1'}).getText()
                    comments.append({date: comment})
                data['reader_comments'] = comments
            else:
                data['reader_comments'] = ''

            data['track_date'] = TODAY
            product_info.append(data)
        except Exception as e:
            print(e)
            print('{} at product {} is failed, go check'.format(subcate_id, product_id))
            not_found_list.append({'subcate_id': subcate_id, 'product_id': product_id, 'track_date': TODAY})
        i += 1
        time.sleep(random.randint(1, 3))
    if len(not_found_list) > 0:
        mongo_insert(product_error, not_found_list)
    return product_info

def phased_out_checker(url_to_scrape, sliced_list, target_id_key):
    i = 0
    current_product_list = []
    phased_out_list = []
    for product in sliced_list:
        if i % 3 == 0 and i > 0:
            time.sleep(random.randint(1, 3))
        ip = random.choice(ip_list)
        product_id = product[target_id_key]
        product_url = url_to_scrape + product_id
        if i % 10 == 0:
            time.sleep(1)       
        try:
            ip = random.choice(ip_list)
            page  = requests.get(product_url, headers = HEADERS, proxies={"http": ip, "https": ip}, timeout=60)
        except:
            # In case website block connection, pause 10 seconds
            print('{} fetching data failed, try again in 10 seconds'.format(product_id))
            time.sleep(10)
            try:
                ip = random.choice(back_up_ip_list)
                page  = requests.get(product_url, headers = HEADERS, proxies={"http": ip, "https": ip}, timeout=60)
            except:
                print(product_id, 'failed')
        try:
        # Update product price and availability info before write back to [catalog_today]   
            page.enconding = 'utf-8'
            page_content = BeautifulSoup(page.content, 'html.parser')
            availability = page_content.find('span', {'class': 'txt_btnbuyb'}).getText()
            if availability == '立即結帳':
                availability == '加入購物車'
            price = page_content.find('b', {'class': 'sty2 txtSize2'}).getText()
            try: 
                discount = page_content.find('b', {'class': 'b1'}).getText()
            except: 
                discount = 0
            product.pop('_id')
            product.pop('type')
            product['availability'] = availability
            product['price'] = price
            product['discount'] = discount
            current_product_list.append(product)
        except:
            product.pop('_id')
            phased_out_list.append(product)
        i += 1
    if len(phased_out_list) > 0:
        phase_out_product_catalog.insert_many(phased_out_list)
    return current_product_list





# Step 1: Get all subcategory id and scrape, with batch insertion at subcategory level #
if not category_list.find_one():
    create_category_list()


def ks_scrap_category():
    # # Step 2. Scrap daily to get the price and looking for new items record error into [error_catalog]
    start = time.time()
    start_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    for i in range(2):
        category_query = {'subcategory_id': {'$regex': 'book'}}
        list_to_scrape = scan_category_for_scraping(catalog_tem_today, 'subcate_id', category_list, category_query, 'subcategory_id')
        multi_scrapers(10, list_to_scrape, CATALOG_URL, 'subcategory_id', catalog_tem_today, get_product_list, mongo_insert)
    unfinished_list = scan_category_for_scraping(catalog_tem_today, 'subcate_id', category_list, category_query, 'subcategory_id')
    if len(unfinished_list) > 0:
        unfinished_category_list = create_new_field(unfinished_list, error_date=TODAY)
        mongo_insert(category_error, unfinished_category_list)
    end = time.time()
    end_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    raw_number = catalog_tem_today.count_documents({})
    timecounter.insert_one({'date': TODAY, 'platform': 'kingstone', 'step': 'scrape catalog', 'time': end - start, 'start': start_time, 'end': end_time, 'quantity': raw_number})

def ks_remove_duplicates():
    # # Step 3. The raw catalog contains duplicate products; remove them from [catalog_tem_today] 
    # #         and copy cleaned catalog to [catalog_today] then delete [catalog_tem_today]
    start = time.time()
    start_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    copy_to_collection(catalog_tem_today, catalog_today, 'kingstone_pid')
    end = time.time()
    end_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    duplicate = catalog_tem_today.count_documents({}) - catalog_today.count_documents({})
    today_quantity = catalog_today.count_documents({})
    db.drop_collection(catalog_tem_today)
    timecounter.insert_one({'date': TODAY, 'platform': 'kingstone', 'step': 'remove duplicates', 'time': end - start, 'start': start_time, 'end': end_time, 'quantity': duplicate})
    timecounter.insert_one({'date': TODAY, 'platform': 'kingstone', 'step': 'create_catalog', 'quantity': today_quantity})



def ks_checking_new_unfound_products(): 
    # Step 4. Mutually compare[catalog_today] with [catalog_yesterday], 
    #         phase out product in [phase_out_product_catalog]
    #         new product in [unfound_product_catalog]
    start = time.time()
    start_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    daily_change_tracker(catalog_today, catalog_yesterday, 'kingstone_pid', new_prodcut_catalog, unfound_product_catalog)
    end = time.time()
    end_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    unfound = unfound_product_catalog.count_documents({})
    timecounter.insert_one({'date': TODAY, 'platform': 'kingstone', 'step': 'track change', 'time': end - start, 'start': start_time, 'end': end_time, 'quantity': unfound})     

    
def ks_scrap_new_products():
    # Step 5: Reading catalog and scraped single product info 
    start = time.time()
    start_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    product_catalog = new_prodcut_catalog.find({'track_date': TODAY})
    product_list = convert_mongo_object_to_list(product_catalog)
    multi_scrapers(
        worker_num = 10, 
        list_to_scrape = product_list, 
        url_to_scrape = PRODUCT_PAGE, 
        target_id_key = 'kingstone_pid', 
        db_to_insert = product_info, 
        scraper_func = get_product_info, 
        insert_func = mongo_insert,
        slicing=True
    )
    end = time.time()
    end_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    new_product = product_info.count_documents({'track_date': TODAY})
    timecounter.insert_one({'date': TODAY, 'platform': 'kingstone', 'step': 'scrape product', 'time': end - start, 'start': start_time, 'end': end_time, 'quantity': new_product}) 

def ks_scrap_unfound_products():
    # Step 6: Reading [unfound_product_catalog], add current back to [catalog_today], phased out to [phase_out_product_catalog]
    #         Delete after finishing scraping
    start = time.time()
    start_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    product_catalog = unfound_product_catalog.find()
    product_list = convert_mongo_object_to_list(product_catalog)
    multi_scrapers(
        worker_num = 10, 
        list_to_scrape = product_list, 
        url_to_scrape = PRODUCT_PAGE, 
        target_id_key = 'kingstone_pid', 
        db_to_insert = catalog_today, 
        scraper_func = phased_out_checker, 
        insert_func = mongo_insert,
        slicing=True
    )
    db.drop_collection(unfound_product_catalog)
    end = time.time()
    end_time = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%H:%M:%S")
    phase_out = phase_out_product_catalog.count_documents({'track_date': TODAY})
    timecounter.insert_one({'date': TODAY, 'platform': 'kingstone', 'step': 'check unfound', 'time': end - start, 'start': start_time, 'end': end_time, 'quantity': phase_out})

def ks_drop_old_collection():
    # Step 7. Delete catalog of 7 days age, EX: today is '2021-10-26', so delete '2021-10-19'
    db.drop_collection(catalog_last_7_days)
