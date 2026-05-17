from itertools import product

from fastapi import APIRouter, Depends, status
import sqlalchemy
from src.api import auth
from src import database as db
from src.api.helper import POTION_PRICE, update_gold

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)


@router.post("/reset", status_code=status.HTTP_204_NO_CONTENT)
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """

    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                TRUNCATE TABLE
                    cart_inventory,
                    cart_checkout,
                    customer_seen,
                    ucb,
                    potion_inventory,
                    global_inventory,
                    gold_history,
                    ml_history,
                    potion_history,
                    capacity_config,
                    transactions
                RESTART IDENTITY CASCADE
                """
            )
        )
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO capacity_config (potion_capacity, barrel_capacity)
                VALUES (1, 1)
                """
            )
        )
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO global_inventory (id, gold, red_ml, green_ml, blue_ml, dark_ml)
                VALUES (1, 0, 0, 0, 0, 0)
                """
            )
        )

        for red, green, blue, dark in product(range(0, 101, 25), repeat=4):
            if red + green + blue + dark == 100:
                name = f"R{red}G{green}B{blue}D{dark}"
                connection.execute(
                    sqlalchemy.text(
                        """
                        INSERT INTO potion_inventory (red_ml, green_ml, blue_ml, dark_ml, price, item_sku, name)
                        VALUES (:red, :green, :blue, :dark, :price, :item_sku, :name)
                        """
                    ),
                    [
                        {
                            "red": red,
                            "green": green,
                            "blue": blue,
                            "dark": dark,
                            "price": POTION_PRICE,
                            "item_sku": name,
                            "name": name,
                        }
                    ],
                )

        update_gold(connection, 100, "initial gold")
