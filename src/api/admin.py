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
                "TRUNCATE TABLE cart_inventory, cart_checkout, potion_inventory, global_inventory, gold_history, ml_history, potion_history, capacity_config, ucb, transactions RESTART IDENTITY CASCADE"
            )
        ) 
        connection.execute(sqlalchemy.text("DROP TABLE IF EXISTS cart_inventory"))
        connection.execute(sqlalchemy.text("DROP TABLE IF EXISTS cart_checkout CASCADE"))
        connection.execute(sqlalchemy.text("DROP TABLE IF EXISTS ucb"))
        connection.execute(
            sqlalchemy.text(
                """
                CREATE TABLE cart_checkout (
                    id SERIAL PRIMARY KEY,
                    customer_id TEXT NOT NULL UNIQUE,
                    customer_name TEXT,
                    customer_species TEXT,
                    customer_class TEXT,
                    level INTEGER,
                    transaction_id INTEGER NOT NULL REFERENCES transactions(id)
                )
                """
            )
        )
        connection.execute(
            sqlalchemy.text(
                """
                CREATE TABLE cart_inventory (
                    id SERIAL PRIMARY KEY,
                    cart_id INTEGER NOT NULL REFERENCES cart_checkout(id),
                    potion_id INTEGER NOT NULL REFERENCES potion_inventory(id),
                    quantity INTEGER NOT NULL DEFAULT 1
                )
                """
            )
        )
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO capacity_config (potion_capacity, barrel_capacity)
                VALUES (1, 1)
                """)
        )
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO global_inventory (id, gold, red_ml, green_ml, blue_ml, dark_ml)
                VALUES (1, 0, 0, 0, 0, 0)
                """
            )
        )
        connection.execute(
            sqlalchemy.text(
                """
                CREATE TABLE ucb (
                    id SERIAL PRIMARY KEY,
                    game_day TEXT NOT NULL,
                    potion_id INTEGER NOT NULL REFERENCES potion_inventory(id),
                    bought INTEGER NOT NULL DEFAULT 0,
                    shown INTEGER NOT NULL DEFAULT 0,
                    ucb_value DOUBLE PRECISION NOT NULL DEFAULT 0,
                    CONSTRAINT uq_ucb_game_day_potion_id UNIQUE (game_day, potion_id)
                )
                """
            )
        )

        # Generate potion combinations with increments of 25 per type
        for red, green, blue, dark in product(range(0, 101, 25), repeat=4):
            if red + green + blue + dark == 100:
                name = f"R{red}G{green}B{blue}D{dark}"
                connection.execute(
                    sqlalchemy.text(
                        """
                        INSERT INTO potion_inventory (red_ml, green_ml, blue_ml, dark_ml, price, item_sku, name)
                        VALUES (:red, :green, :blue, :dark, 100, :item_sku, :name)
                        """),
                        [{"red": red, "green" : green, "blue" : blue, "dark" : dark, "item_sku":name, "name":name}])
        
        # Seeding data from previous card id
        ucb_rows = [
            ("Monday", 1, 1, 2, 2.0),
            ("Monday", 2, 1, 2, 2.0),
            ("Monday", 3, 1, 2, 2.0),
            ("Monday", 4, 1, 2, 2.0),
            ("Monday", 5, 5, 5, 1.8),
            ("Monday", 6, 1, 2, 2.0),
            ("Monday", 7, 1, 2, 2.0),
            ("Monday", 8, 1, 2, 2.0),
            ("Monday", 9, 3, 5, 1.7),
            ("Monday", 10, 1, 2, 2.0),
            ("Monday", 11, 1, 2, 2.0),
            ("Monday", 12, 3, 5, 1.7),
            ("Monday", 13, 1, 2, 2.0),
            ("Monday", 14, 3, 5, 1.7),
            ("Monday", 15, 5, 5, 1.8),
            ("Monday", 16, 1, 2, 2.0),
            ("Monday", 17, 1, 2, 2.0),
            ("Monday", 18, 1, 2, 2.0),
            ("Monday", 19, 3, 5, 1.7),
            ("Monday", 20, 1, 2, 2.0),
            ("Monday", 21, 1, 2, 2.0),
            ("Monday", 22, 3, 5, 1.7),
            ("Monday", 23, 1, 2, 2.0),
            ("Monday", 24, 3, 5, 1.7),
            ("Monday", 25, 3, 5, 1.7),
            ("Monday", 26, 1, 2, 2.0),
            ("Monday", 27, 1, 2, 2.0),
            ("Monday", 28, 3, 5, 1.7),
            ("Monday", 29, 1, 2, 2.0),
            ("Monday", 30, 3, 5, 1.7),
            ("Monday", 31, 3, 5, 1.7),
            ("Monday", 32, 1, 2, 2.0),
            ("Monday", 33, 3, 5, 1.7),
            ("Monday", 34, 3, 5, 1.7),
            ("Monday", 35, 5, 5, 1.8),
            ("Tuesday", 1, 1, 2, 2.0),
            ("Tuesday", 2, 1, 2, 2.0),
            ("Tuesday", 3, 1, 2, 2.0),
            ("Tuesday", 4, 1, 2, 2.0),
            ("Tuesday", 5, 5, 5, 1.8),
            ("Tuesday", 6, 1, 2, 2.0),
            ("Tuesday", 7, 1, 2, 2.0),
            ("Tuesday", 8, 1, 2, 2.0),
            ("Tuesday", 9, 1, 5, 2.0),
            ("Tuesday", 10, 1, 2, 2.0),
            ("Tuesday", 11, 1, 2, 2.0),
            ("Tuesday", 12, 1, 5, 2.0),
            ("Tuesday", 13, 1, 2, 2.0),
            ("Tuesday", 14, 1, 5, 2.0),
            ("Tuesday", 15, 1, 5, 2.0),
            ("Tuesday", 16, 1, 2, 2.0),
            ("Tuesday", 17, 1, 2, 2.0),
            ("Tuesday", 18, 1, 2, 2.0),
            ("Tuesday", 19, 3, 5, 1.7),
            ("Tuesday", 20, 1, 2, 2.0),
            ("Tuesday", 21, 1, 2, 2.0),
            ("Tuesday", 22, 3, 5, 1.7),
            ("Tuesday", 23, 1, 2, 2.0),
            ("Tuesday", 24, 3, 5, 1.7),
            ("Tuesday", 25, 1, 5, 2.0),
            ("Tuesday", 26, 1, 2, 2.0),
            ("Tuesday", 27, 1, 2, 2.0),
            ("Tuesday", 28, 3, 5, 1.7),
            ("Tuesday", 29, 1, 2, 2.0),
            ("Tuesday", 30, 3, 5, 1.7),
            ("Tuesday", 31, 1, 5, 2.0),
            ("Tuesday", 32, 1, 2, 2.0),
            ("Tuesday", 33, 3, 5, 1.7),
            ("Tuesday", 34, 1, 5, 2.0),
            ("Tuesday", 35, 2, 5, 1.7),
            ("Wednesday", 1, 1, 2, 2.0),
            ("Wednesday", 2, 1, 2, 2.0),
            ("Wednesday", 3, 1, 2, 2.0),
            ("Wednesday", 4, 1, 2, 2.0),
            ("Wednesday", 5, 2, 5, 1.7),
            ("Wednesday", 6, 1, 2, 2.0),
            ("Wednesday", 7, 1, 2, 2.0),
            ("Wednesday", 8, 1, 2, 2.0),
            ("Wednesday", 9, 3, 5, 1.7),
            ("Wednesday", 10, 1, 2, 2.0),
            ("Wednesday", 11, 1, 2, 2.0),
            ("Wednesday", 12, 3, 5, 1.7),
            ("Wednesday", 13, 1, 2, 2.0),
            ("Wednesday", 14, 3, 5, 1.7),
            ("Wednesday", 15, 5, 5, 1.8),
            ("Wednesday", 16, 1, 2, 2.0),
            ("Wednesday", 17, 1, 2, 2.0),
            ("Wednesday", 18, 1, 2, 2.0),
            ("Wednesday", 19, 1, 5, 2.0),
            ("Wednesday", 20, 1, 2, 2.0),
            ("Wednesday", 21, 1, 2, 2.0),
            ("Wednesday", 22, 3, 5, 1.7),
            ("Wednesday", 23, 1, 2, 2.0),
            ("Wednesday", 24, 3, 5, 1.7),
            ("Wednesday", 25, 1, 5, 2.0),
            ("Wednesday", 26, 1, 2, 2.0),
            ("Wednesday", 27, 1, 2, 2.0),
            ("Wednesday", 28, 1, 5, 2.0),
            ("Wednesday", 29, 1, 2, 2.0),
            ("Wednesday", 30, 3, 5, 1.7),
            ("Wednesday", 31, 1, 5, 2.0),
            ("Wednesday", 32, 1, 2, 2.0),
            ("Wednesday", 33, 1, 5, 2.0),
            ("Wednesday", 34, 1, 5, 2.0),
            ("Wednesday", 35, 1, 5, 2.0),
            ("Thursday", 1, 1, 2, 2.0),
            ("Thursday", 2, 1, 2, 2.0),
            ("Thursday", 3, 1, 2, 2.0),
            ("Thursday", 4, 1, 2, 2.0),
            ("Thursday", 5, 1, 5, 2.0),
            ("Thursday", 6, 1, 2, 2.0),
            ("Thursday", 7, 1, 2, 2.0),
            ("Thursday", 8, 1, 2, 2.0),
            ("Thursday", 9, 1, 5, 2.0),
            ("Thursday", 10, 1, 2, 2.0),
            ("Thursday", 11, 1, 2, 2.0),
            ("Thursday", 12, 1, 5, 2.0),
            ("Thursday", 13, 1, 2, 2.0),
            ("Thursday", 14, 1, 5, 2.0),
            ("Thursday", 15, 2, 5, 1.7),
            ("Thursday", 16, 1, 2, 2.0),
            ("Thursday", 17, 1, 2, 2.0),
            ("Thursday", 18, 1, 2, 2.0),
            ("Thursday", 19, 1, 5, 2.0),
            ("Thursday", 20, 1, 2, 2.0),
            ("Thursday", 21, 1, 2, 2.0),
            ("Thursday", 22, 3, 5, 1.7),
            ("Thursday", 23, 1, 2, 2.0),
            ("Thursday", 24, 3, 5, 1.7),
            ("Thursday", 25, 3, 5, 1.7),
            ("Thursday", 26, 1, 2, 2.0),
            ("Thursday", 27, 1, 2, 2.0),
            ("Thursday", 28, 1, 5, 2.0),
            ("Thursday", 29, 1, 2, 2.0),
            ("Thursday", 30, 3, 5, 1.7),
            ("Thursday", 31, 3, 5, 1.7),
            ("Thursday", 32, 1, 2, 2.0),
            ("Thursday", 33, 1, 5, 2.0),
            ("Thursday", 34, 3, 5, 1.7),
            ("Thursday", 35, 5, 5, 1.8),
            ("Friday", 1, 1, 2, 2.0),
            ("Friday", 2, 1, 2, 2.0),
            ("Friday", 3, 1, 2, 2.0),
            ("Friday", 4, 1, 2, 2.0),
            ("Friday", 5, 2, 5, 1.7),
            ("Friday", 6, 1, 2, 2.0),
            ("Friday", 7, 1, 2, 2.0),
            ("Friday", 8, 1, 2, 2.0),
            ("Friday", 9, 3, 5, 1.7),
            ("Friday", 10, 1, 2, 2.0),
            ("Friday", 11, 1, 2, 2.0),
            ("Friday", 12, 3, 5, 1.7),
            ("Friday", 13, 1, 2, 2.0),
            ("Friday", 14, 3, 5, 1.7),
            ("Friday", 15, 5, 5, 1.8),
            ("Friday", 16, 1, 2, 2.0),
            ("Friday", 17, 1, 2, 2.0),
            ("Friday", 18, 1, 2, 2.0),
            ("Friday", 19, 3, 5, 1.7),
            ("Friday", 20, 1, 2, 2.0),
            ("Friday", 21, 1, 2, 2.0),
            ("Friday", 22, 3, 5, 1.7),
            ("Friday", 23, 1, 2, 2.0),
            ("Friday", 24, 3, 5, 1.7),
            ("Friday", 25, 3, 5, 1.7),
            ("Friday", 26, 1, 2, 2.0),
            ("Friday", 27, 1, 2, 2.0),
            ("Friday", 28, 3, 5, 1.7),
            ("Friday", 29, 1, 2, 2.0),
            ("Friday", 30, 3, 5, 1.7),
            ("Friday", 31, 3, 5, 1.7),
            ("Friday", 32, 1, 2, 2.0),
            ("Friday", 33, 3, 5, 1.7),
            ("Friday", 34, 3, 5, 1.7),
            ("Friday", 35, 5, 5, 1.8),
            ("Saturday", 1, 1, 2, 2.0),
            ("Saturday", 2, 1, 2, 2.0),
            ("Saturday", 3, 1, 2, 2.0),
            ("Saturday", 4, 1, 2, 2.0),
            ("Saturday", 5, 1, 5, 2.0),
            ("Saturday", 6, 1, 2, 2.0),
            ("Saturday", 7, 1, 2, 2.0),
            ("Saturday", 8, 1, 2, 2.0),
            ("Saturday", 9, 1, 5, 2.0),
            ("Saturday", 10, 1, 2, 2.0),
            ("Saturday", 11, 1, 2, 2.0),
            ("Saturday", 12, 1, 5, 2.0),
            ("Saturday", 13, 1, 2, 2.0),
            ("Saturday", 14, 1, 5, 2.0),
            ("Saturday", 15, 5, 5, 1.8),
            ("Saturday", 16, 1, 2, 2.0),
            ("Saturday", 17, 1, 2, 2.0),
            ("Saturday", 18, 1, 2, 2.0),
            ("Saturday", 19, 1, 5, 2.0),
            ("Saturday", 20, 1, 2, 2.0),
            ("Saturday", 21, 1, 2, 2.0),
            ("Saturday", 22, 3, 5, 1.7),
            ("Saturday", 23, 1, 2, 2.0),
            ("Saturday", 24, 3, 5, 1.7),
            ("Saturday", 25, 3, 5, 1.7),
            ("Saturday", 26, 1, 2, 2.0),
            ("Saturday", 27, 1, 2, 2.0),
            ("Saturday", 28, 1, 5, 2.0),
            ("Saturday", 29, 1, 2, 2.0),
            ("Saturday", 30, 3, 5, 1.7),
            ("Saturday", 31, 3, 5, 1.7),
            ("Saturday", 32, 1, 2, 2.0),
            ("Saturday", 33, 1, 5, 2.0),
            ("Saturday", 34, 3, 5, 1.7),
            ("Saturday", 35, 5, 5, 1.8),
            ("Sunday", 1, 1, 2, 2.0),
            ("Sunday", 2, 1, 2, 2.0),
            ("Sunday", 3, 1, 2, 2.0),
            ("Sunday", 4, 1, 2, 2.0),
            ("Sunday", 5, 5, 5, 1.8),
            ("Sunday", 6, 1, 2, 2.0),
            ("Sunday", 7, 1, 2, 2.0),
            ("Sunday", 8, 1, 2, 2.0),
            ("Sunday", 9, 3, 5, 1.7),
            ("Sunday", 10, 1, 2, 2.0),
            ("Sunday", 11, 1, 2, 2.0),
            ("Sunday", 12, 3, 5, 1.7),
            ("Sunday", 13, 1, 2, 2.0),
            ("Sunday", 14, 3, 5, 1.7),
            ("Sunday", 15, 2, 5, 1.7),
            ("Sunday", 16, 1, 2, 2.0),
            ("Sunday", 17, 1, 2, 2.0),
            ("Sunday", 18, 1, 2, 2.0),
            ("Sunday", 19, 3, 5, 1.7),
            ("Sunday", 20, 1, 2, 2.0),
            ("Sunday", 21, 1, 2, 2.0),
            ("Sunday", 22, 3, 5, 1.7),
            ("Sunday", 23, 1, 2, 2.0),
            ("Sunday", 24, 3, 5, 1.7),
            ("Sunday", 25, 1, 5, 2.0),
            ("Sunday", 26, 1, 2, 2.0),
            ("Sunday", 27, 1, 2, 2.0),
            ("Sunday", 28, 3, 5, 1.7),
            ("Sunday", 29, 1, 2, 2.0),
            ("Sunday", 30, 3, 5, 1.7),
            ("Sunday", 31, 1, 5, 2.0),
            ("Sunday", 32, 1, 2, 2.0),
            ("Sunday", 33, 3, 5, 1.7),
            ("Sunday", 34, 1, 5, 2.0),
            ("Sunday", 35, 2, 5, 1.7),
        ]

        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO ucb (game_day, potion_id, bought, shown, ucb_value)
                VALUES (:game_day, :potion_id, :bought, :shown, :ucb_value)
                """
            ),
            [
                {
                    "game_day": game_day,
                    "potion_id": potion_id,
                    "bought": bought,
                    "shown": shown,
                    "ucb_value": ucb_value,
                }
                for game_day, potion_id, bought, shown, ucb_value in ucb_rows
            ],
        )
        update_gold(connection, 100, "initial gold")

    
