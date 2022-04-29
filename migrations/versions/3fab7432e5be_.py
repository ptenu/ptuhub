"""empty message

Revision ID: 3fab7432e5be
Revises: cdc2288d5318
Create Date: 2022-04-22 00:08:53.063190

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3fab7432e5be'
down_revision = 'cdc2288d5318'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('roles', 'role_title')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('roles', sa.Column('role_title', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    # ### end Alembic commands ###