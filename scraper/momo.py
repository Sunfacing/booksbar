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

def get_product_list(url, subcate_code):
    i = 1
    product_list = []
    while True:
        try:
            catalog_url = url.format(subcate_code, i)
            try:
                page  = requests.get(catalog_url, headers = HEADERS)
            except:
                print('something went wrong with {} at page {}, try again in 10 seconds'.format(subcate_code, i))
                time.sleep(10)
                page  = requests.get(catalog_url, headers = HEADERS)                
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
            print('something wrong with', subcate_code , e)
        i += 1
    return product_list



if __name__=='__main__':
    
    # Step 1: Build up category list if not exists for later scrapping, it's one time set up
    if not category_list.find_one():
        get_category_list(SECTION_URL)

    # Step 2. Scrap daily to get the price and looking for new items record error into [error_catalog] 
    for i in range(2):
        list_to_scrape = scan_category_for_scraping(catalog_tem_today, 'subcate_code', category_list, {}, 'subcate_code')
        multi_scrapers(
            worker_num = 2, 
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


    # Step 3. The raw catalog contains duplicate products; remove them from [catalog_tem_today] 
    #         and copy cleaned catalog to [catalog_today] then delete [catalog_tem_today]
    copy_to_collection(catalog_tem_today, catalog_today, 'momo_pid')
    db.drop_collection(catalog_tem_today)


    # Step 4. Mutually compare[catalog_today] with [catalog_yesterday], 
    #         phase out product in [phase_out_product_catalog]
    #         new product in [new_prodcut_catalog]
    daily_change_tracker(catalog_today, catalog_yesterday, 'momo_pid', new_prodcut_catalog, unfound_product_catalog)

