import pymysql
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from server.models.product_model import *

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

client = MongoClient('localhost', 27017)
m_db = client.Bookstores
ks_category_list = m_db.kingstone
ks_product_info = m_db.kingstone_product_info











def get_products():
    products = Nomenclature.query.filter()
    return [p.to_json() for p in products]



if __name__ == '__main__':

    ks_category_list = ks_category_list.find()
    for i in ks_category_list:
        print(i)

    # db.session.add_all()
    # db.session.commit()