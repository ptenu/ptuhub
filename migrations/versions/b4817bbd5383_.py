"""empty message

Revision ID: b4817bbd5383
Revises: 3fab7432e5be
Create Date: 2022-04-28 23:55:07.104906

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b4817bbd5383"
down_revision = "3fab7432e5be"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "incidents",
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("reference", sa.Integer(), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("_reported_by", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["_reported_by"], ["contacts.id"], onupdate="CASCADE", ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("date", "reference"),
    )
    op.drop_constraint("contacts_lives_at_fkey", "contacts", type_="foreignkey")
    op.create_foreign_key(
        None,
        "contacts",
        "contact_addresses",
        ["lives_at"],
        ["id"],
        onupdate="CASCADE",
        ondelete="SET NULL",
    )
    op.alter_column(
        "requests", "session_id", existing_type=postgresql.UUID(), nullable=True
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "requests", "session_id", existing_type=postgresql.UUID(), nullable=False
    )
    op.drop_constraint(None, "contacts", type_="foreignkey")
    op.create_foreign_key(
        "contacts_lives_at_fkey", "contacts", "contact_addresses", ["lives_at"], ["id"]
    )
    op.drop_table("incidents")
    # ### end Alembic commands ###
