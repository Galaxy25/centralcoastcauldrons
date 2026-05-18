"""Remove cart customer uniqueness

Revision ID: b202cd3c9e33
Revises: c1a2426e50b6
Create Date: 2026-05-18 00:37:59.768376

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b202cd3c9e33"
down_revision: Union[str, None] = "c1a2426e50b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint("cart_checkout_customer_id_key", "cart_checkout", type_="unique")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_unique_constraint("cart_checkout_customer_id_key", "cart_checkout", ["customer_id"])
