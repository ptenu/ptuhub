"""empty message

Revision ID: 3107bcfa0a77
Revises: 95cfeee5ac80
Create Date: 2021-10-11 14:28:51.738522

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "3107bcfa0a77"
down_revision = "95cfeee5ac80"
branch_labels = None
depends_on = None


def upgrade():
    # Create ENUM
    tenures = postgresql.ENUM(
        "RENT_SOCIAL",
        "RENT_PRIVATE",
        "LODGER",
        "LICENSEE",
        "OCCUPIER",
        "OWNER_OCCUPIER",
        "LANDLORD",
        name="tenures",
    )
    tenures.create(op.get_bind())

    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "verify_contact_tokens",
        sa.Column("type", sa.Enum("EMAIL", "PHONE", name="types"), nullable=False),
        sa.Column("id", sa.String(length=1024), nullable=False),
        sa.Column("hash", sa.String(length=256), nullable=False),
        sa.Column("expires", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("type", "id"),
        sa.UniqueConstraint("hash"),
    )
    op.add_column(
        "contact_addresses", sa.Column("mail_to", sa.Boolean(), nullable=False)
    )
    op.add_column(
        "contact_addresses",
        sa.Column(
            "tenure",
            sa.Enum(
                "RENT_SOCIAL",
                "RENT_PRIVATE",
                "LODGER",
                "LICENSEE",
                "OCCUPIER",
                "OWNER_OCCUPIER",
                "LANDLORD",
                name="tenures",
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "contact_addresses", sa.Column("active", sa.Boolean(), nullable=False)
    )
    op.drop_column("contact_addresses", "owner_until")
    op.drop_column("contact_addresses", "occupier_from")
    op.drop_column("contact_addresses", "owner_from")
    op.drop_column("contact_addresses", "tenant_until")
    op.drop_column("contact_addresses", "occupier_until")
    op.drop_column("contact_addresses", "tenant_from")
    op.add_column(
        "contacts", sa.Column("prefered_email", sa.String(length=1024), nullable=True)
    )
    op.add_column(
        "contacts", sa.Column("prefered_phone", sa.String(length=15), nullable=True)
    )
    op.create_foreign_key(
        None, "contacts", "contact_numbers", ["prefered_phone"], ["number"]
    )
    op.create_foreign_key(
        None, "contacts", "contact_emails", ["prefered_email"], ["address"]
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "contacts", type_="foreignkey")
    op.drop_constraint(None, "contacts", type_="foreignkey")
    op.drop_column("contacts", "prefered_phone")
    op.drop_column("contacts", "prefered_email")
    op.add_column(
        "contact_addresses",
        sa.Column("tenant_from", sa.DATE(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "contact_addresses",
        sa.Column("occupier_until", sa.DATE(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "contact_addresses",
        sa.Column("tenant_until", sa.DATE(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "contact_addresses",
        sa.Column("owner_from", sa.DATE(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "contact_addresses",
        sa.Column("occupier_from", sa.DATE(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "contact_addresses",
        sa.Column("owner_until", sa.DATE(), autoincrement=False, nullable=True),
    )
    op.drop_column("contact_addresses", "active")
    op.drop_column("contact_addresses", "tenure")
    op.drop_column("contact_addresses", "mail_to")
    op.drop_table("verify_contact_tokens")
    # ### end Alembic commands ###

    # Remove ENUM
    tenures = postgresql.ENUM(
        "RENT_SOCIAL",
        "RENT_PRIVATE",
        "LODGER",
        "LICENSEE",
        "OCCUPIER",
        "OWNER_OCCUPIER",
        "LANDLORD",
        name="tenures",
    )
    tenures.drop(op.get_bind())