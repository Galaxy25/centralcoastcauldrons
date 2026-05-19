"""Add non-negative global inventory checks.

Revision ID: d4a9b8c7e6f5
Revises: b202cd3c9e33
Create Date: 2026-05-18 14:45:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d4a9b8c7e6f5"
down_revision: Union[str, None] = "b202cd3c9e33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_check_constraint(
        "ck_global_inventory_gold_non_negative",
        "global_inventory",
        "gold >= 0",
    )
    op.create_check_constraint(
        "ck_global_inventory_red_ml_non_negative",
        "global_inventory",
        "red_ml >= 0",
    )
    op.create_check_constraint(
        "ck_global_inventory_green_ml_non_negative",
        "global_inventory",
        "green_ml >= 0",
    )
    op.create_check_constraint(
        "ck_global_inventory_blue_ml_non_negative",
        "global_inventory",
        "blue_ml >= 0",
    )
    op.create_check_constraint(
        "ck_global_inventory_dark_ml_non_negative",
        "global_inventory",
        "dark_ml >= 0",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "ck_global_inventory_dark_ml_non_negative",
        "global_inventory",
        type_="check",
    )
    op.drop_constraint(
        "ck_global_inventory_blue_ml_non_negative",
        "global_inventory",
        type_="check",
    )
    op.drop_constraint(
        "ck_global_inventory_green_ml_non_negative",
        "global_inventory",
        type_="check",
    )
    op.drop_constraint(
        "ck_global_inventory_red_ml_non_negative",
        "global_inventory",
        type_="check",
    )
    op.drop_constraint(
        "ck_global_inventory_gold_non_negative",
        "global_inventory",
        type_="check",
    )
