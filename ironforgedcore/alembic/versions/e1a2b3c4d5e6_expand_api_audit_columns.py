"""expand api audit columns

Revision ID: e1a2b3c4d5e6
Revises: 12c509b3fd8c
Create Date: 2026-07-26 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "e1a2b3c4d5e6"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("api_audit", schema=None) as batch_op:
        batch_op.add_column(sa.Column("query_params", sa.JSON(), nullable=True))
        batch_op.add_column(
            sa.Column("route_template", sa.String(length=256), nullable=True)
        )
        batch_op.add_column(sa.Column("response_bytes", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("cache_hit", sa.Boolean(), nullable=True))
        batch_op.add_column(
            sa.Column("api_version", sa.String(length=32), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("api_audit", schema=None) as batch_op:
        batch_op.drop_column("api_version")
        batch_op.drop_column("cache_hit")
        batch_op.drop_column("response_bytes")
        batch_op.drop_column("route_template")
        batch_op.drop_column("query_params")
