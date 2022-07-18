"""empty message

Revision ID: 844afab1552f
Revises: c8dc8dcff57a
Create Date: 2022-01-23 00:40:30.793742

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "844afab1552f"
down_revision = "c8dc8dcff57a"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "survey_returns", sa.Column("response_2", sa.String(length=1), nullable=True)
    )
    op.add_column(
        "survey_returns", sa.Column("response_3", sa.String(length=1), nullable=True)
    )
    op.add_column(
        "survey_returns", sa.Column("response_4", sa.String(length=1), nullable=True)
    )
    op.drop_column("survey_returns", "housing_cost")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "survey_returns",
        sa.Column("housing_cost", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.drop_column("survey_returns", "response_4")
    op.drop_column("survey_returns", "response_3")
    op.drop_column("survey_returns", "response_2")
    # ### end Alembic commands ###
