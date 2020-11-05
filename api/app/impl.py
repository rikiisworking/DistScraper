import grequests
import requests
import re
import json
import datetime
from pytz import timezone, utc
from urllib.parse import quote
from config import COUPANG_HEADER, GMARKET_HEADER, \
    ELEVEN_HEADER, INTERPARK_HEADER, \
    AUCTION_HEADER, WEMAKEPRICE_HEADER, \
    TMON_HEADER, COUPANG_SEARCH_URL, \
    GMARKET_SEARCH_URL, ELEVEN_SEARCH_URL, \
    INTERPARK_SEARCH_URL, AUCTION_SEARCH_URL, \
    WEMAKEPRICE_SEARCH_URL, TMON_SEARCH_URL
from bs4 import BeautifulSoup
from concurrent.futures.process import ProcessPoolExecutor
from multiprocessing import Pool

global_products = {}


def time_kr_now():
    KST = timezone('Asia/Seoul')
    now = datetime.datetime.utcnow()
    utc.localize(now)
    KST.localize(now)
    return utc.localize(now).astimezone(KST)


def refine_coupang(response, *args, **kwargs):
    soup = BeautifulSoup(response.text, 'lxml')
    product_elements = soup.select(".search-product")
    return {'coupang_result': [{
        'title': element.select_one('.name').text,
        'price': int(element.select_one('.price-value').text.replace(',','')),
        'product_id': element['data-product-id'],
        'url':"https://www.coupang.com/"+element.select_one('a.search-product-link')['href']
    } for element in product_elements]}


async def coupang_products(query, sort='scoreDesc', page='1'):
    url = COUPANG_SEARCH_URL
    params = {'q': query, 'sorter': sort, 'listSize': '100', 'page': str(page)}
    r = requests.get(url=url, headers=COUPANG_HEADER, params=params)
    return refine_coupang(r)


def coupang_products_raw(query, page='1'):
    url = COUPANG_SEARCH_URL
    params = {'q': query, 'listSize': '100', 'page': str(page)}
    r = requests.get(url=url, headers=COUPANG_HEADER, params=params)
    return r.text


def refine_gmarket(response, *args, **kwargs):
    soup = BeautifulSoup(response.text, 'lxml')
    raw_data = soup.select_one("#initial-state")
    data = json.loads(raw_data.string.replace(
        "window.__APP_INITIAL_STATE__=", ""))
    content = next(
        item for item in data['regions'] if item['name'] == 'content')

    items = list(item['rows']
                 for item in content['modules'] if item['designGroup'] == 15)
    if len(items) > 1:
        flat_list = [item for sublist in items for item in sublist]
    else:
        flat_list = items[0]
    return {'gmarket_result': [{'title': each['viewModel']['commonItemInfo']['item']['text'],
                                'price':int(each['viewModel']['commonItemInfo']['price']['binPrice'].replace(',','')),
                                'product_id':each['viewModel']['itemNo'],
                                'url':f'http://item.gmarket.co.kr/Item?goodscode={str(each["viewModel"]["itemNo"])}'} for each in flat_list]}


async def gmarket_products(query, sort='7', page='1'):
    url = GMARKET_SEARCH_URL
    params = {'keyword': query, 's': sort, 'p': page}
    r = requests.get(url=url, headers=GMARKET_HEADER, params=params)
    return refine_gmarket(r)


def gmarket_products_raw(query, page='1'):
    url = GMARKET_SEARCH_URL
    params = {'keyword': query, 'p': page}
    r = requests.get(url=url, headers=GMARKET_HEADER, params=params)
    """soup = BeautifulSoup(r.text, 'lxml')
    raw_data = soup.select_one("#initial-state")"""
    """data = json.loads(raw_data.string.replace(
        "window.__APP_INITIAL_STATE__=", ""))"""
    return r.text


def refine_eleven(response, *args, **kwargs):
    res = re.findall(
        r'window\.searchDataFactory\.catalogPrdList = (.*);', response.text)
    products = json.loads(res[0])['items']
    return {'eleven_result': [{
        'title': each['prdNm'],
        'price':int(each['finalPrc'].replace(',','')),
        'product_id':str(each['prdNo']),
        'url':each['productDetailUrl']
    }for each in products]}


async def elevenStreet_products(query, page='1'):
    encoded_query = quote(quote(query))
    params = {'kwd': encoded_query, 'method': 'getCatalogPrdSearch',
              'catalogYN': 'Y', 'pageNo': page}
    url = ELEVEN_SEARCH_URL
    r = requests.get(url=url, headers=ELEVEN_HEADER, params=params)
    return refine_eleven(r)


def elevenStreet_products_raw(query, page='1'):
    encoded_query = quote(quote(query))
    params = {'kwd': encoded_query, 'method': 'getCatalogPrdSearch',
              'catalogYN': 'Y', 'pageNo': page}
    url = ELEVEN_SEARCH_URL
    r = requests.get(url=url, headers=ELEVEN_HEADER, params=params)
    return r.text


def refine_interpark(response, *args, **kwargs):
    products = response.json()['data']['listChoiceAndNormal']
    return {'interpark_result': [{
        'title': each['name'],
        'price':each['final_sell_price'],
        'product_id':str(each['prdNo']),
        'url':f"http://shopping.interpark.com/product/productInfo.do?prdNo={str(each['prdNo'])}"
    } for each in products]}


async def interpark_products(query, page=1):
    timestamp = str(time_kr_now().timestamp()*1000).split('.')[0]
    params = {
        'pis1': 'shop',
        'page': str(page),
        'keyword': quote(query),
        'rows': '52',
        'pis2': 'more',
        '_': timestamp
    }
    url = INTERPARK_SEARCH_URL
    r = requests.get(url=url, headers=INTERPARK_HEADER(
        page=page, q=quote(query)), params=params)
    return refine_interpark(r)


def interpark_products_raw(query, page='1'):
    timestamp = str(time_kr_now().timestamp()*1000).split('.')[0]
    params = {
        'pis1': 'shop',
        'page': str(page),
        'keyword': quote(query),
        'rows': '52',
        'pis2': 'more',
        '_': timestamp
    }
    url = INTERPARK_SEARCH_URL
    r = requests.get(url=url, headers=INTERPARK_HEADER(
        page=page, q=quote(query)), params=params)
    return r.text


def refine_auction(response, *args, **kwargs):
    soup = BeautifulSoup(response.text, 'lxml')
    raw_data = soup.select_one("#initial-state")
    data = json.loads(raw_data.string.replace(
        "window.__APP_INITIAL_STATE__=", ""))

    content = next(
        item for item in data['regions'] if item['name'] == 'content')
    items = list(item['rows']
                 for item in content['modules'] if item['designGroup'] == 17)
    if len(items) > 1:
        flat_list = [item for sublist in items for item in sublist]
    else:
        flat_list = items[0]
    return {'auction_result': [
        {'title': each['viewModel']['item']['text'],
            'price':int(each['viewModel']['price']['binPrice'].replace(',','')),
            'product_id':each['viewModel']['itemNo'],
            'url':f'http://itempage3.auction.co.kr/DetailView.aspx?itemno={each["viewModel"]["itemNo"]}'} for each in flat_list]}


async def auction_products(query, page=1):
    url = AUCTION_SEARCH_URL
    params = {
        "keyword": query,
        "itemno": "",
        "nickname": "",
        "encKeyword": quote(query),
        "arraycategory": "",
        "frm": "",
        "dom": "auction",
        "isSuggestion": "No",
        "retry": "",
        "s": "7",
        "k": "24",
        "p": str(page)
    }
    r = requests.get(url=url, headers=AUCTION_HEADER(keyword=quote(
        query), enckeyword=quote(quote(query)), page=str(page)), params=params)
    return refine_auction(r)


def auction_products_raw(query, page='1'):
    url = AUCTION_SEARCH_URL
    params = {
        "keyword": query,
        "itemno": "",
        "nickname": "",
        "encKeyword": quote(query),
        "arraycategory": "",
        "frm": "",
        "dom": "auction",
        "isSuggestion": "No",
        "retry": "",
        "s": "7",
        "k": "24",
        "p": str(page)
    }
    r = requests.get(url=url, headers=AUCTION_HEADER(keyword=quote(
        query), enckeyword=quote(quote(query)), page=str(page)), params=params)
    '''    soup = BeautifulSoup(r.text, 'lxml')
    raw_data = soup.select_one("#initial-state")
    data = json.loads(raw_data.string.replace(
        "window.__APP_INITIAL_STATE__=", ""))'''
    return r.text


def refine_weMakePrice(response, *args, **kwargs):
    products = response.json()['data']['deals']
    return {'weMakePrice_result': [
        {
            'title': each['dispNm'],
            'price':each['salePrice'],
            'product_id':str(each['link']['value']),
            'url':f'https://front.wemakeprice.com/product/{str(each["link"]["value"])}'
        } for each in products
    ]}


async def weMakePrice_products(query, page='1'):
    url = WEMAKEPRICE_SEARCH_URL
    headers = WEMAKEPRICE_HEADER(quote(query))
    params = {
        "searchType": "DEFAULT",
        "search_cate": "top",
        "keyword": query,
        "isRec": "1",
        "_service": "5",
        "_type": "3",
        "page": page
    }
    r = requests.get(url=url, headers=headers, params=params)
    return refine_weMakePrice(r)


def weMakePrice_products_raw(query, page='1'):
    url = WEMAKEPRICE_SEARCH_URL
    headers = WEMAKEPRICE_HEADER(quote(query))
    params = {
        "searchType": "DEFAULT",
        "search_cate": "top",
        "keyword": query,
        "isRec": "1",
        "_service": "5",
        "_type": "3",
        "page": page
    }
    r = requests.get(url=url, headers=headers, params=params)
    return r.text


def refine_tmon(response, *args, **kwargs):
    products = response.json()['data']['searchDeals']
    return {'tmon_result': [
        {
            'title': each['searchDealResponse']['dealInfo']['titleName'],
            'price':each['searchDealResponse']['dealInfo']['priceInfo']['price'],
            'product_id':str(each['searchDealResponse']['dealInfo']['dealNo']),
            'url':f'http://www.tmon.co.kr/deal/{each["searchDealResponse"]["dealInfo"]["dealNo"]}',
        } for each in products
    ]}


async def tmon_products(query, page='1'):
    url = TMON_SEARCH_URL
    headers = TMON_HEADER(quote(query))
    params = {
        "_": str(time_kr_now().timestamp()*1000).split('.')[0],
        "keyword": query,
        "mainDealOnly": "true",
        "optionDealOnly": "false",
        "page": str(page),
        "useTypoCorrection": "true",
        "sortType": "POPULAR"
    }
    r = requests.get(url=url, headers=headers, params=params)
    return refine_tmon(r)


def tmon_products_raw(query, page='1'):
    url = TMON_SEARCH_URL
    headers = TMON_HEADER(quote(query))
    params = {
        "_": str(time_kr_now().timestamp()*1000).split('.')[0],
        "keyword": query,
        "mainDealOnly": "true",
        "optionDealOnly": "false",
        "page": str(page),
        "useTypoCorrection": "true",
        "sortType": "POPULAR"
    }
    r = requests.get(url=url, headers=headers, params=params)
    return r.text

def refine_data(response):
    if 'coupang' in response.url:
        return refine_coupang(response)
    elif 'gmarket' in response.url:
        return refine_gmarket(response)
    elif '11st' in response.url:
        return refine_eleven(response)
    elif 'interpark' in response.url:
        return refine_interpark(response)
    elif 'auction' in response.url:
        return refine_auction(response)
    elif 'wemakeprice' in response.url:
        return refine_weMakePrice(response)
    elif 'tmon' in response.url:
        return refine_tmon(response)


async def all_products(query, page='1'):
    async_list = []
    async_list.append(grequests.get(
        url=COUPANG_SEARCH_URL,
        headers=COUPANG_HEADER,
        params={'q': query, 'sorter': 'scoreDesc',
                'listSize': '100', 'page': str(page)}
    ))
    async_list.append(grequests.get(
        url=GMARKET_SEARCH_URL,
        headers=GMARKET_HEADER,
        params={'keyword': query, 's': '7', 'p': page}
    ))
    async_list.append(grequests.get(
        url=ELEVEN_SEARCH_URL,
        headers=ELEVEN_HEADER,
        params={'kwd': quote(quote(query)), 'method': 'getCatalogPrdSearch',
                'catalogYN': 'Y', 'pageNo': page}
    ))
    async_list.append(grequests.get(
        url=INTERPARK_SEARCH_URL,
        headers=INTERPARK_HEADER(
            page=page, q=quote(query)),
        params={
            'pis1': 'shop',
            'page': str(page),
            'keyword': quote(query),
            'rows': '52',
            'pis2': 'more',
            '_': str(time_kr_now().timestamp()*1000).split('.')[0]
        }
    ))
    async_list.append(grequests.get(
        url=AUCTION_SEARCH_URL,
        headers=AUCTION_HEADER(keyword=quote(
            query), enckeyword=quote(quote(query)), page=str(page)),
        params={
            "keyword": query,
            "itemno": "",
            "nickname": "",
            "encKeyword": quote(query),
            "arraycategory": "",
            "frm": "",
            "dom": "auction",
            "isSuggestion": "No",
            "retry": "",
            "s": "7",
            "k": "24",
            "p": str(page)
        }
    ))
    async_list.append(grequests.get(
        url=WEMAKEPRICE_SEARCH_URL,
        headers=WEMAKEPRICE_HEADER(quote(query)),
        params={
            "searchType": "DEFAULT",
            "search_cate": "top",
            "keyword": query,
            "isRec": "1",
            "_service": "5",
            "_type": "3",
            "page": page
        }
    ))
    async_list.append(grequests.get(
        url=TMON_SEARCH_URL,
        headers=TMON_HEADER(quote(query)),
        params={
            "_": str(time_kr_now().timestamp()*1000).split('.')[0],
            "keyword": query,
            "mainDealOnly": "true",
            "optionDealOnly": "false",
            "page": str(page),
            "useTypoCorrection": "true",
            "sortType": "POPULAR"
        }
    ))

    with ProcessPoolExecutor(max_workers=4) as executor:
        return {'result': [each.result() for each in [executor.submit(refine_data, each) for each in grequests.map(async_list, size=7) if each.status_code == 200]]}
