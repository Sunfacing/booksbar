from server import db
from sqlalchemy import ForeignKey



class CategoryList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.String(30))
    section = db.Column(db.String(30))
    category_id = db.Column(db.String(30))
    category = db.Column(db.String(30))
    subcategory_id = db.Column(db.String(30))
    subcategory = db.Column(db.String(30))

class EsliteToKingsCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer)
    category = db.Column(db.String(30))
    kingstone_id = db.Column(db.Integer, ForeignKey('category_list.id'), nullable=False) 

class MomoToKingsCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subcategory_id = db.Column(db.Integer)
    subcategory = db.Column(db.String(30))
    kingstone_id = db.Column(db.Integer, ForeignKey('category_list.id'), nullable=False) 

class Platform(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    platform = db.Column(db.String(30), primary_key=True)

class BookInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    isbn = db.Column(db.String(30), nullable=False)
    show_priority = db.Column(db.Integer, nullable=False)
    platform = db.Column(db.Integer, ForeignKey('platform.id'), nullable=False)
    platform_product_id = db.Column(db.Integer, nullable=False)
    create_date = db.Column(db.DateTime, nullable=False)
    category_id = db.Column(db.Integer, ForeignKey('category_list.id'), nullable=False) 
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.Integer, ForeignKey('author.id'))
    publisher = db.Column(db.Integer, ForeignKey('publisher.id'))
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
    name = db.Column(db.String(100))
    platform = db.Column(db.Integer, ForeignKey('platform.id'))


class Publisher(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(100))
    platform = db.Column(db.Integer, ForeignKey('platform.id'))


class Picture(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    isbn_id = db.Column(db.Integer, ForeignKey('book_info.id')) 
    platform = db.Column(db.Integer, ForeignKey('platform.id'))
    pic_type = db.Column(db.String(30))
    url = db.Column(db.String(30))


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
