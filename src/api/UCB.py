import math

import sqlalchemy


def _calculate_ucb_value(bought: int, shown: int) -> float:
    safe_shown = max(shown, 1)
    exploitation = bought / safe_shown
    exploration = math.sqrt((2.0 * math.log(safe_shown + 1)) / safe_shown)
    return exploitation + exploration


def _is_25_color_off(potion, purchased_potion) -> bool:
    return (
        abs(potion.red_ml - purchased_potion.red_ml) == 25
        or abs(potion.green_ml - purchased_potion.green_ml) == 25
        or abs(potion.blue_ml - purchased_potion.blue_ml) == 25
        or abs(potion.dark_ml - purchased_potion.dark_ml) == 25
    )


def _check_ucb(connection, character_class: str, potion_id: int) -> bool:
    return (
        connection.execute(
            sqlalchemy.text(
                """
                SELECT 1
                FROM ucb
                WHERE character_class = :character_class AND potion_id = :potion_id
                """
            ),
            {"character_class": character_class, "potion_id": potion_id},
        ).one_or_none()
        is not None
    )


def seed_ucb_for_class(connection, character_class: str, potion_id: int) -> None:
    purchased_potion = connection.execute(
        sqlalchemy.text(
            """
            SELECT id, red_ml, green_ml, blue_ml, dark_ml
            FROM potion_inventory
            WHERE id = :potion_id
            """
        ),
        {"potion_id": potion_id},
    ).one_or_none()
    if purchased_potion is None:
        return

    potions = connection.execute(
        sqlalchemy.text(
            """
            SELECT id, red_ml, green_ml, blue_ml, dark_ml
            FROM potion_inventory
            ORDER BY id ASC
            """
        )
    ).all()

    rows = []
    for potion in potions:
        shown = 5
        if potion.id == potion_id:
            bought = 3
        elif _is_25_color_off(potion, purchased_potion):
            bought = 2
        else:
            bought = 0

        rows.append(
            {
                "character_class": character_class,
                "potion_id": potion.id,
                "bought": bought,
                "shown": shown,
                "ucb_value": _calculate_ucb_value(bought, shown),
            }
        )

    connection.execute(
        sqlalchemy.text(
            """
            INSERT INTO ucb (character_class, potion_id, bought, shown, ucb_value)
            VALUES (:character_class, :potion_id, :bought, :shown, :ucb_value)
            """
        ),
        rows,
    )


def update_ucb(connection, character_class: str, potion_id: int):
    row = connection.execute(
        sqlalchemy.text(
            """
            SELECT bought, shown
            FROM ucb
            WHERE character_class = :character_class AND potion_id = :potion_id
            """
        ),
        {"character_class": character_class, "potion_id": potion_id},
    ).one_or_none()

    if row is None:
        return

    ucb_value = _calculate_ucb_value(row.bought, row.shown)

    connection.execute(
        sqlalchemy.text(
            """
            UPDATE ucb
            SET ucb_value = :ucb_value
            WHERE character_class = :character_class AND potion_id = :potion_id
            """
        ),
        {
            "character_class": character_class,
            "potion_id": potion_id,
            "ucb_value": ucb_value,
        },
    )


def increment_shown(connection, character_class: str, potion_id: int, amount: int = 1):
    connection.execute(
        sqlalchemy.text(
            """
            UPDATE ucb
            SET shown = shown + :amount
            WHERE character_class = :character_class AND potion_id = :potion_id
            """
        ),
        {
            "character_class": character_class,
            "potion_id": potion_id,
            "amount": amount,
        },
    )


def increment_bought(connection, character_class: str, potion_id: int, amount: int = 1):
    connection.execute(
        sqlalchemy.text(
            """
            UPDATE ucb
            SET bought = bought + :amount
            WHERE character_class = :character_class AND potion_id = :potion_id
            """
        ),
        {
            "character_class": character_class,
            "potion_id": potion_id,
            "amount": amount,
        },
    )


def ucb_sorted(connection, character_class: str):
    rows = connection.execute(
        sqlalchemy.text(
            """
            SELECT
                potion_inventory.id,
                potion_inventory.quantity
            FROM potion_inventory
            JOIN ucb
                ON potion_inventory.id = ucb.potion_id
               AND ucb.character_class = :character_class
            WHERE potion_inventory.quantity > 0
            GROUP BY potion_inventory.id, potion_inventory.quantity, potion_inventory.item_sku, ucb.ucb_value
            ORDER BY ucb.ucb_value DESC;
            """
        ),
        {"character_class": character_class},
    ).all()
    return rows
