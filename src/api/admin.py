from itertools import product

from fastapi import APIRouter, Depends, status
import sqlalchemy
from src.api import auth
from src import database as db
from src.api.helper import update_gold

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
                "TRUNCATE TABLE cart_inventory, cart_checkout, potion_inventory, gold_history, ml_history, potion_history, capacity_config, ucb, transactions RESTART IDENTITY"
            )
        ) 
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO capacity_config (potion_capacity, barrel_capacity)
                VALUES (1, 1)
                """)
        )
        # Generate potion combinations with increments of 25 per type
        for red, green, blue, dark in product(range(0, 101, 25), repeat=4):
            if red + green + blue + dark == 100:
                name = f"R{red}G{green}B{blue}D{dark}"
                connection.execute(
                    sqlalchemy.text(
                        """
                        INSERT INTO potion_inventory (red_ml, blue_ml, green_ml, dark_ml, price, item_sku, name)
                        VALUES (:red, :green, :blue, :dark, 100, :item_sku, :name)
                        """),
                        [{"red": red, "green" : green, "blue" : blue, "dark" : dark, "item_sku":name, "name":name}])
                
    update_gold(100, "initial gold")

    
