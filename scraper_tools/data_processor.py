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