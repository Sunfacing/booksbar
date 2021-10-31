from server import db
from sqlalchemy import ForeignKey



class Nomenclature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    division_id = db.Integer
    division = db.Column(db.String(30))
    section_id = db.Integer
    section = db.Column(db.String(30))
    category_id = db.Integer
    category = db.Column(db.String(30))
    subcategory_id = db.Integer
    subcategory = db.Column(db.String(30))

class Platform(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    platform = db.Column(db.String(30), primary_key=True)

class BookInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    isbn = db.Column(db.Integer, nullable=False) 
    platform = db.Column(db.Integer, ForeignKey('platform.id'), nullable=False)
    create_date = db.Column(db.DateTime, nullable=False)
    Nomenclature_id = db.Column(db.Integer, ForeignKey('nomenclature.id'), nullable=False) 
    title = db.Column(db.String(30), nullable=False)
    author = db.Column(db.Integer, ForeignKey('publisher.id'))
    publisher = db.Column(db.Integer, ForeignKey('author.id'))
    size = db.Column(db.String(30))
    publish_date = db.Column(db.DateTime)
    table_of_content = db.Column(db.Text)
    description = db.Column(db.Text)
    author_intro = db.Column(db.Text)
    cover_photo = db.Column(db.String(255))
    page = db.Column(db.Integer)
    product_url = db.Column(db.String(255))
    e_book_url = db.Column(db.String(255))

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(30))
    platform = db.Column(db.Integer, ForeignKey('platform.id'))


class Publisher(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(30))
    platform = db.Column(db.Integer, ForeignKey('platform.id'))


class Picture(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    isbn_id = db.Column(db.Integer, ForeignKey('nomenclature.id')) 
    platform = db.Column(db.Integer, ForeignKey('platform.id'))
    pic_type = db.Column(db.String(30))
    url = db.Column(db.String(30))


# class HotItemRecom(db.Model):
#     id = db.Column(db.Integer, primary_key=True) 
#     level = db.Column(db.String(30)) 
#     ks_pid = db.Column(db.Integer, ForeignKey('ks_book_info.id'))
#     es_pid = db.Column(db.Integer, ForeignKey('es_book_info.id'))


# class NewItemRecom(db.Model):
#     id = db.Column(db.Integer, primary_key=True) 
#     level = db.Column(db.String(30)) 
#     ks_pid = db.Column(db.Integer, ForeignKey('ks_book_info.id'))
#     es_pid = db.Column(db.Integer, ForeignKey('es_book_info.id'))



class PriceStatusInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    book_id = db.Column(db.Integer, ForeignKey('book_info.id')) 
    price_type = db.Column(db.Integer, ForeignKey('price_type.id')) 
    status = db.Column(db.Integer, ForeignKey('status.id'))
    price = db.Column(db.Integer)
    survey_date = db.Column(db.Date)

class PriceType(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    price_type = db.Column(db.String(30))     

class Status(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    status = db.Column(db.String(30))   

class UserInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    email = db.Column(db.String(255)) 
    password = db.Column(db.String(255)) 
    username = db.Column(db.String(255))
    source = db.Column(db.String(255)) 
    token = db.Column(db.String(255))


class UserFavorite(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    user_id = db.Column(db.Integer, ForeignKey('user_info.id')) 
    isbn = db.Column(db.Integer) 


class UserComment(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    user_id = db.Column(db.Integer, ForeignKey('user_info.id')) 
    date = db.Column(db.DateTime)
    isbn = db.Column(db.Integer)
    platform = db.Column(db.Integer, ForeignKey('platform.id'))
    comment = db.Column(db.String(255))


class DailyNewCount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime)
    platform = db.Column(db.Integer, ForeignKey('platform.id'))
    total = db.Column(db.Integer)
    new = db.Column(db.Integer)
    remove = db.Column(db.Integer)
    time = db.Column(db.Integer)


class DailyCatalogChange(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    date = db.Column(db.DateTime)
    platform = db.Column(db.Integer, ForeignKey('platform.id'))
    book_id = db.Column(db.Integer, ForeignKey('book_info.id'))
    reason = db.Column(db.Integer)

class DailyScrapeTime(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    date = db.Column(db.DateTime)
    platform = db.Column(db.Integer, ForeignKey('platform.id'))
    step = db.Column(db.String(30))
    time = db.Column(db.Time)
