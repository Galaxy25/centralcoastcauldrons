from src.api.admin import reset
from src.api.barrels import *
from src.api.helper import *

def test_calculate_barrel_summary_returns_total_gold_paid() -> None:
    reset()
    update_gold(2000)
    barrels = [
        Barrel(
            sku="SMALL_RED_BARREL",
            ml_per_barrel=1000,
            potion_type=[1.0, 0, 0, 0],
            price=100,
            quantity=10,
        ),
        Barrel(
            sku="SMALL_GREEN_BARREL",
            ml_per_barrel=1000,
            potion_type=[0, 1.0, 0, 0],
            price=150,
            quantity=5,
        ),
    ]

    delivery_summary = calculate_barrel_summary(barrels)
    assert delivery_summary.gold_paid == 1750
