import math
import sqlalchemy
from src import database as db


def update_ucb(customer_id: str, potion_id: int):
	with db.engine.begin() as connection:
		row = connection.execute(
			sqlalchemy.text(
				"""
				SELECT COALESCE(bought, 0) AS bought, COALESCE(shown, 0) AS shown
				FROM ucb
				WHERE customer_id = :customer_id AND potion_id = :potion_id
				"""
			),
			{"customer_id": customer_id, "potion_id": potion_id},
		).one()

		if row is None:
			ucb = 1000.0
		else:
			explotation = row.bought / (row.shown + 0.001)
			exploration = math.sqrt((2.0 * math.log(row.shown)) / row.bought)
			ucb = explotation + exploration

		connection.execute(
			sqlalchemy.text(
				"""
				UPDATE ucb
				SET ucb_value = :ucb_value
				WHERE customer_id = :customer_id AND potion_id = :potion_id
				"""
			),
			{"customer_id": customer_id, "potion_id": potion_id, "ucb_value": ucb},
		)

def increment_shown(customer_id: str, potion_id: int):
	with db.engine.begin() as connection:
		connection.execute(
			sqlalchemy.text(
				"""
				UPDATE ucb
				SET shown = COALESCE(shown, 0) + 1
				WHERE customer_id = :customer_id AND potion_id = :potion_id
				"""
			),
			{"customer_id": customer_id, "potion_id": potion_id},
		)

def increment_bought(customer_id: str, potion_id: int) :
	with db.engine.begin() as connection:
		connection.execute(
			sqlalchemy.text(
				"""
				UPDATE ucb
				SET bought = COALESCE(bought, 0) + 1
				WHERE customer_id = :customer_id AND potion_id = :potion_id
				"""
			),
			{"customer_id": customer_id, "potion_id": potion_id},
		)


def ucb_sorted(customer_id: str):
	with db.engine.begin() as connection:
		rows = connection.execute(
			sqlalchemy.text(
				"""
				SELECT
					potion_inventory.id,
					COALESCE(SUM(potion_history.change), 0) AS quantity
				FROM potion_inventory
				JOIN potion_history ON potion_inventory.id = potion_history.potion_id
				LEFT JOIN ucb ON potion_inventory.id = ucb.potion_id AND ucb.customer_id = :customer_id
				GROUP BY potion_inventory.id, potion_inventory.item_sku, ucb.ucb_value
				HAVING COALESCE(SUM(potion_history.change), 0) > 0
				ORDER BY COALESCE(ucb.ucb_value, 1000) DESC;
				"""
			),
			{"customer_id": customer_id},
		).all()
	return rows

