import random
from typing import Any
import sqlalchemy

POTION_PRICE = 30


def add_customer_seen(
    connection,
    visit_id: int,
    customer_id: str,
    customer_name: str,
    character_class: str,
    character_species: str,
    level: int,
) -> None:
    connection.execute(
        sqlalchemy.text(
            """
            INSERT INTO customer_seen (visit_id, customer_id, customer_name, character_class, character_species, level)
            VALUES (:visit_id, :customer_id, :customer_name, :character_class, :character_species, :level)
            """
        ),
        {
            "visit_id": visit_id,
            "customer_id": customer_id,
            "customer_name": customer_name,
            "character_class": character_class,
            "character_species": character_species,
            "level": level,
        },
    )


def get_gold_total(connection) -> int:
    return connection.execute(
        sqlalchemy.text("SELECT gold AS total_gold FROM global_inventory")
    ).one().total_gold


def update_gold(connection, value: int, message: str = "gold change") -> None:
    transaction_id = connection.execute(
        sqlalchemy.text("INSERT INTO transactions (description) VALUES (:message) RETURNING id"),
        {"message": message}
    ).one().id
    connection.execute(
        sqlalchemy.text("INSERT INTO gold_history (transaction_id, \"change\") VALUES (:transaction_id, :value)"),
        {"transaction_id": transaction_id, "value": value}
    )
    connection.execute(
        sqlalchemy.text("UPDATE global_inventory SET gold = gold + :value"),
        {"value": value}
    )


def get_ml_total(connection) -> Any:
    return connection.execute(
        sqlalchemy.text("SELECT red_ml, green_ml, blue_ml, dark_ml FROM global_inventory")
    ).one()


def update_ml(connection, red_ml: int = 0, green_ml: int = 0,
              blue_ml: int = 0, dark_ml: int = 0,
              message: str = "ml change") -> None:
    transaction_id = connection.execute(
        sqlalchemy.text("INSERT INTO transactions (description) VALUES (:message) RETURNING id"),
        {"message": message}
    ).one().id
    connection.execute(
        sqlalchemy.text(
            """
            INSERT INTO ml_history (transaction_id, red_ml_change, green_ml_change, blue_ml_change, dark_ml_change)
            VALUES (:transaction_id, :red_change, :green_change, :blue_change, :dark_change)
            """
        ),
        {"transaction_id": transaction_id, "red_change": red_ml, "green_change": green_ml,
         "blue_change": blue_ml, "dark_change": dark_ml}
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
        {"red_change": red_ml, "green_change": green_ml, "blue_change": blue_ml, "dark_change": dark_ml}
    )


def get_potion(connection, id: int) -> int:
    return connection.execute(
        sqlalchemy.text("SELECT quantity AS potion_count FROM potion_inventory WHERE id = :id"),
        {"id": id}
    ).one().potion_count


def get_potion_id(connection, sku: str):
    return connection.execute(
        sqlalchemy.text("SELECT id FROM potion_inventory WHERE item_sku = :sku"),
        {"sku": sku}
    ).one().id


def update_potions(connection, id: int, count: int, message: str = "potion change"):
    transaction_id = connection.execute(
        sqlalchemy.text("INSERT INTO transactions (description) VALUES (:message) RETURNING id"),
        {"message": message}
    ).one().id
    connection.execute(
        sqlalchemy.text(
            "INSERT INTO potion_history (transaction_id, potion_id, change) VALUES (:transaction_id, :id, :count)"
        ),
        {"transaction_id": transaction_id, "id": id, "count": count}
    )
    connection.execute(
        sqlalchemy.text("UPDATE potion_inventory SET quantity = quantity + :count WHERE id = :id"),
        {"id": id, "count": count}
    )


def get_all_potions(connection):
    return connection.execute(
        sqlalchemy.text(
            """
            SELECT id, red_ml, green_ml, blue_ml, dark_ml, price, item_sku, name, quantity
            FROM potion_inventory
            WHERE quantity > 0
            ORDER BY id ASC
            """
        )
    ).all()


def get_recent_customer_classes(connection, limit: int = 6):
    return connection.execute(
        sqlalchemy.text(
            """
            SELECT character_class
            FROM (
                SELECT character_class, MIN(id) AS first_seen_id
                FROM customer_seen
                WHERE visit_id = (
                    SELECT MAX(visit_id)
                    FROM customer_seen
                )
                GROUP BY character_class
            ) latest_classes
            ORDER BY first_seen_id ASC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).all()


def get_random_potions(connection, limit: int, excluded_ids: set[int] | None = None):
    if limit <= 0:
        return []

    excluded_ids = excluded_ids or set()
    potions = get_all_potions(connection)
    available_potions = [potion for potion in potions if potion.id not in excluded_ids]
    return random.sample(available_potions, min(limit, len(available_potions)))


def get_potions_by_ucb(connection, character_class: str):
    return connection.execute(
        sqlalchemy.text(
            """
            SELECT
                potion_inventory.id,
                potion_inventory.red_ml,
                potion_inventory.green_ml,
                potion_inventory.blue_ml,
                potion_inventory.dark_ml,
                potion_inventory.price,
                potion_inventory.item_sku,
                potion_inventory.name,
                potion_inventory.quantity
            FROM potion_inventory
            JOIN ucb
                ON potion_inventory.id = ucb.potion_id
               AND ucb.character_class = :character_class
            WHERE potion_inventory.quantity > 0
            ORDER BY ucb.ucb_value DESC, potion_inventory.id ASC
            """
        ),
        {"character_class": character_class},
    ).all()


def get_cart_customer_class(connection, cart_id: int) -> str:
    return connection.execute(
        sqlalchemy.text(
            """
            SELECT customer_class
            FROM cart_checkout
            WHERE id = :cart_id
            """
        ),
        {"cart_id": cart_id},
    ).one().customer_class


def get_capacity(connection):
    return connection.execute(
        sqlalchemy.text("SELECT potion_capacity, barrel_capacity FROM capacity_config")
    ).one()
