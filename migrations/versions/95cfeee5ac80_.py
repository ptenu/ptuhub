"""empty message

Revision ID: 95cfeee5ac80
Revises: 843bc17f814f
Create Date: 2021-10-10 23:52:42.032266

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "95cfeee5ac80"
down_revision = "843bc17f814f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("contact_notes", sa.Column("content", sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("contact_notes", "content")
    # ### end Alembic commands ###
