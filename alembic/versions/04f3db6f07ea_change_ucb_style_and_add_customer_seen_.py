"""Change UCB style, and add customer seen table.

Revision ID: 04f3db6f07ea
Revises: f8a1b9e097b6
Create Date: 2026-05-16 15:58:19.411481

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from src.api.UCB import seed_ucb_for_class


# revision identifiers, used by Alembic.
revision: str = "04f3db6f07ea"
down_revision: Union[str, None] = "f8a1b9e097b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_table("ucb")
    op.create_table(
        "ucb",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("character_class", sa.Text(), nullable=False),
        sa.Column("potion_id", sa.Integer(), nullable=False),
        sa.Column("bought", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("shown", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("ucb_value", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(
            ["potion_id"],
            ["potion_inventory.id"],
            name="ucb_potion_id_fkey",
        ),
        sa.UniqueConstraint(
            "character_class",
            "potion_id",
            name="uq_ucb_character_class_potion_id",
        ),
    )
    op.create_table(
        "customer_seen",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("visit_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Text(), nullable=False),
        sa.Column("customer_name", sa.Text(), nullable=False),
        sa.Column("character_class", sa.Text(), nullable=False),
        sa.Column("character_species", sa.Text(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.execute(
        sa.text(
            """
            WITH potion_types(red_ml, green_ml, blue_ml, dark_ml) AS (
                VALUES
                    (0, 0, 0, 100),
                    (0, 0, 25, 75),
                    (0, 0, 50, 50),
                    (0, 0, 75, 25),
                    (0, 0, 100, 0),
                    (0, 25, 0, 75),
                    (0, 25, 25, 50),
                    (0, 25, 50, 25),
                    (0, 25, 75, 0),
                    (0, 50, 0, 50),
                    (0, 50, 25, 25),
                    (0, 50, 50, 0),
                    (0, 75, 0, 25),
                    (0, 75, 25, 0),
                    (0, 100, 0, 0),
                    (25, 0, 0, 75),
                    (25, 0, 25, 50),
                    (25, 0, 50, 25),
                    (25, 0, 75, 0),
                    (25, 25, 0, 50),
                    (25, 25, 25, 25),
                    (25, 25, 50, 0),
                    (25, 50, 0, 25),
                    (25, 50, 25, 0),
                    (25, 75, 0, 0),
                    (50, 0, 0, 50),
                    (50, 0, 25, 25),
                    (50, 0, 50, 0),
                    (50, 25, 0, 25),
                    (50, 25, 25, 0),
                    (50, 50, 0, 0),
                    (75, 0, 0, 25),
                    (75, 0, 25, 0),
                    (75, 25, 0, 0),
                    (100, 0, 0, 0)
            )
            INSERT INTO potion_inventory (red_ml, green_ml, blue_ml, dark_ml, price, item_sku, name)
            SELECT
                red_ml,
                green_ml,
                blue_ml,
                dark_ml,
                50,
                'R' || red_ml || 'G' || green_ml || 'B' || blue_ml || 'D' || dark_ml,
                'R' || red_ml || 'G' || green_ml || 'B' || blue_ml || 'D' || dark_ml
            FROM potion_types
            WHERE NOT EXISTS (
                SELECT 1
                FROM potion_inventory
                WHERE item_sku = 'R' || potion_types.red_ml || 'G' || potion_types.green_ml || 'B' || potion_types.blue_ml || 'D' || potion_types.dark_ml
            )
            """
        )
    )
    connection = op.get_bind()
    seed_preferences = [
        ("Hunter", "R50G50B0D0"),
        ("Runesmith", "R0G0B100D0"),
        ("Seer", "R0G100B0D0"),
        ("Warrior", "R100G0B0D0"),
        ("Wolf-Warrior", "R75G25B0D0"),
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
    op.drop_table("customer_seen")
    op.drop_table("ucb")
    op.create_table(
        "ucb",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("game_day", sa.Text(), nullable=False),
        sa.Column("potion_id", sa.Integer(), nullable=False),
        sa.Column("bought", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("shown", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("ucb_value", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(
            ["potion_id"],
            ["potion_inventory.id"],
            name="ucb_potion_id_fkey",
        ),
        sa.UniqueConstraint("game_day", "potion_id", name="uq_ucb_game_day_potion_id"),
    )
