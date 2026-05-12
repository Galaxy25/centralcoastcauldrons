import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import sqlalchemy

from src import database as db

REAL_TZ = ZoneInfo("America/Los_Angeles")
GAME_DAY_OFFSET = timedelta(hours=18)


def get_game_day() -> str:
    return (datetime.now(REAL_TZ) + GAME_DAY_OFFSET).strftime("%A")


def _calculate_ucb_value(bought: int, shown: int) -> float:
    exploitation = bought / shown
    exploration = math.sqrt((2.0 * math.log(shown + 1)) / bought)
    return exploitation + exploration


def update_ucb(potion_id: int):
    with db.engine.begin() as connection:
        game_day = get_game_day()
        row = connection.execute(
            sqlalchemy.text(
                """
                SELECT bought, shown
                FROM ucb
                WHERE game_day = :game_day AND potion_id = :potion_id
                """
            ),
            {"game_day": game_day, "potion_id": potion_id},
        ).one_or_none()

        if row is None:
            return

        bought = max(row.bought, 1)
        shown = max(row.shown, 1)
        ucb_value = _calculate_ucb_value(bought, shown)

        connection.execute(
            sqlalchemy.text(
                """
                UPDATE ucb
                SET ucb_value = :ucb_value
                WHERE game_day = :game_day AND potion_id = :potion_id
                """
            ),
            {"game_day": game_day, "potion_id": potion_id, "ucb_value": ucb_value},
        )


def increment_shown(potion_id: int):
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE ucb
                SET shown = shown + 1
                WHERE game_day = :game_day AND potion_id = :potion_id
                """
            ),
            {"game_day": get_game_day(), "potion_id": potion_id},
        )


def increment_bought(potion_id: int):
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE ucb
                SET bought = bought + 1
                WHERE game_day = :game_day AND potion_id = :potion_id
                """
            ),
            {"game_day": get_game_day(), "potion_id": potion_id},
        )


def ucb_sorted():
    with db.engine.begin() as connection:
        rows = connection.execute(
            sqlalchemy.text(
                """
                SELECT
                    potion_inventory.id,
                    potion_inventory.quantity
                FROM potion_inventory
                JOIN ucb
                    ON potion_inventory.id = ucb.potion_id
                   AND ucb.game_day = :game_day
                WHERE potion_inventory.quantity > 0
                GROUP BY potion_inventory.id, potion_inventory.quantity, potion_inventory.item_sku, ucb.ucb_value
                ORDER BY ucb.ucb_value DESC;
                """
            ),
            {"game_day": get_game_day()},
        ).all()
    return rows
