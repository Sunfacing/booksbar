import requests
from ip_list import ip_list
import random
from fake_useragent import UserAgent


import time



from datetime import date, timedelta
import datetime
import pytz
my_date = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y-%m-%d")
print(my_date)


TODAY = datetime.datetime.now(pytz.timezone('Asia/Taipei')).strftime("%Y-%m-%d")
TODAY_FOR_COLLECTION_NAME = (datetime.datetime.now(pytz.timezone('Asia/Taipei'))).strftime("%m%d")
DATE_SUBTRACT_1 = (datetime.datetime.now(pytz.timezone('Asia/Taipei')) - timedelta(days=1)).strftime("%m%d")
YESTERDAY_FOR_EORROR_CHECKER = ''.join(DATE_SUBTRACT_1)
DATE_SUBTRACT_7 = (datetime.datetime.now(pytz.timezone('Asia/Taipei')) - timedelta(days=7)).strftime("%m%d")
DATE_FOR_DELETE_COLLECTION_NAME = ''.join(DATE_SUBTRACT_7)




HEADERS = {'User-Agent': UserAgent().random}


ip = random.choice(ip_list)
proxy = {
    'http': 'http://117.85.105.170:808',
    'https': 'https://117.85.105.170:808'
}
ip = random.choice(ip_list)
head = {'User-Agent': UserAgent().random}
# # https://athena.eslite.com/api/v2/search?final_price=0,&sort=manufacturer_date+desc&size=100&start=1&categories=[36]
p = requests.get('https://www.kingstone.com.tw/basic/2029140640929', 
                headers=HEADERS, proxies={"http": ip, "https": ip}, timeout=60)
                
print(p.content.decode('utf-8'))
print(p)

# from urllib import request as urlrequest

# req = urlrequest.Request('https://athena.eslite.com/api/v2/search?final_price=0,&sort=manufacturer_date+desc&size=100&start=1&categories=[36]', headers={'User-Agent': 'Mozilla/5.0'})
# req.set_proxy(ip, 'http')
# webpage = urlrequest.urlopen(req).read().decode('utf-8')
# print(webpage)


# from urllib import request as urlrequest

# proxy_host = 'https://cpzwueik:lx1j2lt584r0@193.8.231.191:9197'    # host and port of your proxy
# url = 'http://www.httpbin.org/ip'

# req = urlrequest.Request(url)
# req.set_proxy(proxy_host, 'http')

# response = urlrequest.urlopen(req)
# print(response.read().decode('utf8'))