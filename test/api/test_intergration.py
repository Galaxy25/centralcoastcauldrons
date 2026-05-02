from typing import List

from src.api.admin import reset
from src.api.barrels import Barrel, get_wholesale_purchase_plan, post_deliver_barrels
from src.api.bottler import get_bottle_plan, post_deliver_bottles
from src.api.helper import get_all_potions, get_ml_total, update_gold


def test_simulation():
    reset()
    update_gold(2000)
    barrel_catalog: List[Barrel] = [
        Barrel(sku="RED", ml_per_barrel=500, potion_type=[1, 0, 0, 0], price=100, quantity=99),
        Barrel(sku="GREEN", ml_per_barrel=500, potion_type=[0, 1, 0, 0], price=100, quantity=99),
        Barrel(sku="BLUE", ml_per_barrel=500, potion_type=[0, 0, 1, 0], price=100, quantity=99),
        Barrel(sku="DARK", ml_per_barrel=500, potion_type=[0, 0, 0, 1], price=100, quantity=99),
    ]
    purchase_plan = get_wholesale_purchase_plan(barrel_catalog)
    barrels = []
    for order in purchase_plan:
        for barrel in barrel_catalog:
            if barrel.sku == order.sku:
                barrels.append(Barrel(
                    sku=barrel.sku,
                    ml_per_barrel=barrel.ml_per_barrel,
                    potion_type=barrel.potion_type,
                    price=barrel.price,
                    quantity=order.quantity
                ))

    post_deliver_barrels(barrels, 0)

    ml_total = get_ml_total()
    assert ml_total.red_ml == 2500
    assert ml_total.green_ml == 2500
    assert ml_total.blue_ml == 2500
    assert ml_total.dark_ml == 2500

    plan = get_bottle_plan()
    post_deliver_bottles(plan, 1)

    expected = {}
    for potion in plan:
        sku = f"R{potion.potion_type[0]}G{potion.potion_type[1]}B{potion.potion_type[2]}D{potion.potion_type[3]}"
        expected[sku] = expected.get(sku, 0) + potion.quantity

    potions = get_all_potions()
    assert len(potions) == len(expected)
    for potion in potions:
        assert potion.item_sku in expected
        assert potion.quantity == expected[potion.item_sku]
    assert len(potions) != 0

