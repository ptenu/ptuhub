"""empty message

Revision ID: 0cfc9ab13529
Revises: 5fdf12fd9014
Create Date: 2022-05-12 01:15:49.635551

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0cfc9ab13529"
down_revision = "5fdf12fd9014"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "csrf_sessions",
        sa.Column("source", sa.VARCHAR(length=1024), nullable=False),
    )


def downgrade():

    op.alter_column(
        "csrf_sessions",
        sa.Column("source", sa.VARCHAR(length=22), nullable=False),
    )
