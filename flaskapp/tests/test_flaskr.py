import unittest
import sys
import os
from dotenv import load_dotenv
from flask import url_for
from flask_testing import TestCase
from server import create_app
from pymongo import MongoClient
sys.path.append("..")
from scraper.kingstone import get_product_info, PRODUCT_PAGE
from scraper.scrapers import multi_scrapers
from scraper.data_processor import mongo_insert


load_dotenv()
CLIENT = MongoClient('mongodb://{}:{}@{}/?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&directConnection=true&ssl=false'.format(os.getenv("mon_user"), os.getenv("mon_passwd"), os.getenv("mon_host")))
MONGO_DB = CLIENT.test_bookbar
TEST_COLLECTION = MONGO_DB.test
PRODUCT_INFO = MONGO_DB.product_info


class SettingBase(TestCase):
    def create_app(self):
        return create_app("testing")



# 這邊繼承剛剛的寫的 SettingBase class，接下來會把測試都寫在這裡
class ScrapProductDetail(SettingBase):
    def test_1_create_db(self):
        product_one = {'subcate_id': '/book/jod', 'kingstone_pid': '2018562671802', 'title': '我被滑雪場錄取了：畫說日本打工度假日常'}
        product_two = {'subcate_id': '/book/jod', 'kingstone_pid': '2011771371532', 'title': '用寬容的心情，處理惱人的事情'}
        TEST_COLLECTION.insert_many([product_one, product_two])

    def test_2_scrap_book(self):
        product_list = TEST_COLLECTION.find()
        list_to_scrap = [product for product in product_list]
        multi_scrapers(
            worker_num=1,
            list_to_scrape=list_to_scrap,
            url_to_scrape=PRODUCT_PAGE,
            target_id_key='kingstone_pid',
            db_to_insert=PRODUCT_INFO,
            scraper_func=get_product_info,
            insert_func=mongo_insert,
            slicing=True
        )
        
    def test_3_check_result(self):
        product_one = PRODUCT_INFO.find_one({'title': '我被滑雪場錄取了：畫說日本打工度假日常'})
        product_two = PRODUCT_INFO.find_one({'title': '用寬容的心情，處理惱人的事情'})
        self.assertEqual(len(product_one['description']), 691)
        self.assertEqual(len(product_two['description']), 1101)
        TEST_COLLECTION.drop()
        PRODUCT_INFO.drop()




if __name__ == '__main__':
    unittest.main()