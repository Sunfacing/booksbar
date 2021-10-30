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