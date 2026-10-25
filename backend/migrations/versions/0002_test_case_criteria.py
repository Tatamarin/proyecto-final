"""Add explicit acceptance criterion to test case traceability."""

from alembic import op
import sqlalchemy as sa


revision = "0002_test_case_criteria"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "test_case_criteria",
        sa.Column(
            "test_case_id",
            sa.Integer(),
            sa.ForeignKey("test_cases.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "acceptance_criteria_id",
            sa.Integer(),
            sa.ForeignKey("acceptance_criteria.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )


def downgrade():
    op.drop_table("test_case_criteria")
