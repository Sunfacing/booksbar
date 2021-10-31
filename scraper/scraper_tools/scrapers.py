import threading
import queue


class Worker(threading.Thread):

    def __init__(self, queue, worker_num, url_to_scrape, target_id_key, db_to_insert, scraper_func, insert_func, slicing=False):
        """
        :param worker_num: defind how many threads to use
        :param url_to_scrape: takes url prefix defined in file as constant
        :param target_id_key: the key for getting category_id(or subcategory_id)
        :param db_to_insert: collection to write into
        :param scraper_func: each worker use this function with [url_to_scrape] and [target_id_key]
        :param insert_func: a function takes result from scraper function and insert to db specified
        """     
        threading.Thread.__init__(self)
        self.queue = queue
        self.worker_num = worker_num
        self.url_to_scrape = url_to_scrape
        self.target_id_key = target_id_key
        self.db_to_insert = db_to_insert
        self.scraper_func = scraper_func
        self.insert_func = insert_func
        self.slicing = slicing

    def run(self):
        while self.queue.qsize() > 0:
            target_id = self.queue.get() 
            if self.slicing:
                self.do_by_slicing_product_list(self.url_to_scrape, target_id, self.target_id_key, self.db_to_insert, self.scraper_func, self.insert_func)
            else:   
                self.do_by_category(target_id, self.url_to_scrape, self.target_id_key, self.db_to_insert, self.scraper_func, self.insert_func)

    def do_by_category(self, target_id, url_to_scrape, target_id_key, db_to_insert, scraper_func, insert_func):
        try:
            catalog = scraper_func(url_to_scrape, target_id[target_id_key])
        except Exception as e:
            print('{} has problem with gathering information: {}'.format(target_id, e))

        try:
            insert_func(db_to_insert, catalog)
        except Exception as e:
            print('{} has problem with inserting data: {}'.format(target_id, e))


    def do_by_slicing_product_list(self, url_to_scrape, sliced_list, target_id_key, db_to_insert, scraper_func, insert_func):
        catalog = scraper_func(url_to_scrape, sliced_list, target_id_key)
        try:
            if len(catalog) > 0:
                insert_func(db_to_insert, catalog)
            print('Worker {} has {} done'.format(self.worker_num, len(catalog)))
        except Exception as e:
            print('Worker {} has problem with inserting data: {}'.format(self.worker_num, e))   


def multi_scrapers(worker_num, list_to_scrape, url_to_scrape, target_id_key, db_to_insert, scraper_func, insert_func, slicing=False):
    if slicing:
        my_queue = queue.Queue()
        share = len(list_to_scrape) // 50
        if share != 0:
            for i in range(share):
                start = i * 50
                end = (i + 1) * 50
                item = list_to_scrape[start: end]    
                my_queue.put(item)
            item = list_to_scrape[end: ]   
        else:
            item = list_to_scrape[share: ]
        my_queue.put(item)
    else:
        my_queue = queue.Queue()
        for item in list_to_scrape:
            my_queue.put(item)

    worker_list = []
    for i in range(worker_num):
        worker_list.append('worker{}'.format(i + 1))

    for i in range(len(worker_list)):
        worker_list[i] = Worker(my_queue, i + 1, url_to_scrape, target_id_key, db_to_insert, scraper_func, insert_func, slicing)

    for i in range(len(worker_list)):
        worker_list[i].start()

    for i in range(len(worker_list)):
        worker_list[i].join()
    
    print("Done.")
