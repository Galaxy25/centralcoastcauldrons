from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Annotated
from src.api.UCB import get_game_day, increment_shown, update_ucb
from src.api.helper import POTION_PRICE, get_potions_by_ucb
from src import database as db

router = APIRouter()


class CatalogItem(BaseModel):
    sku: Annotated[str, Field(pattern=r"^[a-zA-Z0-9_]{1,20}$")]
    name: str
    quantity: Annotated[int, Field(ge=1, le=10000)]
    price: Annotated[int, Field(ge=1, le=500)]
    potion_type: List[int] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Must contain exactly 4 elements: [r, g, b, d]",
    )


# Placeholder function, you will replace this with a database call
def create_catalog() -> List[CatalogItem]:
    with db.engine.begin() as connection:
        potions = get_potions_by_ucb(connection, get_game_day())

        items = []
        for p in potions[:6]:
            increment_shown(connection, p.id)
            items.append(
                CatalogItem(
                    sku=p.item_sku,
                    name=p.name,
                    quantity=p.quantity,
                    price=POTION_PRICE,
                    potion_type=[p.red_ml, p.green_ml, p.blue_ml, p.dark_ml],
                )
            )
    return items


@router.get("/catalog/", tags=["catalog"], response_model=List[CatalogItem])
def get_catalog() -> List[CatalogItem]:
    """
    Retrieves the catalog of items. Each unique item combination should have only a single price.
    You can have at most 6 potion SKUs offered in your catalog at one time.
    """
    return create_catalog()
