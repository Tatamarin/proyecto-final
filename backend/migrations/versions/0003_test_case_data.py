"""Persistir datos de prueba.

Revision ID: 0003_test_case_data
Revises: 0002_test_case_criteria
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_test_case_data"
down_revision = "0002_test_case_criteria"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "test_cases",
        sa.Column("test_data", sa.JSON(), server_default=sa.text("'[]'"), nullable=False),
    )


def downgrade():
    op.drop_column("test_cases", "test_data")
