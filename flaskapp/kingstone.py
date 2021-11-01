import pymysql
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from server.models.user_model import *

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
db = client.Bookstores


def get_products():
    products = Nomenclature.query.filter()
    return [p.to_json() for p in products]


x = get_products()
print(x)