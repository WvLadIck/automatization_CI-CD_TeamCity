"""Начальная схема БД

Revision ID: 0001
Revises:
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SCHEMA_SQL = """
-- Схема БД «Учёт успеваемости студентов»

-- Контингент студентов
CREATE TABLE IF NOT EXISTS students (
    id             SERIAL PRIMARY KEY,
    last_name      VARCHAR(50)  NOT NULL,
    first_name     VARCHAR(50)  NOT NULL,
    patronymic     VARCHAR(50),
    admission_year INTEGER      NOT NULL,
    study_form     VARCHAR(10)  NOT NULL
        CHECK (study_form IN ('дневная', 'вечерняя', 'заочная')),
    group_name     VARCHAR(20)  NOT NULL
);

-- Учебный план
CREATE TABLE IF NOT EXISTS study_plans (
    id          SERIAL PRIMARY KEY,
    specialty   VARCHAR(100) NOT NULL,
    discipline  VARCHAR(100) NOT NULL,
    semester    INTEGER      NOT NULL CHECK (semester BETWEEN 1 AND 12),
    hours       INTEGER      NOT NULL CHECK (hours > 0),
    report_form VARCHAR(10)  NOT NULL
        CHECK (report_form IN ('экзамен', 'зачёт'))
);

-- Журнал успеваемости (дисциплина и семестр берутся из учебного плана)
CREATE TABLE IF NOT EXISTS grades (
    id          SERIAL PRIMARY KEY,
    study_year  VARCHAR(9)  NOT NULL,
    student_id  INTEGER     NOT NULL REFERENCES students (id) ON DELETE CASCADE,
    plan_id     INTEGER     NOT NULL REFERENCES study_plans (id) ON DELETE CASCADE,
    grade       VARCHAR(10) NOT NULL
        CHECK (grade IN ('2', '3', '4', '5', 'зачёт', 'незачёт')),
    UNIQUE (study_year, student_id, plan_id)
);
"""


def upgrade():
    op.execute(SCHEMA_SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS grades, study_plans, students")
