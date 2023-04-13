from dataclasses import dataclass, fields
from typing import List

import time
import yaml
import bs4
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@dataclass
class ShippingInfo:
    template_name: str


@dataclass
class ProductPrice:
    final_price: float
    payment_method_cost: float
    net_price: float
    net_price_formatted: str
    final_price_formatted: str
    shop_id: int
    no_credit_card: bool
    sorting_score: List[float]
    payment_method_cost_supported: None
    ecommerce_payment_method_cost_supported: None
    free_shipping_cost_supported: bool
    ecommerce_final_price: float
    ecommerce_final_price_formatted: str
    ecommerce_payment_method_cost: float
    final_price_without_payment_cost_formatted: str
    sorting_prices: List[float]
    shipping_info: ShippingInfo
    untracked_redirect_supported: bool
    shipping_cost: float
    link: str


def dict_to_class(class_name, some_dict):
    fields_set = {f.name for f in fields(class_name) if f.init}
    filtered_arg_dict = {k: v for k, v in some_dict.items() if k in fields_set}
    return class_name(**filtered_arg_dict)


def request_get_item_page(item_name):
    url = 'https://www.skroutz.gr/s/' + item_name
    response = request_send(url)
    response.raise_for_status()
    return response.text


def request_get_prices(product_ids):
    url = "https://www.skroutz.gr/personalization/product_prices.json"
    json = {'active_sizes': [], 'product_ids': product_ids}
    response = request_send(url, json)
    return response.json()


def request_send(url, json=None):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        'Cache-Control': 'no-cache',
        'Accept': '*/*'
    }
    time.sleep(0.9)
    if json is None:
        print("== GET - " + url)
        response = requests.get(url, headers=headers, verify=False)
    else:
        print("== POST - " + url)
        response = requests.post(url, json=json, headers=headers, verify=False)
    response.raise_for_status()
    return response


def extract_links(html_string):
    soup = bs4.BeautifulSoup(html_string, 'lxml')
    link_tags = soup.find_all('a', href=True)
    return list(map(lambda x: x['href'], filter(lambda a: str(a['href']).startswith('/products/show'), link_tags)))


def extract_product_id(href):
    return int(keep_digits(str(href).split('?')[0]))


def keep_digits(a_string):
    return ''.join(c for c in a_string if c.isdigit())


def get_item_prices(item_name, only_skroutz_shops=False) -> list[ProductPrice]:
    item_page = request_get_item_page(item_name)
    hrefs = extract_links(item_page)
    product_ids = [extract_product_id(href) for href in hrefs]
    product_prices = request_get_prices(product_ids)
    if only_skroutz_shops:
        product_prices = {key: value for key, value in product_prices.items() if value['ShippingInfo'] is not None}
    price_list = [dict_to_class(ProductPrice, product_prices[str(pid)]) for pid in product_ids]
    return sorted(price_list, key=lambda product: product.shop_id)


def calculate_shop_total_items_and_price(items_and_prices: dict, quantities: dict) -> dict:
    """
    Calculates the number of items that can be bought from each shop and the total price of these items.
    Returns a dictionary containing the number of items and total price for each shop.
    """
    shop_totals = {}
    for item, shop_prices in items_and_prices.items():
        for shop, price in shop_prices.items():
            if shop not in shop_totals:
                shop_totals[shop] = {"total_items": 0, "total_price": 0}
            shop_totals[shop]["total_items"] += 1
            shop_totals[shop]["total_price"] += quantities[item] * price
    return shop_totals


def to_shop_price(prices):
    return {str(pr.shop_id): pr.net_price for pr in prices}


def fetch_items_data(items, only_skroutz_shops):
    return {item['name']: to_shop_price(get_item_prices(item['name'], only_skroutz_shops)) for item in items}


def find_cheaper_shop(item_data, quantities):
    shop_totals = calculate_shop_total_items_and_price(item_data, quantities)
    totals = {k: v for k, v in shop_totals.items() if len(quantities.items()) == v['total_items']}
    totals = dict(sorted(totals.items(), key=lambda x: x[1]['total_price'], reverse=False))
    return totals


def load_config_file(yaml_file):
    with open(yaml_file, mode='r', encoding='utf-8') as file:
        return yaml.safe_load(file)


def execute(items, only_skroutz_shops):
    item_data = fetch_items_data(items, only_skroutz_shops)
    quantities = {item['name']: item['qnt'] for item in items}
    shop_totals = find_cheaper_shop(item_data, quantities)
    for shop, totals in shop_totals.items():
        print(f"{shop}: Total items = {totals['total_items']}, Total price = {totals['total_price']}")


if __name__ == '__main__':
    execute(load_config_file('items.yaml'), only_skroutz_shops=False)
