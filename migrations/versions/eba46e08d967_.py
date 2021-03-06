"""empty message

Revision ID: eba46e08d967
Revises: ccf3a0a55f58
Create Date: 2022-04-17 23:10:03.164621

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "eba46e08d967"
down_revision = "ccf3a0a55f58"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "requests",
        sa.Column("method", sa.VARCHAR(length=6), nullable=False),
    )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "requests",
        sa.Column("method", sa.VARCHAR(length=5), nullable=False),
    )
