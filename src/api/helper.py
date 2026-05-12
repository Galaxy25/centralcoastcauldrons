from typing import Any
from src import database as db
import sqlalchemy

def get_gold_total() -> int:
    """
    Return total gold
    """

    with db.engine.begin() as connection:
        row = connection.execute(
            sqlalchemy.text(
                """
                SELECT gold AS total_gold
                FROM global_inventory
                """
            )
        ).one()
    return row.total_gold

def update_gold(value: int, message: str = "gold change") -> None:
    """
    Add update gold history and transaction
    """
    with db.engine.begin() as connection:
        transaction_id = connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO transactions (description)
                VALUES (:message)
                RETURNING id
                """
            ),
            {"message": message}
        ).one().id
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO gold_history (transaction_id, "change")
                VALUES (:transaction_id, :value)
                """
            ),
            {"transaction_id": transaction_id, "value": value}
        )
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory
                SET gold = gold + :value
                """
            ),
            {"value": value},
        )

def get_ml_total() -> Any:
    """
    Return total ml inventory as seperate colors
    """
    with db.engine.begin() as connection:
        row = connection.execute(
            sqlalchemy.text(
                """
                SELECT
                    red_ml,
                    green_ml,
                    blue_ml,
                    dark_ml
                FROM global_inventory
                """
            )
        ).one()
    return row

def update_ml(red_ml: int = 0, green_ml: int = 0, 
              blue_ml: int = 0, dark_ml: int = 0, 
              message: str = "ml change") -> None:
    """
    Add update ml history and transaction
    """
    with db.engine.begin() as connection:
        transaction_id = connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO transactions (description)
                VALUES (:message)
                RETURNING id
                """
            ),
            {"message": message}
        ).one().id
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO ml_history (transaction_id, red_ml_change, green_ml_change, blue_ml_change, dark_ml_change)
                VALUES (:transaction_id, :red_change, :green_change, :blue_change, :dark_change)
                """
            ),
            {
                "transaction_id": transaction_id,
                "red_change": red_ml,
                "green_change": green_ml,
                "blue_change": blue_ml,
                "dark_change": dark_ml,
            }
        )
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory
                SET red_ml = red_ml + :red_change,
                    green_ml = green_ml + :green_change,
                    blue_ml = blue_ml + :blue_change,
                    dark_ml = dark_ml + :dark_change
                """
            ),
            {
                "red_change": red_ml,
                "green_change": green_ml,
                "blue_change": blue_ml,
                "dark_change": dark_ml,
            },
        )



def get_potion(id: int) -> int:
    with db.engine.begin() as connection:
        row = connection.execute(
            sqlalchemy.text(
                """
                SELECT quantity AS potion_count
                FROM potion_inventory
                WHERE id = :id;
                """
            ), {"id" : id}
        ).one()
    return row.potion_count

def get_potion_id(sku: str):
    with db.engine.begin() as connection:
        row = connection.execute(
            sqlalchemy.text(
                """
                SELECT id
                FROM potion_inventory
                WHERE item_sku = :sku;
                """
            ), {"sku" : sku}
        ).one()
    return row.id


def update_potions(id: int, count: int, message: str = "potion change"):
    """
    Updates count of the potion with specific id.
    """
    with db.engine.begin() as connection:
        transaction_id = connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO transactions (description)
                VALUES (:message)
                RETURNING id
                """
            ), {"message": message}
        ).one().id
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO potion_history (transaction_id, potion_id, change)
                VALUES (:transaction_id, :id, :count)
                """
            ), {"transaction_id": transaction_id, "id": id, "count": count}
        )
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE potion_inventory
                SET quantity = quantity + :count
                WHERE id = :id
                """
            ),
            {"id": id, "count": count},
        )

def get_all_potions():
    """
    Return potion_id, quantity, and sku for quantity > 0
    """
    with db.engine.begin() as connection:
        rows = connection.execute(
            sqlalchemy.text(
                """
                SELECT
                    id,
                    red_ml,
                    green_ml,
                    blue_ml,
                    dark_ml,
                    price,
                    item_sku,
                    name,
                    quantity
                FROM potion_inventory
                WHERE quantity > 0
                ORDER BY id ASC;
                """
            )
        ).all()
    return rows

def get_capacity():
    with db.engine.begin() as connection:
        capacity = connection.execute(
            sqlalchemy.text(
                """
                SELECT potion_capacity, barrel_capacity
                FROM capacity_config
                """
            )
        ).one()
    return capacity


