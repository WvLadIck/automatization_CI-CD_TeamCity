"""Тестовые данные из db/seed.sql

Revision ID: 0002
Revises: 0001
"""
from pathlib import Path

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

SEED_FILE = Path(__file__).resolve().parents[2] / "db" / "seed.sql"


def upgrade():
    op.get_bind().exec_driver_sql(SEED_FILE.read_text(encoding="utf-8"))


def downgrade():
    op.get_bind().exec_driver_sql(
        "TRUNCATE grades, study_plans, students, student_groups, educational_programs "
        "RESTART IDENTITY")
