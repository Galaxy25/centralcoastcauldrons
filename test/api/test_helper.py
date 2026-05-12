from src.api.admin import reset
from src.api.catalog import get_catalog
from src.api.helper import *
from src.api.UCB import get_game_day, increment_bought
from src import database as db
import sqlalchemy

def test_gold_history() -> None:
    reset()
    update_gold(100, "test gold change")
    assert get_gold_total() == 200
    update_gold(550, "test gold change")
    assert get_gold_total() == 750
    update_gold(-750, "test gold change")
    assert get_gold_total() == 0

def test_ml_history() -> None:
    reset()
    update_ml(red_ml=100)
    ml_total = get_ml_total()
    assert ml_total.red_ml == 100
    assert ml_total.green_ml == 0
    assert ml_total.blue_ml == 0
    assert ml_total.dark_ml == 0

    update_ml(green_ml=200, blue_ml=250, dark_ml=300)
    ml_total = get_ml_total()
    assert ml_total.red_ml == 100
    assert ml_total.green_ml == 200
    assert ml_total.blue_ml == 250
    assert ml_total.dark_ml == 300
    
    update_ml(red_ml=-100, green_ml=-100, blue_ml=-100, dark_ml=-100)
    ml_total = get_ml_total()
    assert ml_total.red_ml == 0
    assert ml_total.green_ml == 100
    assert ml_total.blue_ml == 150
    assert ml_total.dark_ml == 200

def test_potion_history() -> None:
    reset()
    update_potions(1, 10)
    assert get_potion(1) == 10
    update_potions(1, 20)
    assert get_potion(1) == 30
    update_potions(1, -10)
    assert get_potion(1) == 20
    potions = get_all_potions()
    assert potions[0].quantity == 20
    assert len(potions) == 1

    update_potions(2, 1)
    update_potions(3, 1)
    update_potions(4, 5)
    potions = get_all_potions()
    assert len(potions) == 4
    print(potions)
    assert potions[0].quantity == 20
    assert potions[1].quantity == 1
    assert potions[2].quantity == 1
    assert potions[3].quantity == 5


def test_reset_seeds_ucb_by_game_day() -> None:
    reset()

    with db.engine.begin() as connection:
        ucb_count = connection.execute(
            sqlalchemy.text("SELECT COUNT(*) FROM ucb")
        ).scalar_one()
        pure_blue_tuesday = connection.execute(
            sqlalchemy.text(
                """
                SELECT bought, shown
                FROM ucb
                JOIN potion_inventory ON potion_inventory.id = ucb.potion_id
                WHERE ucb.game_day = 'Tuesday'
                  AND potion_inventory.item_sku = 'R0G0B100D0'
                """
            )
        ).one()
        pure_red_thursday = connection.execute(
            sqlalchemy.text(
                """
                SELECT bought, shown
                FROM ucb
                JOIN potion_inventory ON potion_inventory.id = ucb.potion_id
                WHERE ucb.game_day = 'Thursday'
                  AND potion_inventory.item_sku = 'R100G0B0D0'
                """
            )
        ).one()
        red_green_saturday = connection.execute(
            sqlalchemy.text(
                """
                SELECT bought, shown
                FROM ucb
                JOIN potion_inventory ON potion_inventory.id = ucb.potion_id
                WHERE ucb.game_day = 'Saturday'
                  AND potion_inventory.item_sku = 'R50G50B0D0'
                """
            )
        ).one()
        red_green_sunday = connection.execute(
            sqlalchemy.text(
                """
                SELECT bought, shown
                FROM ucb
                JOIN potion_inventory ON potion_inventory.id = ucb.potion_id
                WHERE ucb.game_day = 'Sunday'
                  AND potion_inventory.item_sku = 'R50G50B0D0'
                """
            )
        ).one()
        dark_potion = connection.execute(
            sqlalchemy.text(
                """
                SELECT bought, shown
                FROM ucb
                JOIN potion_inventory ON potion_inventory.id = ucb.potion_id
                WHERE ucb.game_day = 'Sunday'
                  AND potion_inventory.item_sku = 'R0G0B0D100'
                """
            )
        ).one()

    assert ucb_count == 245
    assert pure_blue_tuesday == (5, 5)
    assert pure_red_thursday == (5, 5)
    assert red_green_saturday == (3, 5)
    assert red_green_sunday == (1, 5)
    assert dark_potion == (1, 2)


def test_catalog_increments_shown_for_visible_potions() -> None:
    reset()
    for potion_id in range(1, 8):
        update_potions(potion_id, 1)

    game_day = get_game_day()
    with db.engine.begin() as connection:
        before_visible = connection.execute(
            sqlalchemy.text(
                """
                SELECT potion_id, shown
                FROM ucb
                WHERE game_day = :game_day
                  AND potion_id BETWEEN 1 AND 7
                ORDER BY potion_id
                """
            ),
            {"game_day": game_day},
        ).all()

    catalog = get_catalog()

    with db.engine.begin() as connection:
        after_visible = connection.execute(
            sqlalchemy.text(
                """
                SELECT potion_id, shown
                FROM ucb
                WHERE game_day = :game_day
                  AND potion_id BETWEEN 1 AND 7
                ORDER BY potion_id
                """
            ),
            {"game_day": game_day},
        ).all()

    assert len(catalog) == 6
    assert [row.shown for row in after_visible[:6]] == [row.shown + 1 for row in before_visible[:6]]
    assert after_visible[6].shown == before_visible[6].shown


def test_increment_bought_updates_ucb_counter() -> None:
    reset()
    game_day = get_game_day()

    with db.engine.begin() as connection:
        before_bought = connection.execute(
            sqlalchemy.text(
                """
                SELECT bought
                FROM ucb
                WHERE game_day = :game_day
                  AND potion_id = 5
                """
            ),
            {"game_day": game_day},
        ).scalar_one()

    increment_bought(5)

    with db.engine.begin() as connection:
        after_bought = connection.execute(
            sqlalchemy.text(
                """
                SELECT bought
                FROM ucb
                WHERE game_day = :game_day
                  AND potion_id = 5
                """
            ),
            {"game_day": game_day},
        ).scalar_one()

    assert after_bought == before_bought + 1

