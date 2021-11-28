import re
import pymysql
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from server import db
from server.models.user_model import *
from server.models.product_model import *
from category_glossary import *


client = MongoClient('localhost', 27017)
m_db = client.Bookstores
ks_category_list = m_db.kingstone


def create_platform():
    kingstone = Platform(id=1, platform='kingstone')
    eslite = Platform(id=2, platform='eslite')
    momo = Platform(id=3, platform='momo')
    books = Platform(id=4, platform='books')
    native = Platform(id=5, platform='native')
    platforms = [kingstone, eslite, momo, books, native]
    db.session.add_all(platforms)
    db.session.commit()


def create_category_list(collection):
    ks_category_list = collection.find()
    cate_list = []
    for each in ks_category_list:
        section_id = each['section_code']
        section_nm = each['section_nm']
        if 'book' in section_id and section_nm not in ['生活風格', '漫畫', '考試書／政府出版品', '輕小說', '羅曼史', '宗教命理']:
            category = CategoryList(section_id=section_id,
                                    section=each['section_nm'],
                                    category_id=each['category_code'],
                                    category=each['category_nm'],
                                    subcategory_id=each['subcate_code'],
                                    subcategory=each['subcate_nm'])
            cate_list.append(category)
    db.session.add_all(cate_list)
    db.session.commit()


def register_price_type():
    original = PriceType(id=1, price_type='original')
    promotional = PriceType(id=2, price_type='promotional')
    types = [original, promotional]
    db.session.add_all(types)
    db.session.commit()


def register_status():
    in_stock = Status(id=1, status='in_stock')
    out_of_stock = Status(id=2, status='out_of_stock')
    types = [in_stock, out_of_stock]
    db.session.add_all(types)
    db.session.commit()




def register_kingstone_commenter():
    kingstone_user = UserInfo(username='kingstone_user')
    db.session.add(kingstone_user)
    db.session.commit()




def register_track_type():
    type_1 = TrackType(track_type='subcategory')
    type_2 = TrackType(track_type='product')
    type_3 = TrackType(track_type='author')
    type_4 = TrackType(track_type='browsing')
    db.session.add_all([type_1, type_2, type_3, type_4])
    db.session.commit()


def register_pipeline_step():
    step_1 = PipelineStep(step='scrape_raw')
    step_2 = PipelineStep(step='remove_duplicate')
    step_3 = PipelineStep(step='detect_unfound')
    step_4 = PipelineStep(step='scrape_new_item')
    step_5 = PipelineStep(step='create_catalog')
    step_6 = PipelineStep(step='register_new_author')
    step_7 = PipelineStep(step='register_new_publisher')
    step_8 = PipelineStep(step='register_new_book')
    step_9 = PipelineStep(step='update_price')
    db.session.add_all([step_1, step_2, step_3, step_4, step_5, step_6, step_7, step_8, step_9])
    db.session.commit()



if __name__ == '__main__':
    if True:
        register_status()
        create_platform()
        register_price_type()
        create_category_list(ks_category_list)
        register_kingstone_commenter()
        register_track_type()
        register_pipeline_step()