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
                SELECT COALESCE(SUM(change), 0) AS total_gold
                FROM gold_history;
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

def get_ml_total() -> Any:
    """
    Return total ml inventory as seperate colors
    """
    with db.engine.begin() as connection:
        row = connection.execute(
            sqlalchemy.text(
                """
                SELECT
                    COALESCE(SUM(red_ml_change), 0) AS red_ml,
                    COALESCE(SUM(green_ml_change), 0) AS green_ml,
                    COALESCE(SUM(blue_ml_change), 0) AS blue_ml,
                    COALESCE(SUM(dark_ml_change), 0) AS dark_ml
                FROM ml_history;
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



def get_potion(id: int) -> int:
    with db.engine.begin() as connection:
        row = connection.execute(
            sqlalchemy.text(
                """
                SELECT COALESCE(SUM(change), 0) AS potion_count
                FROM potion_history
                WHERE potion_id = :id;
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

def get_all_potions():
    """
    Return potion_id, quantity, and sku for quantity > 0
    """
    with db.engine.begin() as connection:
        rows = connection.execute(
            sqlalchemy.text(
                """
                SELECT
                    potion_inventory.id,
                    COALESCE(SUM(potion_history.change), 0) AS quantity,
                    potion_inventory.item_sku
                FROM potion_inventory
                JOIN potion_history ON potion_inventory.id = potion_history.potion_id
                GROUP BY potion_inventory.id
                HAVING COALESCE(SUM(potion_history.change), 0) > 0
                ORDER BY potion_inventory.id ASC;
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


