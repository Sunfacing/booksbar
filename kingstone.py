from pymongo import MongoClient
from collections import defaultdict
from datetime import date
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from scraper_tools.data_processor import *
from scraper_tools.scrapers import multi_scrapers

from datetime import datetime
import random
import requests
import time
import json



client = MongoClient('localhost', 27017)
db = client.Bookstores

TODAY = date.today().strftime("%Y-%m-%d")
TODAY_FOR_COLLECTION_NAME = date.today().strftime("%m%d")
DATE_FOR_DELETE_COLLECTION_NAME = str(int(TODAY_FOR_COLLECTION_NAME) - 7)
YESTERDAY_FOR_EORROR_CHECKER = str(int(TODAY_FOR_COLLECTION_NAME) - 1)

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
        product_url = url.format(subcate_code, i)
        try:
            try:
                page = requests.get(product_url, headers= HEADERS)
            except:
                # Eslite api sometimes won't response, so try second time
                print('{} fetching data failed, try again in 10 seconds'.format(subcate_code))
                time.sleep(10)
                page = requests.get(product_url, headers= HEADERS)
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
    if len(error_pages) > 0:
        mongo_insert(page_error, error_pages)
    return catalog

def get_product_info(url_to_scrape, sliced_list, target_id_key):
    product_info = []
    not_found_list = []
    i = 0
    for each in sliced_list:
        product_id = each[target_id_key]
        subcate_id = each['subcate_id']
        product_url = url_to_scrape + product_id
        if i % 10 == 0:
            time.sleep(1)
        # In case website block connection, pause 10 seconds
        try:
            page  = requests.get(product_url, headers = HEADERS)
        except:
            print('{} fetching data failed, try again in 10 seconds'.format(subcate_id))
            time.sleep(10) 
            page  = requests.get(product_url, headers = HEADERS)

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
                try: img_collection.append(img.find('img')['data-src'])
                except: pass
            data['images'] = img_collection

            # Original price, ex: 170元 -> 170
            original_price = page_content.find('div', {'class': 'basicfield'}).find('b').getText()
            if original_price is not None: data['original_price'] = original_price


            # Electronic version
            electronic_book = BeautifulSoup(page.content, 'html.parser').find_all('span', {'class': 'versionbox'})
            if len(electronic_book) > 0:
                electronic_book = 'https://www.kingstone.com.tw/' + electronic_book[1].find('a')['href']
                data['e_book'] = electronic_book
            else:
                data['e_book'] = None

            # Content description, this contains html tag, so store in text
            description = page_content.find('div', {'class': 'pdintro_txt1field panelCon'})
            try:
                # Kingstone's tag are not always in the same form, handle by each condition
                # In case any unfound exception, return None
                if description is not None: 
                    if description.find('div', {'class': 'catalogfield panelCon'}) is not None:
                        data['description'] = str(description.find('div', {'class': 'catalogfield panelCon'}).find('span').getText())
                    elif description.find('div', {'class': 'pdintro_txt1field panelCon'}) is not None:
                        data['description'] = str(description.find('div', {'class': 'pdintro_txt1field panelCon'}).find('span').getText())
                    else:
                        data['description'] = str(description.find('span').getText())
            except:
                data['description'] = None

            # For author description, same as content description, saving html tag in text
            author_description = page_content.find('div', {'class': 'authorintrofield panelCon'})
            if author_description is not None:
                author_description = str(author_description.find('span'))
            data['author_description'] = author_description

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
                data['reader_comments'] = None

            data['scrap_date'] = datetime.today().strftime('%Y-%m-%d')
            product_info.append(data)
        except:
            print('{} at product {} is failed, go check'.format(subcate_id, product_id))
            not_found_list.append({'subcate_id': subcate_id, 'product_id': product_id, 'track_date': TODAY})
        i += 1
    if len(not_found_list) > 0:
        mongo_insert(product_error, not_found_list)
    return product_info

if __name__=='__main__':
    # Step 1: Get all subcategory id and scrape, with batch insertion at subcategory level #
    # create_category_list()


    # Step 2. Scrap daily to get the price and looking for new items record error into [error_catalog]
    for i in range(2):
        category_query = {'subcate_code': {'$regex': 'book'}}
        list_to_scrape = scan_category_for_scraping(catalog_tem_today, 'subcate_id', category_list, category_query, 'subcate_code')
        multi_scrapers(30, list_to_scrape, CATALOG_URL, 'subcate_code', catalog_tem_today, get_product_list, mongo_insert)
    unfinished_list = scan_category_for_scraping(catalog_tem_today, 'subcate_id', category_list, category_query, 'subcate_code')
    unfinished_category_list = create_new_field(unfinished_list, error_date=TODAY)
    mongo_insert(category_error, unfinished_category_list)


    # Step 3. The raw catalog contains duplicate products; remove them from [catalog_tem_today] 
    #         and copy cleaned catalog to [catalog_today] then delete [catalog_tem_today]
    copy_to_collection(catalog_tem_today, catalog_today, 'kingstone_pid')
    db.drop_collection(catalog_tem_today)

    # Step 4. Mutually compare[catalog_today] with [catalog_yesterday], 
    #         phase out product in [phase_out_product_catalog]
    #         new product in [unfound_product_catalog]
    daily_change_tracker(catalog_today, catalog_yesterday, 'kingstone_pid', new_prodcut_catalog, unfound_product_catalog)


    # Step 5: Reading catalog and scraped single product info 
    product_catalog = new_prodcut_catalog.find({'track_date': TODAY})
    product_list = convert_mongo_object_to_list(product_catalog)
    multi_scrapers(
        worker_num = 20, 
        list_to_scrape = product_list, 
        url_to_scrape = PRODUCT_PAGE, 
        target_id_key = 'kingstone_pid', 
        db_to_insert = product_info, 
        scraper_func = get_product_info, 
        insert_func = mongo_insert,
        slicing=True
    )
