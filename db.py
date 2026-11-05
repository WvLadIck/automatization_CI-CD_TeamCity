"""Подключение к PostgreSQL.

Адрес БД берётся из переменной окружения DATABASE_URL, например:
postgresql://user:password@localhost:5432/students
"""
import os

import psycopg2
import psycopg2.extras
from flask import g

from errors import ValidationError

# Понятные сообщения для нарушений уникальности (имя ограничения -> текст)
UNIQUE_MESSAGES = {
    "educational_programs_version_uq": "Такая версия образовательной программы уже есть",
    "student_groups_name_uq": "Группа с таким номером уже есть",
    "students_no_uq": "Студент с таким номером зачётной книжки уже есть",
    "study_plans_component_uq": "Эта дисциплина уже есть в плане программы в этом семестре",
    "grades_event_uq": "Такая запись об аттестации уже есть в журнале",
    "grades_result_uq": "У студента уже есть результат по этой попытке "
                        "(повторную сдачу вносите со следующим номером попытки)",
}


def get_db():
    """Одно подключение на запрос."""
    if "db" not in g:
        g.db = psycopg2.connect(
            os.environ["DATABASE_URL"],
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, params=(), one=False):
    """SELECT: список строк или одна строка (one=True)."""
    with get_db().cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()
    if one:
        return rows[0] if rows else None
    return rows


def _db_error_message(exc):
    """Текст для пользователя по ошибке PostgreSQL или None, если ошибка не наша."""
    constraint = exc.diag.constraint_name
    if isinstance(exc, psycopg2.errors.RaiseException):  # сообщение из триггера
        return exc.diag.message_primary
    if isinstance(exc, psycopg2.errors.UniqueViolation):
        return UNIQUE_MESSAGES.get(constraint, "Такая запись уже есть")
    if isinstance(exc, psycopg2.errors.ForeignKeyViolation):
        return "Связанная запись не найдена или уже используется"
    if isinstance(exc, psycopg2.errors.CheckViolation):
        return f"Данные не прошли проверку в базе данных ({constraint})"
    return None


def execute(sql, params=()):
    """INSERT / UPDATE с фиксацией изменений.

    Ошибки ограничений и триггеров превращаются в ValidationError.
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
    except psycopg2.Error as exc:
        conn.rollback()
        message = _db_error_message(exc)
        if message is None:
            raise
        raise ValidationError(message) from exc
