import re
import pymysql
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from server.models.user_model import *
from server.models.product_model import *
from category_glossary import *

client = MongoClient('localhost', 27017)
m_db = client.Bookstores
ks_category_list = m_db.kingstone





connection = pymysql.connect(
    host = os.getenv('host'),
    user = os.getenv('user'),
    passwd = os.getenv('passwd'),
    database = os.getenv('database'),
    port = int(os.getenv('port')),
    cursorclass = pymysql.cursors.DictCursor,
    autocommit=True
)
cursor = connection.cursor()




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


    email = db.Column(db.String(255)) 
    password = db.Column(db.String(255)) 
    username = db.Column(db.String(255))
    source = db.Column(db.String(255)) 
    token = db.Column(db.String(255))






if __name__ == '__main__':
    if False:
        register_status()
        create_platform()
        register_price_type()
        create_category_list(ks_category_list)
    register_kingstone_commenter()