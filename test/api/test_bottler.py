from src.api.bottler import *
from src.api.admin import reset

from typing import List


def test_bottle_red_potions() -> None:
    reset()
    red_ml: int = 100
    green_ml: int = 0
    blue_ml: int = 0
    dark_ml: int = 0
    maximum_potion_capacity: int = 1000
    current_potion_inventory: List[PotionMixes] = []

    result = create_bottle_plan(
        red_ml=red_ml,
        green_ml=green_ml,
        blue_ml=blue_ml,
        dark_ml=dark_ml,
        maximum_potion_capacity=maximum_potion_capacity,
        current_potion_inventory=current_potion_inventory,
    )
    assert len(result) == 1
    assert result[0].potion_type == [100, 0, 0, 0]
    assert result[0].quantity == 1

def test_bottler_database() -> None: 
    reset()
    update_ml(red_ml=400, blue_ml=200, green_ml=100, dark_ml=100)
    ml_total = get_ml_total()
    assert ml_total.red_ml == 400
    assert ml_total.green_ml == 100
    assert ml_total.blue_ml == 200
    assert ml_total.dark_ml == 100

    assert sum([potions.quantity for potions in get_bottle_plan()]) != 0
    post_deliver_bottles(get_bottle_plan(), 0)


    reset()
    # Verify reset worked
    assert get_gold_total() == 100
    ml_total = get_ml_total()
    assert ml_total.red_ml == 0
    assert ml_total.green_ml == 0
    assert ml_total.blue_ml == 0
    assert ml_total.dark_ml == 0


