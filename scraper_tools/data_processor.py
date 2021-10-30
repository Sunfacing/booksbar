from collections import defaultdict


def mongo_insert(collection, product_list):
    """
    :param collection: collection to be insert
    :param list: must be a list of dicts, best created by [convert_new_collection] function
    """
    collection.insert_many(product_list)
    name = str(collection)
    print(name, 'data created')


def scan_category_for_scraping(catalog, key, category_list, category_query, key_for_hash):
    """
    Compare two collections: [category_list] and [catalog], to determine which category aren't scraped,
    this function can track progress in case any incident halting scraping, and continue from last status
    :param catalog: product catalog scraped each day, namely [catalog_tem_today]
    :param catalog_query: grouping query for faster check
    :param category_list: category list containing every available cateogries
    :param category_query: filtering query for selecting specific category
    :param key_for_hash: key for category_list to check if in catelog
    """
    key_list = catalog.distinct(key)
    try: 
        cate_list = category_list.find(category_query)
    except: 
        cate_list = category_list.aggregate(category_query)
    unfinished_list = []
    for cate in cate_list:
        try:
            if cate[key_for_hash] not in key_list: 
                unfinished_list.append(cate)
        except:
            pass
    return unfinished_list


def create_new_field(product_list, **field_value):
    """
    Create new field or overwrite current field of each product with the same value
    support multiple field input, and return product list able to be inserted into collection
    :param product_list: the product list to add new field
    :param **field_value: provide field=value will create the field(or overwrite) with the value
    """
    new_list = []
    for product in product_list:
        try: product.pop('_id')
        except: pass   
        for field, value in field_value.items():
            product[field] = value
        new_list.append(product)
    return new_list



def convert_hashtable(collection, key_for_hash, query={}):
    """
    Create hashtable for finding duplicate products / comparing catalog and product info
    :param collection: a list of hashtable created by [covert_hashtable] 
    :param key_for_hash: if turned true, each document in collection will add 'scrape
    """
    collection = collection.find(query)
    hash_table = defaultdict(dict)

    for product in collection:
        product_value_as_key = product[key_for_hash]
        product.pop('_id')
        hash_table[product_value_as_key] = product
    return hash_table    


def convert_new_collection(converted_hashtable, add_scrape_date=False, scrape_date=TODAY):
    """
    Create list type of new collection via hashtable, the result is duplicate free
    :param converted_hashtable: a list of hashtable created by [covert_hashtable] 
    :param add_scrape_date: if turned true, each document in collection will add 'scrape_date' field
    :param scrape_date: if [add_scrape_date] is True, date must be provided
    """ 
    new_collection = []
    for doc in converted_hashtable.values():
        if add_scrape_date:
            doc['scrape_date'] = scrape_date
        new_collection.append(doc)
    return new_collection

def copy_to_collection(copied_from_db, copy_to_db, key_for_hash, add_scrape_date=False, scrape_date=TODAY):
    """
    Used when need to remove duplicate products, and store the collection
    this function combines functions of [convert_hashtable], [convert_new_collection], [mongo_insert]
    :param copied_from_db: collection to be insert
    :param copy_to_db: must be a list of dicts, best created by [convert_new_collection] function    
    """
    hashtable = convert_hashtable(copied_from_db, key_for_hash)
    collection_list = convert_new_collection(hashtable, add_scrape_date, scrape_date)
    mongo_insert(copy_to_db, collection_list)
    print(len(collection_list), 'is copied') 


def find_unmatched_product(big_collection, small_collection, key_for_hash):
    """
    Find the products found in bigger_collection, but not in smaller_collection and return list
    :param big_collection: used to find products not in small_collection
    :param small_collection: used to find products not in small_collection
    :param key_for_hash: key that should exist in both collections for comparison
    """
    small_collection = convert_hashtable(small_collection, key_for_hash)
    unmatched_list = []
    for doc in big_collection.find():
        if doc[key_for_hash] not in small_collection:
            doc.pop('_id')
            unmatched_list.append(doc)
    return unmatched_list


def daily_change_tracker(catalog_today, catalog_yesterday, key_for_hash, new_prodcut_catalog, unfound_product_catalog):
    """
    Track if there's any product found yesterday but not today
    It's possible the product is missed today, and tomorrow shows up again
    for tracking long term scrapping process's quality
    """
    # Find out new product compared to yesterday
    new_product = find_unmatched_product(catalog_today, catalog_yesterday, key_for_hash)
    product_list = create_new_field(new_product, track_date=TODAY, type='new_product')
    mongo_insert(new_prodcut_catalog, product_list)

    # Find out phased out product compared to today
    phased_out_product = find_unmatched_product(catalog_yesterday, catalog_today, key_for_hash)
    product_list = create_new_field(phased_out_product, track_date=TODAY, type='phase_out')
    mongo_insert(unfound_product_catalog, product_list)


def convert_mongo_object_to_list(mongo_object):
    """
    Remove mongo object's _id key, and append to a new list
    :param mongo_object: mongo object from collection.find() method
    """
    product_list = []
    for product in mongo_object:
        product.pop('_id')
        product_list.append(product)
    return product_list