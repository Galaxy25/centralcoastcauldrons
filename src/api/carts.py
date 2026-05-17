from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
import sqlalchemy
from src.api import auth
from enum import Enum
from typing import List, Optional
from src.api.UCB import _check_ucb, increment_bought, seed_ucb_for_class, update_ucb
from src.api.helper import (
    POTION_PRICE,
    add_customer_seen,
    get_cart_customer_class,
    update_gold,
    update_potions,
)
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class SearchSortOptions(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"


class SearchSortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class LineItem(BaseModel):
    line_item_id: int
    item_sku: str
    customer_name: str
    line_item_total: int
    timestamp: str


class SearchResponse(BaseModel):
    previous: Optional[str] = None
    next: Optional[str] = None
    results: List[LineItem]


@router.get("/search/", response_model=SearchResponse, tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: SearchSortOptions = SearchSortOptions.timestamp,
    sort_order: SearchSortOrder = SearchSortOrder.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.
    """
    return SearchResponse(
        previous=None,
        next=None,
        results=[
            LineItem(
                line_item_id=1,
                item_sku="1 oblivion potion",
                customer_name="Scaramouche",
                line_item_total=50,
                timestamp="2021-01-01T00:00:00Z",
            )
        ],
    )



class Customer(BaseModel):
    customer_id: str
    customer_name: str
    character_class: str
    character_species: str
    level: int = Field(ge=1, le=20)


@router.post("/visits/{visit_id}", status_code=status.HTTP_204_NO_CONTENT)
def post_visits(visit_id: int, customers: List[Customer]):
    """
    Shares the customers that visited the store on that tick.
    """
    with db.engine.begin() as connection:
        for customer in customers:
            add_customer_seen(
                connection,
                visit_id,
                customer.customer_id,
                customer.customer_name,
                customer.character_class,
                customer.character_species,
                customer.level,
            )

    return status.HTTP_204_NO_CONTENT

class CartCreateResponse(BaseModel):
    cart_id: int


@router.post("/", response_model=CartCreateResponse)
def create_cart(new_cart: Customer):
    """
    Creates a new cart for a specific customer.
    """

    with db.engine.begin() as connection:
        transaction_id = connection.execute(
            sqlalchemy.text("INSERT INTO transactions (description) VALUES (:msg) RETURNING id"),
            {"msg": f"Cart created for {new_cart.customer_id}"},
        ).one().id
        id = connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO cart_checkout (customer_id, customer_name, customer_species, customer_class, level, transaction_id)
                VALUES (:customer_id, :customer_name, :customer_species, :customer_class, :level, :transaction_id)
                RETURNING id;
                """
            ),
            {"customer_id": new_cart.customer_id, "customer_name": new_cart.customer_name, "customer_species": new_cart.character_species, "customer_class": new_cart.character_class, "level": new_cart.level, "transaction_id": transaction_id},
        ).one().id
    return CartCreateResponse(cart_id=id)


class CartItem(BaseModel):
    quantity: int = Field(ge=1, description="Quantity must be at least 1")


@router.post("/{cart_id}/items/{item_sku}", status_code=status.HTTP_204_NO_CONTENT)
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    print(
        f"cart_id: {cart_id}, item_sku: {item_sku}, cart_item: {cart_item}"
    )

    with db.engine.begin() as connection:
        potion_id = connection.execute(
            sqlalchemy.text(
                """
                SELECT id
                FROM potion_inventory
                WHERE item_sku = :item_sku
                """
            ),
            {"item_sku": item_sku},
        ).one().id
        connection.execute(
            sqlalchemy.text(
                """
                INSERT INTO cart_inventory (cart_id, potion_id, quantity)
                VALUES (:cart_id, :potion_id, :quantity)
                """
            ),
            {"cart_id": cart_id, "potion_id": potion_id, "quantity": cart_item.quantity},
        )

    return status.HTTP_204_NO_CONTENT


class CheckoutResponse(BaseModel):
    total_potions_bought: int
    total_gold_paid: int


class CartCheckout(BaseModel):
    payment: str


@router.post("/{cart_id}/checkout", response_model=CheckoutResponse)
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """
    Handles the checkout process for a specific cart.
    """

    with db.engine.begin() as connection:
        customer_class = get_cart_customer_class(connection, cart_id)
        cart_items = connection.execute(
            sqlalchemy.text(
                """
                SELECT *
                FROM cart_inventory
                WHERE cart_id = :cart_id
                """
            ),
            {"cart_id": cart_id},
        ).all()
        total_potions_bought = 0
        total_gold_paid = 0
        for potion in cart_items:
            total_potions_bought += potion.quantity
            total_gold_paid += potion.quantity * POTION_PRICE
            if not _check_ucb(connection, customer_class, potion.potion_id):
                seed_ucb_for_class(connection, customer_class, potion.potion_id)
            else:
                increment_bought(connection, customer_class, potion.potion_id, 1)
                update_ucb(connection, customer_class, potion.potion_id)
            update_potions(connection, potion.potion_id, -potion.quantity, message=f"Checkout for cart: {cart_id}, potion_id: {potion.potion_id}, quantity: {potion.quantity}")
        update_gold(connection, total_gold_paid, f"Checkout for cart: {cart_id}, gold paid: {total_gold_paid}")

    return CheckoutResponse(
        total_potions_bought=total_potions_bought, total_gold_paid=total_gold_paid
    )
