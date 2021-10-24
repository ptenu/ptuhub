"""empty message

Revision ID: b0c70b5cb3bf
Revises: a7171e65bb62
Create Date: 2021-10-22 00:44:23.003097

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b0c70b5cb3bf'
down_revision = 'a7171e65bb62'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('case_addresses',
    sa.Column('case_id', sa.Integer(), nullable=False),
    sa.Column('uprn', sa.BigInteger(), nullable=False),
    sa.Column('reference', sa.String(length=25), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('_created_on', sa.DateTime(), nullable=False),
    sa.Column('_created_by', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['_created_by'], ['contacts.id'], onupdate='CASCADE', ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['case_id'], ['cases.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['uprn'], ['addresses.uprn'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('case_id', 'uprn')
    )
    op.create_index(op.f('ix_case_addresses_reference'), 'case_addresses', ['reference'], unique=False)
    op.create_table('case_files',
    sa.Column('case_id', sa.Integer(), nullable=True),
    sa.Column('file_id', sa.String(length=10), nullable=True),
    sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
    sa.ForeignKeyConstraint(['file_id'], ['files.id'], )
    )
    op.add_column('case_text', sa.Column('title', sa.String(length=150), nullable=True))
    op.drop_constraint('contacts_avatar_id_fkey', 'contacts', type_='foreignkey')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key('contacts_avatar_id_fkey', 'contacts', 'files', ['avatar_id'], ['id'])
    op.drop_column('case_text', 'title')
    op.drop_table('case_files')
    op.drop_index(op.f('ix_case_addresses_reference'), table_name='case_addresses')
    op.drop_table('case_addresses')
    # ### end Alembic commands ###
