"""Add shadowwalker

Revision ID: c1a2426e50b6
Revises: 04f3db6f07ea
Create Date: 2026-05-17 13:09:55.144844

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from src.api.UCB import seed_ucb_for_class


# revision identifiers, used by Alembic.
revision: str = 'c1a2426e50b6'
down_revision: Union[str, None] = '04f3db6f07ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    seed_preferences = [
        ("Shadow Walker", "R0G0B0D100"),
    ]
    for character_class, item_sku in seed_preferences:
        potion_id = connection.execute(
            sa.text(
                """
                SELECT id
                FROM potion_inventory
                WHERE item_sku = :item_sku
                """
            ),
            {"item_sku": item_sku},
        ).scalar_one()
        seed_ucb_for_class(connection, character_class, potion_id)


def downgrade() -> None:
    """Downgrade schema."""
    pass
