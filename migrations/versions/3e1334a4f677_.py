"""empty message

Revision ID: 3e1334a4f677
Revises: 5b1dc203def0
Create Date: 2021-10-22 16:14:27.581685

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3e1334a4f677'
down_revision = '5b1dc203def0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pages', sa.Column('_created_on', sa.DateTime(), nullable=True))
    op.add_column('pages', sa.Column('_updated_on', sa.DateTime(), nullable=True))
    op.add_column('pages', sa.Column('_created_by', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'pages', 'contacts', ['_created_by'], ['id'], onupdate='CASCADE', ondelete='SET NULL')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'pages', type_='foreignkey')
    op.drop_column('pages', '_created_by')
    op.drop_column('pages', '_updated_on')
    op.drop_column('pages', '_created_on')
    # ### end Alembic commands ###