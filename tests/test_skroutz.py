import skroutz


def test_find_cheaper_shop():
    item_data = {
        "item1": {
            "shop1": 1.11,
            "shop2": 2.22,
            "shop3": 7.25
        },
        "item2": {
            "shop1": 31.50,
            "shop2": 22.22,
            "shop4": 17.25
        },
        "item3": {
            "shop1": 10,
            "shop2": 11,
            "shop5": 27.25,
            "shop6": 28.27
        }
    }

    quantities = {
        "item1": 1,
        "item2": 2,
        "item3": 1
    }
    shop_totals = skroutz.find_cheaper_shop(item_data, quantities)
    assert len(shop_totals) == 2
    assert shop_totals['shop1'] is not None
    assert shop_totals['shop1']['total_items'] == 3
    assert round(shop_totals['shop1']['total_price'], 2) == 74.11
    assert shop_totals['shop2'] is not None
    assert shop_totals['shop2']['total_items'] == 3
    assert round(shop_totals['shop2']['total_price'], 2) == 57.66
