from pymongo import MongoClient
from collections import defaultdict
from datetime import date
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from scraper_tools.data_processor import *
from scraper_tools.scrapers import multi_scrapers
import requests
import time

TODAY = date.today().strftime("%Y-%m-%d")
TODAY_FOR_COLLECTION_NAME = date.today().strftime("%m%d")
DATE_FOR_DELETE_COLLECTION_NAME = str(int(TODAY_FOR_COLLECTION_NAME) - 7)
YESTERDAY_FOR_EORROR_CHECKER = str(int(TODAY_FOR_COLLECTION_NAME) - 1)


client = MongoClient('localhost', 27017)
db = client.Bookstores

# Set collection name with variable for auto addition / validation / deletion
catalog_today = db['momo_catalog_' + TODAY_FOR_COLLECTION_NAME]
catalog_yesterday = db['momo_catalog_' + YESTERDAY_FOR_EORROR_CHECKER]
catalog_last_7_days = db['momo_catalog_' + DATE_FOR_DELETE_COLLECTION_NAME]

category_list = db.momo_nomenclature  # Category List
catalog_tem_today = db.momo_catalog_tem_today
# category_list = db.momo  # Category List
category_error = db.momo_category_error
product_info = db.momo_product_info
product_error = db.momo_product_error
new_prodcut_catalog = db.momo_new_product_catalog
phase_out_product_catalog = db.momo_phase_out_catalog
unfound_product_catalog = db.momo_unfound_product_catalog


SECTION_URL = 'https://m.momoshop.com.tw/category.momo?cn=4000000000&cid=dir&oid=dir&imgSH=fourCardType'
CATALOG_URL = 'https://m.momoshop.com.tw/cateGoods.momo?cn={}&page={}&sortType=5&imgSH=itemizedType'
PRODUCT_URL = 'https://m.momoshop.com.tw//goods.momo?i_code='
HEADERS = {'User-Agent': UserAgent().random,'X-Requested-With': 'XMLHttpRequest'}