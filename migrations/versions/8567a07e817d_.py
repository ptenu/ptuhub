"""empty message

Revision ID: 8567a07e817d
Revises: f7de189ba8a1
Create Date: 2022-04-29 02:47:55.358073

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "8567a07e817d"
down_revision = "f7de189ba8a1"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "challenges",
        sa.Column("token", sa.VARCHAR(length=64), nullable=False),
        sa.Column("contact_id", sa.INTEGER(), nullable=True),
        sa.Column("created_on", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("last4", sa.VARCHAR(length=4), nullable=True),
        sa.Column("sms", sa.BOOLEAN(), nullable=True),
        sa.Column("email", sa.BOOLEAN(), nullable=True),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("token"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("challenges")
    # ### end Alembic commands ###
