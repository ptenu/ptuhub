"""empty message

Revision ID: 9d133e300ff1
Revises: 392fddfad2cd
Create Date: 2021-10-14 00:50:22.005843

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9d133e300ff1"
down_revision = "392fddfad2cd"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("emails", sa.Column("type", sa.String(length=15), nullable=False))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("emails", "type")
    # ### end Alembic commands ###
