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
    page  = requests.get(url, headers = HEADERS) 
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




if __name__=='__main__':
    
    # Step 1: Build up category list if not exists for later scrapping, it's one time set up
    if not category_list.find_one():
        get_category_list(SECTION_URL)