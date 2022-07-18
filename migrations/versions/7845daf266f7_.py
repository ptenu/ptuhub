"""empty message

Revision ID: 7845daf266f7
Revises: e6ae7ee38bb4
Create Date: 2022-04-10 04:46:42.581403

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7845daf266f7"
down_revision = "e6ae7ee38bb4"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("contacts", sa.Column("lives_at", sa.Integer(), nullable=True))
    op.create_foreign_key(None, "contacts", "contact_addresses", ["lives_at"], ["id"])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "contacts", type_="foreignkey")
    op.drop_column("contacts", "lives_at")
    # ### end Alembic commands ###
