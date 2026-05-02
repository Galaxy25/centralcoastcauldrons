import math

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
import sqlalchemy
from src.api import auth
from src import database as db
from src.api.helper import *

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)


class InventoryAudit(BaseModel):
    number_of_potions: int
    ml_in_barrels: int
    gold: int


class CapacityPlan(BaseModel):
    potion_capacity: int = Field(
        ge=0, le=10, description="Potion capacity units, max 10"
    )
    ml_capacity: int = Field(ge=0, le=10, description="ML capacity units, max 10")


@router.get("/audit", response_model=InventoryAudit)
def get_inventory():
    """
    Returns an audit of the current inventory. Any discrepancies between
    what is reported here and my source of truth will be posted
    as errors on potion exchange.
    """
    total_gold = get_gold_total()
    total_ml = sum(get_ml_total())
    total_potions = sum([i.quantity for i in get_all_potions()])
    return InventoryAudit(number_of_potions=total_potions, 
                          ml_in_barrels=total_ml, 
                          gold=total_gold)


@router.post("/plan", response_model=CapacityPlan)
def get_capacity_plan():
    """
    Provides a daily capacity purchase plan.

    - Start with 1 capacity for 50 potions and 1 capacity for 10,000 ml of potion.
    - Each additional capacity unit costs 1000 gold.
    """
    max_cu = get_gold_total() // 1000
    max_cu -= 2
    if max_cu <= 0:
        return CapacityPlan(potion_capacity=0, ml_capacity=0)
    capacity = get_capacity()
    potion_capacity = min(10 - capacity.potion_capacity, math.ceil(max_cu / 2))
    ml_capacity = min(10 - capacity.barrel_capacity, math.floor(max_cu / 2))
    return CapacityPlan(potion_capacity=potion_capacity, ml_capacity=ml_capacity)


@router.post("/deliver/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def deliver_capacity_plan(capacity_purchase: CapacityPlan, order_id: int):
    """
    Processes the delivery of the planned capacity purchase. order_id is a
    unique value representing a single delivery; the call is idempotent.

    - Start with 1 capacity for 50 potions and 1 capacity for 10,000 ml of potion.
    - Each additional capacity unit costs 1000 gold.
    """
    print(f"capacity delivered: {capacity_purchase} order_id: {order_id}")
    total_cost = (capacity_purchase.potion_capacity + capacity_purchase.ml_capacity) * 1000
    update_gold(-total_cost, f"Capacity purchase for order: {order_id}, potion_capacity: {capacity_purchase.potion_capacity}, ml_capacity: {capacity_purchase.ml_capacity}")
    with db.engine.begin() as connection:
        connection.execute(
            sqlalchemy.text(
                """
                UPDATE capacity_config
                SET potion_capacity = potion_capacity + :potion_capacity,
                    barrel_capacity = barrel_capacity + :ml_capacity
                """),
                [{"potion_capacity": capacity_purchase.potion_capacity, "ml_capacity": capacity_purchase.ml_capacity}])