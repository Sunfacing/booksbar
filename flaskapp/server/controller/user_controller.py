import pymysql
import os
import datetime
import plotly.express as px
import plotly
import json
from flask import Flask, render_template, request, redirect, send_from_directory, jsonify, abort, current_app
from flask.helpers import url_for
from flask_bcrypt  import Bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from dotenv import load_dotenv
from werkzeug.utils import secure_filename

import redis
import logging
from server import app, bcrypt

from server import db
import boto3

from server.models.user_model import *

# import server.models.user_model

client = boto3.client('s3', region_name='us-east-2')
limiter = Limiter(app, key_func=get_remote_address)

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

r= redis.Redis.from_url('redis://flaskproject.gtlinm.0001.use2.cache.amazonaws.com:6379')


ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'jfif'])
EXPIRE = 3600
TODAY = datetime.datetime.today().strftime('%Y-%m-%d')
BUCKET = 'stylishproject'



@app.route('/')
@limiter.limit("5/minute", error_message='chill!')
def index(category=None):
    db.create_all()
    return 'hi'

