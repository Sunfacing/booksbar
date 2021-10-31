import time
import requests

from pymongo import MongoClient
from collections import defaultdict
from datetime import date
from fake_useragent import UserAgent
from scraper_tools.data_processor import *
from scraper_tools.scrapers import multi_scrapers


SEC_LIST = [3, 171, 301] # Each Represent 中文書, 外文書, 童書
CATE_EXCLUSDE = [559, 963, 966, 1076, 956, 979, 1088, 1073, 1075, 3823, 1582, 3829, 1211, 1212, 2370, 3938] # These are for campaign use, and will cause duplicate products
CETEGORY_URL = 'https://athena.eslite.com/api/v1/categories' # Api that returns all categories
MAIN_CAMPAIGN_URL = 'https://athena.eslite.com/api/v1/headers'
MAIN_RECO_ITEM_URL = 'https://athena.eslite.com/api/v1/banners/L1Page/{}/big_b,recommend_new_products,editor_recommend'
CATALOG_URL = 'https://athena.eslite.com/api/v2/search?final_price=0,&sort=manufacturer_date+desc&size=1000&start={}&categories=[{}]' # Main api to get product price, use with paging, category id
PRODUCT_PAGE = 'https://athena.eslite.com/api/v1/products/' # Single product page prefix url, must add item code at the end
USER_AGENT = UserAgent().random
TODAY = date.today().strftime("%Y-%m-%d")
TODAY_FOR_COLLECTION_NAME = date.today().strftime("%m%d")
DATE_FOR_DELETE_COLLECTION_NAME = str(int(TODAY_FOR_COLLECTION_NAME) - 7)
YESTERDAY_FOR_EORROR_CHECKER = str(int(TODAY_FOR_COLLECTION_NAME) - 1)


client = MongoClient('localhost', 27017)
db = client.Bookstores
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