from server import db
from sqlalchemy import ForeignKey
from sqlalchemy.schema import UniqueConstraint


class CategoryList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.String(30))
    section = db.Column(db.String(30))
    category_id = db.Column(db.String(30))
    category = db.Column(db.String(30))
    subcategory_id = db.Column(db.String(30))
    subcategory = db.Column(db.String(30))


class Platform(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    platform = db.Column(db.String(30), primary_key=True)


class IsbnCatalog(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True) 
    isbn = db.Column(db.String(30), primary_key=True)
    category_id = db.Column(db.Integer, ForeignKey('category_list.id'), nullable=False)
    platform = db.Column(db.Integer, ForeignKey('platform.id'), nullable=False)
    __table_args__ = (UniqueConstraint('isbn', name='isbn'),)


class BookInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement = True) 
    isbn_id = db.Column(db.Integer, ForeignKey('isbn_catalog.id'), nullable=False)
    platform = db.Column(db.Integer, ForeignKey('platform.id'), nullable=False)
    platform_product_id = db.Column(db.String(255), primary_key=True, nullable=False)
    create_date = db.Column(db.DateTime, nullable=False) 
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
    book_id = db.Column(db.Integer, ForeignKey('book_info.id')) 
    url = db.Column(db.String(255))


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


class DailyScrapeResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime)
    platform = db.Column(db.Integer, ForeignKey('platform.id'))
    total = db.Column(db.Integer)
    new = db.Column(db.Integer)
    phase_out = db.Column(db.Integer)


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



def get_catalog_section(section):
    product_list =db.session.execute("""
        SELECT b.isbn_id,
            b.id AS book_id,
            publish_date,
            title,
            description,
            cover_photo,
            a.name AS author,
            p.name AS publisher
        FROM category_list AS c 
        INNER JOIN isbn_catalog AS i
        ON i.category_id = c.id
        INNER JOIN book_info AS b
        ON b.isbn_id = i.id
        INNER JOIN author AS a
        ON b.author = a.id
        INNER JOIN publisher AS p
        ON b.publisher = p.id
        WHERE b.platform = 1 and c.section = '{}'  
        LIMIT 9""".format(section))
    return product_list


def get_catalog_subcategory(subcategory):
    product_list =db.session.execute("""
        SELECT b.isbn_id,
                b.id AS book_id,
                publish_date,
                title,
                description,
                cover_photo,
                a.name AS author,
                p.name AS publisher
            FROM category_list AS c 
            INNER JOIN isbn_catalog AS i
            ON i.category_id = c.id
            INNER JOIN book_info AS b
            ON b.isbn_id = i.id
            INNER JOIN author AS a
            ON b.author = a.id
            INNER JOIN publisher AS p
            ON b.publisher = p.id
            WHERE b.platform = 1 and c.subcategory = '{}'  
            ORDER BY publish_date DESC 
            LIMIT 40""".format(subcategory))
    return product_list




def get_book_info(isbn_id, date):
    info_list = db.session.execute("""
        SELECT title, a.name AS author, u.name AS publisher, publish_date, 
        isbn_id, i.isbn AS ISBN, b.platform, size, page, p.status, p.price, product_url, cover_photo
    FROM book_info AS b
    INNER JOIN isbn_catalog AS i
    ON i.id = b.isbn_id
    LEFT JOIN price_status_info AS p
    ON b.id = p.book_id 
    INNER JOIN author AS a
    ON a.id = b.author
    INNER JOIN publisher AS u
    ON u.id = b.publisher
    WHERE isbn_id = {} AND survey_date='{}'""".format(isbn_id, date))
    return info_list



def get_book_pics(isbn_id):
    pic_list = db.session.execute("""
    SELECT b.cover_photo, p.url AS pics FROM book_info AS b
    INNER JOIN picture AS p
    ON b.id = p.book_id
    WHERE isbn_id = {} and platform = 1""".format(isbn_id))
    return pic_list



def api_book_info(isbn_id):
    info_list = db.session.execute("""
        SELECT table_of_content, description, author_intro
    FROM book_info AS b
    LEFT JOIN price_status_info AS p
    ON b.id = p.book_id 
    INNER JOIN author AS a
    ON a.id = b.author
    WHERE isbn_id = {} and b.platform = 1""".format(isbn_id))
    return info_list