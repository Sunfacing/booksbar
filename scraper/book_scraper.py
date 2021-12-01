import datetime
from airflow import DAG
from airflow.operators.python_operator import PythonOperator


from kingstone import ks_scrap_category, ks_remove_duplicates, ks_checking_new_unfound_products, ks_scrap_new_products, ks_scrap_unfound_products, ks_drop_old_collection

from momo import mm_scrap_category, mm_remove_duplicates, mm_checking_new_unfound_products, mm_scrap_new_products, mm_scrap_unfound_products, mm_drop_old_collection


from sql_writer import (scraper_result_from_mongo, k_register_author, k_register_publisher, k_register_isbn, k_register_from_catalog, 
                        k_register_picture, k_register_user_comment, k_update_price, eslite_register_from_catalog, eslite_update_price, 
                        momo_register_from_catalog, momo_update_price)




with DAG(
dag_id='a_the_book_scraper',
schedule_interval='0 16 * * *',
start_date=datetime.datetime(2021, 11, 1),
catchup=False,
tags=['final_version'],
) as dag:

    # Kingstone pipeline
    task_k1 = PythonOperator(task_id='ks_scrap_category', python_callable=ks_scrap_category)
    task_k2 = PythonOperator(task_id='ks_remove_duplicates', python_callable=ks_remove_duplicates)
    task_k3 = PythonOperator(task_id='ks_checking_new_unfound_products', python_callable=ks_checking_new_unfound_products)
    task_k4 = PythonOperator(task_id='ks_scrap_new_products', python_callable=ks_scrap_new_products, retries=300)
    task_k5 = PythonOperator(task_id='ks_scrap_unfound_products', python_callable=ks_scrap_unfound_products)
    task_k6 = PythonOperator(task_id='ks_drop_old_collection', python_callable=ks_drop_old_collection)

    # Momo pipeline
    task_m1 = PythonOperator(task_id='mm_scrap_category', python_callable=mm_scrap_category)
    task_m2 = PythonOperator(task_id='mm_remove_duplicates', python_callable=mm_remove_duplicates)
    task_m3 = PythonOperator(task_id='mm_checking_new_unfound_products', python_callable=mm_checking_new_unfound_products)
    task_m4 = PythonOperator(task_id='mm_scrap_new_products', python_callable=mm_scrap_new_products)
    task_m5 = PythonOperator(task_id='mm_scrap_unfound_products', python_callable=mm_scrap_unfound_products)
    task_m6 = PythonOperator(task_id='mm_drop_old_collection', python_callable=mm_drop_old_collection)
    
    # Mongo to SQL pipeline
    task_s1 = PythonOperator(task_id='scraper_result_from_mongo', python_callable=scraper_result_from_mongo)

    task_s2 = PythonOperator(task_id='k_register_author', python_callable=k_register_author)
    task_s3 = PythonOperator(task_id='k_register_publisher', python_callable=k_register_publisher)
    task_s4 = PythonOperator(task_id='k_register_isbn', python_callable=k_register_isbn)
    task_s5 = PythonOperator(task_id='k_register_from_catalog', python_callable=k_register_from_catalog)
    task_s6 = PythonOperator(task_id='k_register_picture', python_callable=k_register_picture)
    task_s7 = PythonOperator(task_id='k_register_user_comment', python_callable=k_register_user_comment)
    task_s8 = PythonOperator(task_id='k_update_price', python_callable=k_update_price)

    task_s9 = PythonOperator(task_id='eslite_register_from_catalog', python_callable=eslite_register_from_catalog)
    task_s10 = PythonOperator(task_id='eslite_update_price', python_callable=eslite_update_price)

    task_s11 = PythonOperator(task_id='momo_register_from_catalog', python_callable=momo_register_from_catalog)
    task_s12 = PythonOperator(task_id='momo_update_price', python_callable=momo_update_price)



    [task_k1 >> task_k2 >> task_k3 >> task_k4 >> task_k5 >> task_k6 , task_m1 >> task_m2 >> task_m3 >> task_m4 >> task_m5 >> task_m6] >> task_s1 >> task_s2 >> task_s3 >> task_s4 >> task_s5
    task_s5 >> task_s6 >> task_s7 >> task_s8
    task_s5 >> task_s9 >> task_s10
    task_s5 >> task_s11 >> task_s12

