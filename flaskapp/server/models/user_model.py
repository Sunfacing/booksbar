from server import db
from sqlalchemy import ForeignKey
from server.models.product_model import *


class UserInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    email = db.Column(db.String(255)) 
    password = db.Column(db.String(255)) 
    username = db.Column(db.String(255))
    source = db.Column(db.String(255)) 
    token = db.Column(db.Text)


class UserFavorite(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    user_id = db.Column(db.Integer, ForeignKey('user_info.id'))
    track_type = db.Column(db.Integer, ForeignKey('track_type.id'))
    type_id = db.Column(db.Integer) 


class TrackType(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    track_type = db.Column(db.String(255)) 



class UserComment(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    user_id = db.Column(db.Integer, ForeignKey('user_info.id')) 
    date = db.Column(db.DateTime)
    isbn = db.Column(db.Integer)
    platform = db.Column(db.Integer, ForeignKey('platform.id'))
    comment = db.Column(db.Text)



