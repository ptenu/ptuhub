"""empty message

Revision ID: 5b1dc203def0
Revises: a758d1a41c56
Create Date: 2021-10-22 01:29:21.133072

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5b1dc203def0'
down_revision = 'a758d1a41c56'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pages', sa.Column('archived', sa.Boolean(), nullable=False))
    op.add_column('pages', sa.Column('publish_on', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('pages', 'publish_on')
    op.drop_column('pages', 'archived')
    # ### end Alembic commands ###
