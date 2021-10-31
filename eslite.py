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


def create_category_list(url):
    """ Get all category/subcate id """
    data = requests.get(url, headers= {'user-agent': USER_AGENT }).json()
    cate_list = []
    # Get Chinese / Foreign / Children Section
    for cate in data:
        if cate['id'] in [3, 171, 301]:
            cate_list.append(cate)

    # Create list for Category / Subcategory Level
    nomenclature = []
    for section in cate_list:
        nomenclature.append({'id': section['id'], 
                            'depth': section['depth'], 
                            'description': section['description'],
                            'path': section['path']
                            })
        for cate in section['children']:
            if cate['id'] not in CATE_EXCLUSDE:
                nomenclature.append({'id': cate['id'], 
                                    'depth': cate['depth'], 
                                    'description': cate['description'],
                                    'path': cate['path']
                                    })
                for subcate in cate['children']:
                    if '新書' not in subcate['description']:
                        nomenclature.append({'id': subcate['id'], 
                                            'depth': subcate['depth'], 
                                            'description': subcate['description'],
                                            'path': subcate['path']
                                            })
    mongo_insert(category_list, nomenclature)

def get_product_list(url, category_id):
    paging = 0
    pause_count = 0
    catalog = []
    while True:
        print('============== start', category_id, 'with paging:', paging, '==============')
        if pause_count % 10 == 0:
            time.sleep(3)
        pause_count += 1
        try:
            data = requests.get(url.format(paging, category_id), headers= {'user-agent': USER_AGENT }).json()
        except:
            print('category {} fetching data at paging {} has error, try again in 10 seconds'.format(category_id, paging))
            time.sleep(10)
            data = requests.get(url.format(paging, category_id), headers= {'user-agent': USER_AGENT }).json()

        if len(data['hits']['hit']) == 0:
            print('category {} at page {} has no more'.format(category_id, paging))
            break
        product_list = data['hits']['hit']
        for each in product_list:
            field = each['fields']
            catalog.append({
                'category_id': category_id,
                'eslite_pid': each['id'],
                'discount_type': field['discount_type'], 
                'categories': field['categories'], 
                'create_date': field['create_date'], 
                'name': field['name'], 
                'description': field['description'], 
                'final_price': field['final_price'], 
                'mprice': field['mprice'], 
                'product_url': field['url'], 
                'product_photo_url': 'https://s.eslite.dev' + field['product_photo_url'], 
                'subtitle': field['subtitle'], 
                'restricted': field['restricted'], 
                'stock': field['stock'], 
                'discount': field['discount'], 
                'hotcakes': field['hotcakes'], 
                'eslite_sn': field['eslite_sn'], 
                'isbn': field['isbn'], 
                'isbn10': field['isbn10'], 
                'ean': field['ean'], 
                'original_name': field['original_name'], 
                'sub_title': field['sub_title'], 
                'origin_subtitle': field['origin_subtitle'], 
                'key_word': field['key_word'], 
                'author': field['author'][0], 
                'manufacturer': field['manufacturer'][0], 
                'discount_range': field['discount_range'], 
                'publish_date': field['manufacturer_date'], 
                'is_book': field['is_book'],
                'category_ttl': int(data['hits']['found'])
            })
        paging += 1
    return catalog








if __name__ == '__main__':

    # Step 1: Build up category list if not exists for later scrapping, it's one time set up
    if not category_list.find_one():
        create_category_list(CETEGORY_URL)

    # Step 2. Scrap daily to get the price and looking for new items record error into [error_catalog]
    for i in range(2):
        category_query = [{"$match": {"$and" : [{'path': {'$regex': '中文出版'}},{"depth":3}]}}, 
                        {"$project": {'id':1, 'depth':1, 'path': 1}}]
        list_to_scrape = scan_category_for_scraping(catalog_tem_today, 'category_id', category_list, category_query, 'id')
        multi_scrapers(
            worker_num = 5, 
            list_to_scrape = list_to_scrape, 
            url_to_scrape = CATALOG_URL, 
            target_id_key = 'id', 
            db_to_insert = catalog_tem_today, 
            scraper_func = get_product_list, 
            insert_func = mongo_insert
        )
    unfinished_list = scan_category_for_scraping(catalog_tem_today, 'category_id', category_list, category_query, 'id')
    if len(unfinished_list) > 0:
        unfinished_category_list = create_new_field(unfinished_list, error_date=TODAY)
        mongo_insert(category_error, unfinished_category_list)


    # Step 3. The raw catalog contains duplicate products; remove them from [catalog_tem_today] 
    #         and copy cleaned catalog to [catalog_today] then delete [catalog_tem_today]
    copy_to_collection(catalog_tem_today, catalog_today, 'eslite_pid')
    db.drop_collection(catalog_tem_today)


    # Step 4. Mutually compare[catalog_today] with [catalog_yesterday], 
    #         phase out product in [phase_out_product_catalog]
    #         new product in [new_prodcut_catalog]
    daily_change_tracker(catalog_today, catalog_yesterday, 'eslite_pid', new_product_catalog, unfound_product_catalog)
 
  