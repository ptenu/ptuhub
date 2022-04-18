"""empty message

Revision ID: 85af3e892167
Revises: 3cd6567b4287
Create Date: 2022-02-08 04:16:34.774924

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "85af3e892167"
down_revision = "3cd6567b4287"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "contact_availability",
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "AVAILABLE",
                "OFFLINE",
                "EMAR",
                "ASSIGNED",
                "BUSY",
                "ON_BREAK",
                name="availabilitystatuses",
            ),
            nullable=False,
        ),
        sa.Column(
            "latitude", sa.Float(precision=8, decimal_return_scale=7), nullable=True
        ),
        sa.Column(
            "longitude", sa.Float(precision=8, decimal_return_scale=7), nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["contact_id"], ["contacts.id"], onupdate="CASCADE", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("contact_id", "timestamp"),
    )
    op.create_table(
        "request_clients",
        sa.Column("id", sa.VARCHAR(length=64), nullable=False),
        sa.Column("created", postgresql.TIMESTAMP(), nullable=True),
        sa.Column(
            "vector",
            postgresql.ENUM(
                "PASSWORD", "SMS", "EMAIL", "PAYMENT", "NEW", name="vectors"
            ),
            nullable=True,
        ),
        sa.Column("contact_id", sa.INTEGER(), nullable=True),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "request_sessions",
        sa.Column(
            "id",
            postgresql.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_agent_hash", sa.VARCHAR(length=64), nullable=False),
        sa.Column("remote_addr", postgresql.INET(), nullable=False),
        sa.Column("source", sa.VARCHAR(length=22), nullable=False),
        sa.Column("created", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("last_used", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("trusted", sa.BOOLEAN(), nullable=False),
        sa.Column("contact_id", sa.INTEGER(), nullable=True),
        sa.Column("client_id", sa.VARCHAR(length=64), nullable=True),
        sa.ForeignKeyConstraint(
            ["client_id"], ["request_clients.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "requests",
        sa.Column("id", sa.INTEGER(), nullable=False),
        sa.Column("started", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("finished", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("time", sa.INTEGER(), nullable=True),
        sa.Column("session_id", postgresql.UUID(), nullable=False),
        sa.Column("host", sa.VARCHAR(length=256), nullable=True),
        sa.Column("path", sa.VARCHAR(length=1024), nullable=True),
        sa.Column("method", sa.VARCHAR(length=6), nullable=False),
        sa.Column("trusted", sa.BOOLEAN(), nullable=False),
        sa.Column("response_code", sa.INTEGER(), nullable=True),
        sa.Column("contact_id", sa.INTEGER(), nullable=True),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["session_id"], ["request_sessions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("requests")
    op.drop_table("request_sessions")
    op.drop_table("request_clients")
    op.drop_table("contact_availability")
    # ### end Alembic commands ###
