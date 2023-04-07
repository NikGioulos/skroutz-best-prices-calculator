from dataclasses import dataclass, fields
from typing import List

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


def request_get_page(page_id):
    url = 'https://www.skroutz.gr/s/' + page_id
    headers = {
        'User-Agent2': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
    }
    response = requests.get(url=url, headers=headers, verify=False)
    response.raise_for_status()
    return response.text


def request_get_prices(product_ids):
    url = "https://www.skroutz.gr/personalization/product_prices.json"
    json = {'active_sizes': [], 'product_ids': product_ids}
    print("== GET - " + url)
    response = requests.post(url, json=json, verify=False)
    response.raise_for_status()
    return response.json()


def extract_links(html_string):
    # table=soup.find('href',id="main_table_countries_today")
    soup = bs4.BeautifulSoup(html_string, 'lxml')
    link_tags = soup.find_all('a', href=True)
    return list(map(lambda x: x['href'], filter(lambda a: str(a['href']).startswith('/products/show'), link_tags)))


def extract_product_id(href):
    return int(keep_digits(str(href).split('?')[0]))


def keep_digits(a_string):
    return ''.join(c for c in a_string if c.isdigit())


def get_item_prices(item_name, buy_from_skroutz_only=False) -> list[ProductPrice]:
    page1 = request_get_page(item_name)
    hrefs = extract_links(page1)
    product_ids = list(map(lambda x: extract_product_id(x), hrefs))
    product_prices = request_get_prices(product_ids)
    if buy_from_skroutz_only:
        product_prices = filter(lambda x: x['ShippingInfo'] is not None, product_prices)
    list1 = list(map(lambda pid: dict_to_class(ProductPrice, product_prices[str(pid)]), product_ids))
    return sorted(list1, key=lambda product: product.shop_id)


def calculate_best_price(item_ids: List[str], item_data: dict[str, dict[str, float]]) -> dict[str, float]:
    """
    Calculates the best total price for all given items across all shops.
    Returns a dictionary mapping shop names to their total price.
    """
    shop_prices = {}  # Dictionary to store total prices for each shop
    for shop in set(shop for item in item_ids for shop in item_data.get(item, {})):
        # Iterate over all shops that sell at least one of the requested items
        total_price = 0
        for item_id in item_ids:
            item_prices = item_data.get(item_id, {})
            if shop in item_prices:
                total_price += item_prices[shop]
            else:
                # If shop doesn't sell item, skip it
                total_price = None
                break
        if total_price is not None:
            shop_prices[shop] = total_price

    if not shop_prices:
        # If no shops sell all the items, return None
        return None

    # Find shop with the lowest total price
    best_shop = min(shop_prices, key=shop_prices.get)
    return {best_shop: shop_prices[best_shop]}


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
            # Ask the user how many items they want to buy
            qty = 1  # int(input(f"How many {item} would you like to buy from {shop}? "))
            if item in quantities.keys():
                qty = quantities[item]
            # Calculate the total price for the specified quantity of items
            item_total_price = qty * price
            shop_totals[shop]["total_items"] += qty
            shop_totals[shop]["total_price"] += item_total_price
    return shop_totals


def to_shop_price(prices):
    shop_price = {}
    for pr in prices:
        shop_price[str(pr.shop_id)] = pr.net_price
    return shop_price


def some_code():
    items = [
        "7075737/Thea-Pharma-Hellas-Thealoz-Duo-Οφθαλμικές-Σταγόνες-με-Υαλουρονικό-Οξύ-για-Ξηροφθαλμία-5ml.html",
        "9893600/Helenvita-BlephaCare-Duo-Υγρά-Μαντηλάκια-14τμχ.html",
        "30955219/A-Derma-Dermatological-Rich-Cream-Hydrating-Biology-40ml.html",
        "3157786/La-Roche-Posay-Cicaplast-Baume-B5-Balm-Ανάπλασης-για-Ευαίσθητες-Επιδερμίδες-100ml.html",
        "7586995/Froika-Κρέμα-Προσώπου-Ημέρας-για-Ενυδάτωση-Αντιγήρανση-Ανάπλαση-με-Υαλουρονικό-Οξύ-Βιταμίνη-C-40ml.html",
        "7131071/Froika-Hyaluronic-C-Ενυδατική-Αντιγηραντική-Κρέμα-Ματιών-κατά-των-Μαύρων-Κύκλων-για-Λάμψη-με-Υαλουρονικό-Οξύ-Βιταμίνη-C-για-Ώριμες-Επιδερμίδες-15ml.html"
    ]
    quantities = {
        "30955219/A-Derma-Dermatological-Rich-Cream-Hydrating-Biology-40ml.html": 2,
        "7586995/Froika-Κρέμα-Προσώπου-Ημέρας-για-Ενυδάτωση-Αντιγήρανση-Ανάπλαση-με-Υαλουρονικό-Οξύ-Βιταμίνη-C-40ml.html": 2
    }
    buy_from_skroutz_only = False

    item_data = {}
    for item in items:
        prices = get_item_prices(item, buy_from_skroutz_only)
        item_data[item] = to_shop_price(prices)
    print(item_data)

    best_shop = calculate_best_price(items, item_data)
    print(best_shop)
    print('======')
    shop_totals2 = calculate_shop_total_items_and_price(item_data, quantities)
    for shop, totals in shop_totals2.items():
        if totals['total_items'] >= len(item_data.items()):
            print(f"{shop}: Total items = {totals['total_items']}, Total price = {totals['total_price']}")


if __name__ == '__main__':
    some_code()
