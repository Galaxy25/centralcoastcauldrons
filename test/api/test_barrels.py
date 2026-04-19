import sqlalchemy

from src.api.barrels import (
    calculate_barrel_summary,
    create_barrel_plan,
    Barrel,
    BarrelOrder,
)
from typing import List
from src.api.admin import reset
from src import database as db
from src.api.barrels import *
from src.api.bottler import get_bottle_plan, post_deliver_bottles
from src.api.carts import CartCheckout, CartItem, Customer, checkout, create_cart, set_item_quantity


def test_barrel_delivery() -> None:
    reset()

    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory SET 
                gold = 1000,
                red_ml = 400,
                blue_ml = 200,
                green_ml = 100,
                dark_ml = 300
                """
            )
        )
    delivery: List[Barrel] = [
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

    delivery_summary = calculate_barrel_summary(delivery)
    assert len(create_barrel_plan(1500, 1000000, 100, 100, 100, 100, delivery)) == 2

    assert delivery_summary.gold_paid == 1750
    reset()

def test_barrel_plan() -> None:
    wholesale_catalog: List[Barrel] = [
        Barrel(
            sku="SMALL_RED_BARREL",
            ml_per_barrel=1000,
            potion_type=[1.0, 0, 0, 0],
            price=50,
            quantity=10,
        ),
        Barrel(
            sku="SMALL_GREEN_BARREL",
            ml_per_barrel=1000,
            potion_type=[0, 1.0, 0, 0],
            price=50,
            quantity=5,
        ),
        Barrel(
            sku="SMALL_BLUE_BARREL",
            ml_per_barrel=1000,
            potion_type=[0, 0, 1.0, 0],
            price=50,
            quantity=2,
        ),
    ]

    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory SET 
                gold = 1000,
                red_ml = 400,
                blue_ml = 200,
                green_ml = 100,
                dark_ml = 300
                """
            )
        )
    
    post_deliver_barrels(wholesale_catalog, 0)
    with db.engine.begin() as connection:
        row = connection.execute(
            sqlalchemy.text(
                """
                SELECT gold, red_ml, green_ml, blue_ml, dark_ml
                FROM global_inventory
                """
            )
        ).one()
    assert row[0] == 150
    assert row[1] == 10400
    assert row[2] == 5100
    assert row[3] == 2200
    assert row[4] == 300

    plan = get_wholesale_purchase_plan(wholesale_catalog)[0]
    assert plan.quantity == 3
        


    reset()
    # Verify reset worked
    with db.engine.begin() as connection:
        table_row = connection.execute(
            sqlalchemy.text(
                """
                SELECT gold, red_ml, green_ml, blue_ml, dark_ml
                FROM global_inventory  
                """
            )
        ).one()

    assert table_row[0] == 100
    for i in range(1, len(table_row)):
        assert table_row[i] == 0
    reset()

def test_barrel() -> None:
    reset()
    wholesale_catalog: List[Barrel] = [
        Barrel(
            sku="SMALL_DARK_BARREL",
            ml_per_barrel=8000,
            potion_type=[0, 0, 0, 1],
            price=20,
            quantity=100,
        ),
        Barrel(
            sku="SMALL_GREEN_BARREL",
            ml_per_barrel=1000,
            potion_type=[0, 1.0, 0, 0],
            price=50,
            quantity=5,
        ),
        Barrel(
            sku="SMALL_BLUE_BARREL",
            ml_per_barrel=1000,
            potion_type=[0, 0, 1.0, 0],
            price=50,
            quantity=2,
        ),
    ]

    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory SET 
                gold = 1000,
                red_ml = 400,
                blue_ml = 200,
                green_ml = 100,
                dark_ml = 300
                """
            )
        )
    
    barrels = create_barrel_plan(1000, 1000000, 400, 100, 200, 300, wholesale_catalog)
    assert len(barrels) == 1
    assert barrels[0].quantity == 50

    reset()

def test_cart_databases():
    reset()

    #Create mixes
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory SET 
                gold = 1000,
                red_ml = 1000,
                blue_ml = 0,
                green_ml = 0,
                dark_ml = 0
                """
            )
        )
    mixes = get_bottle_plan()
    post_deliver_bottles(mixes, 0)
    response = create_cart(
        Customer(customer_id="0", customer_name="Henry", character_class="Warrior", character_species="Dragon", level=10))
    set_item_quantity(response.cart_id, "R100G0B0D0", CartItem(quantity=10))
    checkout_response = checkout(cart_id=response.cart_id,  cart_checkout=CartCheckout(payment="gold"))

    reset()
   