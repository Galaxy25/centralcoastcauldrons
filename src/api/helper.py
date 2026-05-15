from typing import Any
import sqlalchemy

POTION_PRICE = 40


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


def get_potions_by_ucb(connection, game_day: str):
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
               AND ucb.game_day = :game_day
            WHERE potion_inventory.quantity > 0
            ORDER BY ucb.ucb_value DESC, potion_inventory.id ASC
            """
        ),
        {"game_day": game_day},
    ).all()


def get_capacity(connection):
    return connection.execute(
        sqlalchemy.text("SELECT potion_capacity, barrel_capacity FROM capacity_config")
    ).one()
