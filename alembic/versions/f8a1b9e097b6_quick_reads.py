"""Quick reads

Revision ID: f8a1b9e097b6
Revises: f9016e310b3d
Create Date: 2026-05-11 17:49:41.227383

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f8a1b9e097b6"
down_revision: Union[str, None] = "f9016e310b3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "global_inventory",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("gold", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("red_ml", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "green_ml", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("blue_ml", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("dark_ml", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )

    op.add_column(
        "potion_inventory",
        sa.Column(
            "quantity", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
    )

    op.execute(
        sa.text(
            """
            INSERT INTO global_inventory (id, gold, red_ml, green_ml, blue_ml, dark_ml)
            VALUES (
                1,
                (SELECT COALESCE(SUM(change), 0) FROM gold_history),
                (SELECT COALESCE(SUM(red_ml_change), 0) FROM ml_history),
                (SELECT COALESCE(SUM(green_ml_change), 0) FROM ml_history),
                (SELECT COALESCE(SUM(blue_ml_change), 0) FROM ml_history),
                (SELECT COALESCE(SUM(dark_ml_change), 0) FROM ml_history)
            )
            """
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("potion_inventory", "quantity")
    op.drop_table("global_inventory")
