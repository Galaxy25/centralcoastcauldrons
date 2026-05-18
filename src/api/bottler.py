import math

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, field_validator
from typing import List

import sqlalchemy
from src.api import auth
from src.api.helper import *
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)


class PotionMixes(BaseModel):
    potion_type: List[int] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Must contain exactly 4 elements: [r, g, b, d]",
    )
    quantity: int = Field(
        ..., ge=1, le=10000, description="Quantity must be between 1 and 10,000"
    )

    @field_validator("potion_type")
    @classmethod
    def validate_potion_type(cls, potion_type: List[int]) -> List[int]:
        if sum(potion_type) != 100:
            raise ValueError("Sum of potion_type values must be exactly 100")
        return potion_type


@router.post("/deliver/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def post_deliver_bottles(potions_delivered: List[PotionMixes], order_id: int):
    """
    Delivery of potions requested after plan. order_id is a unique value representing
    a single delivery; the call is idempotent based on the order_id.
    """
    if not potions_delivered:
        return

    red_total = sum(p.potion_type[0] * p.quantity for p in potions_delivered)
    green_total = sum(p.potion_type[1] * p.quantity for p in potions_delivered)
    blue_total = sum(p.potion_type[2] * p.quantity for p in potions_delivered)
    dark_total = sum(p.potion_type[3] * p.quantity for p in potions_delivered)

    with db.engine.begin() as connection:
        transaction_id = (
            connection.execute(
                sqlalchemy.text(
                    "INSERT INTO transactions (description) VALUES (:message) RETURNING id"
                ),
                {"message": f"Bottle delivery for order: {order_id}"},
            )
            .one()
            .id
        )

        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO ml_history
                    (transaction_id, red_ml_change, green_ml_change, blue_ml_change, dark_ml_change)
                VALUES (:transaction_id, :red, :green, :blue, :dark)
                """
            ),
            {
                "transaction_id": transaction_id,
                "red": -red_total,
                "green": -green_total,
                "blue": -blue_total,
                "dark": -dark_total,
            },
        )
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE global_inventory
                SET red_ml = red_ml - :red,
                    green_ml = green_ml - :green,
                    blue_ml = blue_ml - :blue,
                    dark_ml = dark_ml - :dark
                """
            ),
            {
                "red": red_total,
                "green": green_total,
                "blue": blue_total,
                "dark": dark_total,
            },
        )

        inventory_rows = connection.execute(
            sqlalchemy.text(
                "SELECT id, red_ml, green_ml, blue_ml, dark_ml FROM potion_inventory"
            )
        ).all()
        key_id = {
            (r.red_ml, r.green_ml, r.blue_ml, r.dark_ml): r.id for r in inventory_rows
        }

        potion_rows = [
            {
                "tid": transaction_id,
                "pid": key_id[
                    (
                        p.potion_type[0],
                        p.potion_type[1],
                        p.potion_type[2],
                        p.potion_type[3],
                    )
                ],
                "qty": p.quantity,
            }
            for p in potions_delivered
        ]

        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO potion_history (transaction_id, potion_id, change)
                VALUES (:tid, :pid, :qty)
                """
            ),
            potion_rows,
        )
        connection.execute(
            sqlalchemy.text(
                "UPDATE potion_inventory SET quantity = quantity + :qty WHERE id = :pid"
            ),
            potion_rows,
        )


def create_bottle_plan(
    connection,
    red_ml: int,
    green_ml: int,
    blue_ml: int,
    dark_ml: int,
    maximum_potion_capacity: int,
    current_potion_inventory: List[PotionMixes],
) -> List[PotionMixes]:
    mixes = []
    remaining_slots = maximum_potion_capacity
    remaining_slots -= sum([potion.quantity for potion in current_potion_inventory])
    per_potion_type_limit = max(10, math.ceil(maximum_potion_capacity / 36))
    current_quantities = {
        tuple(potion.potion_type): potion.quantity
        for potion in current_potion_inventory
    }
    rows = connection.execute(
        sqlalchemy.text(
            """
            SELECT
                red_ml,
                green_ml,
                blue_ml,
                dark_ml
            FROM potion_inventory
            """
        )
    ).all()
    for p in rows:
        # Calculated the most possible potion of specific type that can be made.
        most_possible = maximum_potion_capacity
        if p.red_ml != 0:
            most_possible = min(most_possible, red_ml // p.red_ml)
        if p.green_ml != 0:
            most_possible = min(most_possible, green_ml // p.green_ml)
        if p.blue_ml != 0:
            most_possible = min(most_possible, blue_ml // p.blue_ml)
        if p.dark_ml != 0:
            most_possible = min(most_possible, dark_ml // p.dark_ml)
        potion_type = [p.red_ml, p.green_ml, p.blue_ml, p.dark_ml]
        existing_quantity = current_quantities.get(tuple(potion_type), 0)
        most_possible = min(most_possible, per_potion_type_limit - existing_quantity)
        most_possible = min(most_possible, remaining_slots)
        if most_possible <= 0:
            continue
        red_ml -= most_possible * p.red_ml
        green_ml -= most_possible * p.green_ml
        blue_ml -= most_possible * p.blue_ml
        dark_ml -= most_possible * p.dark_ml
        remaining_slots -= most_possible
        mixes.append(PotionMixes(potion_type=potion_type, quantity=most_possible))
    return mixes


@router.post("/plan", response_model=List[PotionMixes])
def get_bottle_plan():
    """
    Gets the plan for bottling potions.
    Each bottle has a quantity of what proportion of red, green, blue, and dark potions to add.
    Colors are expressed in integers from 0 to 100 that must sum up to exactly 100.
    """

    with db.engine.begin() as connection:
        ml = get_ml_total(connection)
        potions = get_all_potions(connection)
        capacity = get_capacity(connection)

        mixes = []
        for p in potions:
            mixes.append(
                PotionMixes(
                    potion_type=[p.red_ml, p.green_ml, p.blue_ml, p.dark_ml],
                    quantity=p.quantity,
                )
            )

        return create_bottle_plan(
            connection,
            red_ml=ml.red_ml,
            green_ml=ml.green_ml,
            blue_ml=ml.blue_ml,
            dark_ml=ml.dark_ml,
            maximum_potion_capacity=capacity.potion_capacity * 50,
            current_potion_inventory=mixes,
        )
