import os
import datetime
from dotenv import load_dotenv

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:  # 基本配置
    SECRET_KEY = 'THIS IS MAX'
    PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=14)
    DB_HOST = os.getenv('host')
    DB_USERNAME = os.getenv('user')
    DB_PASSWORD = os.getenv('passwd')


class DevelopmentConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{os.getenv('user')}:{os.getenv('passwd')}@{os.getenv('host')}:3306/{os.getenv('database')}?charset=utf8mb4"
    DB_DATABASE = os.getenv('database')


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{os.getenv('user')}:{os.getenv('passwd')}@{os.getenv('host')}:3306/{os.getenv('test_database')}?charset=utf8mb4"
    DB_DATABASE = os.getenv('test_database')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
}
