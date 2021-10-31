import os
from dotenv import load_dotenv
load_dotenv()


class Config(object):
    UPLOAD_FOLDER = 'server\\static\\uploads'
    JWT_SECRET_KEY = os.getenv('jwt_secret_key')
    RESTFUL_JSON = {"ensure_ascii": False}
    JSON_AS_ASCII = False

    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{os.getenv('user')}:{os.getenv('passwd')}@{os.getenv('host')}:3306/{os.getenv('database')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DB_HOST = os.getenv('host')
    DB_USERNAME = os.getenv('user')
    DB_PASSWORD = os.getenv('passwd')
    DB_DATABASE = os.getenv('database')