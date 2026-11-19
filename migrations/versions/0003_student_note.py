import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("students", sa.Column("academic_note", sa.String(120)))


def downgrade():
    op.drop_column("students", "academic_note")
