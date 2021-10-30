from pymongo import MongoClient
from collections import defaultdict
from datetime import date
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

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
