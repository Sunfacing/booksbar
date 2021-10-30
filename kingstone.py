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