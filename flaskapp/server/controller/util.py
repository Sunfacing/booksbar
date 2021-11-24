from collections import defaultdict

from enum import Enum


class Platform(Enum):
    KINGSTONE = 1
    ESLITE = 2
    MOMO = 3


class TrackType(Enum):
    ACTIVITY_HISTORY = '0'
    FAVORITE_CATEGORY = '1'
    FAVORITE_BOOK = '2'
    FAVORITE_AUTHOR = '3'


def create_booslist_by_category(*returned_booklists):
    product_list = defaultdict(dict)
    duplicate_hash = defaultdict(dict)
    count = 0
    for booklist in returned_booklists:
        for book in booklist:
            isbn_id = book['isbn_id']
            categroy = book['category']
            if not duplicate_hash[isbn_id]:
                data = {
                'isbn_id': isbn_id,
                'title': book['title'],
                'cover_photo': book['cover_photo'],
                'author': book['author'],
                'description': book['description'],
                }
                if not product_list[categroy]:
                    product_list[categroy] = [data]
                else:
                    product_list[categroy].append(data)
                duplicate_hash[isbn_id] = 1
                count += 1
    return [product_list, count]