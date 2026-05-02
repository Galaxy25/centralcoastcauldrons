"""Transaction reset

Revision ID: f9016e310b3d
Revises: eac56a34e5a6
Create Date: 2026-05-01 18:07:38.803294

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9016e310b3d'
down_revision: Union[str, None] = 'eac56a34e5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS public CASCADE")
    op.execute("CREATE SCHEMA public")

    op.create_table(
    "alembic_version",
    sa.Column("version_num", sa.String(32), nullable=False, primary_key=True),
)
    op.get_bind().execute(
        sa.text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
        {"revision": down_revision},
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("time", sa.TIMESTAMP(), nullable=True, server_default=sa.text("now()")),
        sa.Column("description", sa.Text(), nullable=True, server_default=sa.text("''::text")),
    )

    op.create_table(
        "capacity_config",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("potion_capacity", sa.Integer(), nullable=False),
        sa.Column("barrel_capacity", sa.Integer(), nullable=False),
    )

    

    op.create_table(
        "cart_checkout",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False, autoincrement=False),
        sa.Column("customer_id", sa.Text(), nullable=False),
        sa.Column("customer_name", sa.Text(), nullable=True),
        sa.Column("customer_species", sa.Text(), nullable=True),
        sa.Column("customer_class", sa.Text(), nullable=True),
        sa.Column("level", sa.Integer(), nullable=True),
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.UniqueConstraint("customer_id", name="uq_cart_checkout_customer_id"),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["transactions.id"],
            name="cart_checkout_transaction_id_fkey",
        ),
    )

    op.create_table(
        "gold_history",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.Column("change", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["transactions.id"],
            name="gold_history_transaction_id_fkey",
        ),
    )

    op.create_table(
        "ml_history",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.Column("red_ml_change", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("green_ml_change", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("blue_ml_change", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("dark_ml_change", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["transactions.id"],
            name="ml_history_transaction_id_fkey",
        ),
    )

    op.create_table(
        "potion_inventory",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("red_ml", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("green_ml", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("blue_ml", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("dark_ml", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("price", sa.Integer(), nullable=True, server_default=sa.text("75")),
        sa.Column("item_sku", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=True),
    )

    op.create_table(
        "potion_history",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.Column("potion_id", sa.Integer(), nullable=True),
        sa.Column("change", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["potion_id"],
            ["potion_inventory.id"],
            name="potion_history_potion_id_fkey",
        ),
        sa.ForeignKeyConstraint(
            ["transaction_id"],
            ["transactions.id"],
            name="potion_history_transaction_id_fkey",
        ),
    )

    op.create_table(
        "cart_inventory",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("cart_id", sa.Integer(), nullable=False),
        sa.Column("potion_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["cart_id"],
            ["cart_checkout.id"],
            name="cart_inventory_cart_id_fkey",
        ),
        sa.ForeignKeyConstraint(
            ["potion_id"],
            ["potion_inventory.id"],
            name="cart_inventory_potion_id_fkey",
        ),
    )

    op.create_table(
        "ucb",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("customer_id", sa.Text(), nullable=False),
        sa.Column("potion_id", sa.Integer(), nullable=True),
        sa.Column("bought", sa.Integer(), nullable=True),
        sa.Column("shown", sa.Integer(), nullable=True),
        sa.Column("ucb_value", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["cart_checkout.customer_id"],
            name="ucb_customer_id_fkey",
        ),
        sa.ForeignKeyConstraint(
            ["potion_id"],
            ["potion_inventory.id"],
            name="ucb_potion_id_fkey",
        ),
    )


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS public CASCADE")
    op.execute("CREATE SCHEMA public")

    op.create_table(
    "alembic_version",
    sa.Column("version_num", sa.String(32), nullable=False, primary_key=True),
)
    op.get_bind().execute(
        sa.text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
        {"revision": revision},
    )

