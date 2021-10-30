def mongo_insert(collection, product_list):
    """
    :param collection: collection to be insert
    :param list: must be a list of dicts, best created by [convert_new_collection] function
    """
    collection.insert_many(product_list)
    name = str(collection)
    print(name, 'data created')