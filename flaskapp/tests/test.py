import unittest
import sys
import os
import datetime
import pytz
from dotenv import load_dotenv
from flask_testing import TestCase
from server import create_app, db
from server.models.product_model import CategoryList, Platform
from sql_writer import register_isbn, register_author, register_publisher, register_kingstone_from_catalog
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
TODAY = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y-%m-%d")

unittest.TestLoader.sortTestMethodsUsing = None


class SettingBase(TestCase):
    def create_app(self):
        return create_app("testing")


class ScrapProductDetail(SettingBase):
    def test_1_create_db(self):
        db.drop_all()
        product_1 = {'subcate_id': '/book/job',
                     'kingstone_pid': '2018562671802',
                     'title': '我被滑雪場錄取了：畫說日本打工度假日常',
                     'author': 'author1',
                     'publisher': 'publisher1'}
        product_2 = {'subcate_id': '/book/ccd',
                     'kingstone_pid': '2011771371532',
                     'title': '用寬容的心情，處理惱人的事情',
                     'author': 'author2',
                     'publisher': 'publisher2'
                     }
        TEST_COLLECTION.insert_many([product_1, product_2])

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


class ToSQLISBN(SettingBase):
    def test_4_create_db(self):
        db.create_all()
        cate_1 = CategoryList(subcategory_id='/book/job')
        cate_2 = CategoryList(subcategory_id='/book/ccd')
        platform = Platform(id=1, platform='kingstone')
        db.session.add_all([cate_1, cate_2, platform])
        db.session.commit()

    def test_5_create_isbn(self):
        register_isbn(PRODUCT_INFO, date=TODAY)

    def test_6_check_result(self):
        product_list = db.session.execute("SELECT * FROM isbn_catalog")
        final_list = []
        for product in product_list:
            final_list.append(product)
        self.assertEqual(final_list[0]['isbn'], '9786263210493')
        self.assertEqual(final_list[1]['isbn'], '9789863897996')


class TryCreateBookInfo(SettingBase):
    def test_7_create_db(self):
        register_author(TEST_COLLECTION)
        register_publisher(TEST_COLLECTION)
        register_kingstone_from_catalog(TEST_COLLECTION, PRODUCT_INFO)

    def test_8_check_result(self):
        product_list = db.session.execute("SELECT * FROM book_info")
        final_list = []
        for product in product_list:
            final_list.append(product)
        self.assertEqual(len(final_list[0]['description']), 691)
        self.assertEqual(len(final_list[1]['description']), 1101)

    def test_9_drop_data(self):
        TEST_COLLECTION.drop()
        PRODUCT_INFO.drop()
        db.drop_all()


if __name__ == '__main__':
    unittest.main()