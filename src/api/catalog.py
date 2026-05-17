from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Annotated
from src.api.UCB import increment_shown, update_ucb
from src.api.helper import (
    POTION_PRICE,
    get_potions_by_ucb,
    get_random_potions,
    get_recent_customer_classes,
)
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


def _class_slot_counts(character_classes: list[str]) -> list[tuple[str, int]]:
    if not character_classes:
        return []

    classes = character_classes[:6]
    base_slots = 6 // len(classes)
    extra_slots = 6 % len(classes)
    return [
        (character_class, base_slots + (1 if index < extra_slots else 0))
        for index, character_class in enumerate(classes)
    ]


def _catalog_item_from_potion(potion) -> CatalogItem:
    return CatalogItem(
        sku=potion.item_sku,
        name=potion.name,
        quantity=potion.quantity,
        price=POTION_PRICE,
        potion_type=[potion.red_ml, potion.green_ml, potion.blue_ml, potion.dark_ml],
    )


def create_catalog() -> List[CatalogItem]:
    with db.engine.begin() as connection:
        # Recent classes decide how the six catalog slots are divided
        recent_classes = [
            row.character_class
            for row in get_recent_customer_classes(connection, 6)
        ]
        selected_ids = set()
        selected_potions = []

        for character_class, slot_count in _class_slot_counts(recent_classes):
            selected_for_class = 0
            # Use the best UCB potions for each class first
            for potion in get_potions_by_ucb(connection, character_class):
                if potion.id in selected_ids:
                    continue

                selected_ids.add(potion.id)
                selected_potions.append((potion, character_class))
                selected_for_class += 1
                if selected_for_class == slot_count:
                    break

            fallback_count = slot_count - selected_for_class
            # New classes may not have UCB rows yet, so fill their slots randomly
            for potion in get_random_potions(connection, fallback_count, selected_ids):
                selected_ids.add(potion.id)
                selected_potions.append((potion, character_class))

        if len(selected_potions) < 6:
            # If there were fewer than six class-backed picks, keep the catalog full.
            for potion in get_random_potions(
                connection,
                6 - len(selected_potions),
                selected_ids,
            ):
                selected_ids.add(potion.id)
                selected_potions.append((potion, None))

        items = []
        for potion, character_class in selected_potions[:6]:
            # Only class-backed picks should train that class's UCB row.
            if character_class is not None:
                increment_shown(connection, character_class, potion.id)
                update_ucb(connection, character_class, potion.id)
            items.append(_catalog_item_from_potion(potion))
    return items


@router.get("/catalog/", tags=["catalog"], response_model=List[CatalogItem])
def get_catalog() -> List[CatalogItem]:
    """
    Retrieves the catalog of items. Each unique item combination should have only a single price.
    You can have at most 6 potion SKUs offered in your catalog at one time.
    """
    return create_catalog()
