from dataclasses import dataclass
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field, field_validator
from typing import List

from src.api import auth
from src.api.helper import *
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)


class Barrel(BaseModel):
    sku: str
    ml_per_barrel: int = Field(gt=0, description="Must be greater than 0")
    potion_type: List[float] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Must contain exactly 4 elements: [r, g, b, d] that sum to 1.0",
    )
    price: int = Field(ge=0, description="Price must be non-negative")
    quantity: int = Field(ge=0, description="Quantity must be non-negative")

    @field_validator("potion_type")
    @classmethod
    def validate_potion_type(cls, potion_type: List[float]) -> List[float]:
        if len(potion_type) != 4:
            raise ValueError("potion_type must have exactly 4 elements: [r, g, b, d]")
        if not abs(sum(potion_type) - 1.0) < 1e-6:
            raise ValueError("Sum of potion_type values must be exactly 1.0")
        return potion_type


class BarrelOrder(BaseModel):
    sku: str
    quantity: int = Field(gt=0, description="Quantity must be greater than 0")


@dataclass
class BarrelSummary:
    gold_paid: int


def calculate_barrel_summary(barrels: List[Barrel]) -> BarrelSummary:
    return BarrelSummary(gold_paid=sum(b.price * b.quantity for b in barrels))


@router.post("/deliver/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def post_deliver_barrels(barrels_delivered: List[Barrel], order_id: int):
    """
    Processes barrels delivered based on the provided order_id. order_id is a unique value representing
    a single delivery; the call is idempotent based on the order_id.
    """
    print(f"barrels delivered: {barrels_delivered} order_id: {order_id}")
    ml_options = ("red_ml", "green_ml", "blue_ml", "dark_ml")

    delivery = calculate_barrel_summary(barrels_delivered)
    update_gold(-delivery.gold_paid, f"Barrel delivery for order: {order_id}, gold paid: {delivery.gold_paid}  s")


    for barrel in barrels_delivered:
        ml =  barrel.ml_per_barrel * barrel.quantity

        highest_type = max(barrel.potion_type)
        select = barrel.potion_type.index(highest_type)

        mlType = ml_options[select]
        update_ml(**{mlType: ml}, message=f"Barrel delivery for order: {order_id}, {mlType} {ml}")

    pass


def create_barrel_plan(
    gold: int,
    max_barrel_capacity: int,
    current_red_ml: int,
    current_green_ml: int,
    current_blue_ml: int,
    current_dark_ml: int,
    wholesale_catalog: List[Barrel],
) -> List[BarrelOrder]:
    print(
        f"gold: {gold}, max_barrel_capacity: {max_barrel_capacity}, current_red_ml: {current_red_ml}, current_green_ml: {current_green_ml}, current_blue_ml: {current_blue_ml}, current_dark_ml: {current_dark_ml}, wholesale_catalog: {wholesale_catalog}"
    )

    total_spend = 0
    temp_ml_storage = [current_red_ml, current_green_ml, current_blue_ml, current_dark_ml]
    bought_barrels = []
    max_barrel_capacity = max_barrel_capacity // 4
    for barrel in sorted(wholesale_catalog, key = lambda b : b.price / b.ml_per_barrel):
        # Do not buy when ml content exceeds 1/4 of max capacity
        price_sum = barrel.price * barrel.quantity
        # 100 to ml to make and 100 gold to price
        if 100 * barrel.price / barrel.ml_per_barrel > 50 or gold - total_spend < barrel.price: 
            # Avoid barrels that go over 50 per potion
            continue
        elif price_sum <= gold - total_spend:
            # Avoid overflow
            if temp_ml_storage[barrel.potion_type.index(1)] + (barrel.quantity * barrel.ml_per_barrel) <= max_barrel_capacity:
                total_spend += price_sum
                temp_ml_storage[barrel.potion_type.index(1)] += barrel.quantity * barrel.ml_per_barrel
                bought_barrels.append(BarrelOrder(sku=barrel.sku, quantity=barrel.quantity))
            else:
                quantity = (max_barrel_capacity - temp_ml_storage[barrel.potion_type.index(1)]) // barrel.ml_per_barrel
                if quantity == 0:
                    continue
                total_spend += barrel.price * quantity
                temp_ml_storage[barrel.potion_type.index(1)] += quantity * barrel.ml_per_barrel
                bought_barrels.append(BarrelOrder(sku=barrel.sku, quantity=quantity))
                
        else:
            buyable = (gold - total_spend) // barrel.price
            if temp_ml_storage[barrel.potion_type.index(1)] + buyable * barrel.ml_per_barrel <= max_barrel_capacity:
                temp_ml_storage[barrel.potion_type.index(1)] += buyable * barrel.ml_per_barrel
                total_spend += buyable * barrel.price
                if buyable > 0:
                    bought_barrels.append(BarrelOrder(sku=barrel.sku, quantity=buyable))
            else:
                quantity = (max_barrel_capacity - temp_ml_storage[barrel.potion_type.index(1)]) // barrel.ml_per_barrel
                if quantity == 0:
                    continue
                total_spend += barrel.price * quantity
                temp_ml_storage[barrel.potion_type.index(1)] += quantity * barrel.ml_per_barrel
                bought_barrels.append(BarrelOrder(sku=barrel.sku, quantity=quantity))

    return bought_barrels


@router.post("/plan", response_model=List[BarrelOrder])
def get_wholesale_purchase_plan(wholesale_catalog: List[Barrel]):
    """
    Gets the plan for purchasing wholesale barrels. The call passes in a catalog of available barrels
    and the shop returns back which barrels they'd like to purchase and how many.
    """
    print(f"barrel catalog: {wholesale_catalog}")

    gold_total = get_gold_total()
    ml_total = get_ml_total()

    return create_barrel_plan(
        gold=gold_total,
        max_barrel_capacity=get_capacity().barrel_capacity*10000,
        current_red_ml=ml_total.red_ml,
        current_green_ml=ml_total.green_ml,
        current_blue_ml=ml_total.blue_ml,
        current_dark_ml=ml_total.dark_ml,
        wholesale_catalog=wholesale_catalog
    )
 