from src.api.admin import reset
from src.api.helper import *

def test_gold_history() -> None:
    reset()
    update_gold(100, "test gold change")
    assert get_gold_total() == 200
    update_gold(550, "test gold change")
    assert get_gold_total() == 750
    update_gold(-750, "test gold change")
    assert get_gold_total() == 0

def test_ml_history() -> None:
    reset()
    update_ml(red_ml=100)
    ml_total = get_ml_total()
    assert ml_total.red_ml == 100
    assert ml_total.green_ml == 0
    assert ml_total.blue_ml == 0
    assert ml_total.dark_ml == 0

    update_ml(green_ml=200, blue_ml=250, dark_ml=300)
    ml_total = get_ml_total()
    assert ml_total.red_ml == 100
    assert ml_total.green_ml == 200
    assert ml_total.blue_ml == 250
    assert ml_total.dark_ml == 300
    
    update_ml(red_ml=-100, green_ml=-100, blue_ml=-100, dark_ml=-100)
    ml_total = get_ml_total()
    assert ml_total.red_ml == 0
    assert ml_total.green_ml == 100
    assert ml_total.blue_ml == 150
    assert ml_total.dark_ml == 200

def test_potion_history() -> None:
    reset()
    update_potions(1, 10)
    assert get_potion(1) == 10
    update_potions(1, 20)
    assert get_potion(1) == 30
    update_potions(1, -10)
    assert get_potion(1) == 20
    potions = get_all_potions()
    assert potions[0].quantity == 20
    assert len(potions) == 1

    update_potions(2, 1)
    update_potions(3, 1)
    update_potions(4, 5)
    potions = get_all_potions()
    assert len(potions) == 4
    print(potions)
    assert potions[0].quantity == 20
    assert potions[1].quantity == 1
    assert potions[2].quantity == 1
    assert potions[3].quantity == 5

