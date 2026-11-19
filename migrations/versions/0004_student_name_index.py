"""Добавить индекс по фамилии и имени для списка студентов."""
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    """Создать индекс для столбцов из ORDER BY списка студентов."""
    op.create_index("students_name_idx", "students", ["last_name", "first_name"])


def downgrade():
    """Удалить индекс при откате."""
    op.drop_index("students_name_idx", table_name="students")
