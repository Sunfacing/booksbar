from collections import defaultdict
from enum import Enum

from server import db

class Platform(Enum):
    KINGSTONE = 1
    ESLITE = 2
    MOMO = 3


class TrackType(Enum):
    FAVORITE_CATEGORY = '1'
    FAVORITE_BOOK = '2'
    FAVORITE_AUTHOR = '3'
    ACTIVITY_HISTORY = '4'


def create_booslist_by_category(*returned_booklists):
    """
    Used in search page under introduction section, called by [introduction_checker]
    :param returned_booklists: information title -> table_of_contents, description, author_intro
    """
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



def introduction_checker(info, error_message):
    """
    Used in product page under introduction section, called by [introduction_checker]
    :param info: information title -> table_of_contents, description, author_intro
    :param error_message: message return if information is empty
    """
    if info == 'None' or not info:
        return error_message
    return info


def create_data(data):
    """
    Reduce repetitive db.session.add and db.session.commit
    :param data: data to add
    """
    db.session.add(data)
    db.session.commit()



def show_paging(page, book_counts, books_per_page):
    """
    Takes current book total counts and calculate if there's next paging
    :param page: the current page passed from html
    :param book_counts: total number of books in database now
    :param books_per_page: number of books rendered in html
    """
    ttl_pages = 0
    shown_pages = defaultdict(dict)

    # Calculate how many pages available based on current number of books rendered each page
    for book in book_counts:
        ttl_pages = (book[0] / books_per_page)
    # If user is at the first page, return -1 for html to turn off link, otherwise the previous page
    if int(page) - 1 == 0:
        shown_pages['pre'] = -1
    else:
        shown_pages['pre'] = int(page) - 1
    # If user is at the last page, return -1 for html to turn off link, otherwise the previous page
    if ttl_pages - int(page) < 0 :
        shown_pages['next'] = -1
    else:
        shown_pages['next'] = int(page) + 1
    
    shown_pages['current'] = page
    return shown_pages