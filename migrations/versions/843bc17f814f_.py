"""empty message

Revision ID: 843bc17f814f
Revises: 72af127614b6
Create Date: 2021-10-10 23:46:01.910727

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '843bc17f814f'
down_revision = '72af127614b6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('contact_notes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('contact_id', sa.Integer(), nullable=False),
    sa.Column('_created_on', sa.DateTime(), nullable=True),
    sa.Column('_updated_on', sa.DateTime(), nullable=True),
    sa.Column('_created_by', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['_created_by'], ['contacts.id'], onupdate='CASCADE', ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', 'contact_id')
    )
    op.add_column('contacts', sa.Column('stripe_customer_id', sa.String(length=52), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('contacts', 'stripe_customer_id')
    op.drop_table('contact_notes')
    # ### end Alembic commands ###
