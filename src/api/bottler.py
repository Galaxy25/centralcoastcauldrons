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
    print(f"potions delivered: {potions_delivered} order_id: {order_id}")

    for potion in potions_delivered:
        update_ml(-potion.potion_type[0] * potion.quantity,
                  -potion.potion_type[1] * potion.quantity,
                  -potion.potion_type[2] * potion.quantity,
                  -potion.potion_type[3] * potion.quantity,
                  message=f"Bottle delivery for order: {order_id}, potion type: {potion.potion_type}, quantity: {potion.quantity}")
        potion_sku = f"R{potion.potion_type[0]}G{potion.potion_type[1]}B{potion.potion_type[2]}D{potion.potion_type[3]}"
        potion_id = get_potion_id(potion_sku)
        update_potions(potion_id, potion.quantity, message=f"Bottle delivery for order: {order_id}, potion type: {potion.potion_type}, quantity: {potion.quantity}")

    pass


def create_bottle_plan(
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
    with db.engine.begin() as connection:
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
        most_possible = get_capacity().potion_capacity*50
        if p.red_ml != 0:
            most_possible = min(most_possible, red_ml // p.red_ml)
        if p.green_ml != 0:
            most_possible = min(most_possible, green_ml // p.green_ml)
        if p.blue_ml != 0:
            most_possible = min(most_possible, blue_ml // p.blue_ml)
        if p.dark_ml != 0:
            most_possible = min(most_possible, dark_ml // p.dark_ml)
        most_possible = min(most_possible, remaining_slots)
        if most_possible == 0:
            continue
        red_ml -= most_possible * p.red_ml
        green_ml -= most_possible * p.green_ml
        blue_ml -= most_possible * p.blue_ml
        dark_ml -= most_possible * p.dark_ml
        remaining_slots -= most_possible
        mixes.append(PotionMixes(
            potion_type=[p.red_ml, p.green_ml, p.blue_ml, p.dark_ml], 
            quantity=most_possible))
    return mixes


@router.post("/plan", response_model=List[PotionMixes])
def get_bottle_plan():
    """
    Gets the plan for bottling potions.
    Each bottle has a quantity of what proportion of red, green, blue, and dark potions to add.
    Colors are expressed in integers from 0 to 100 that must sum up to exactly 100.
    """

    ml = get_ml_total()
    mixes = []
    potions = get_all_potions()
    for p in potions:
        mixes.append(PotionMixes(potion_type=[p.red_ml, p.green_ml, p.blue_ml, p.dark_ml], quantity=p.quantity))

    return create_bottle_plan(
        red_ml=ml.red_ml,
        green_ml=ml.green_ml,
        blue_ml=ml.blue_ml,
        dark_ml=ml.dark_ml,
        maximum_potion_capacity=get_capacity().potion_capacity*50,
        current_potion_inventory=mixes
    )


if __name__ == "__main__":
    print(get_bottle_plan())
