"""Подключение к PostgreSQL.

Адрес БД берётся из переменной окружения DATABASE_URL, например:
postgresql://user:password@localhost:5432/students
"""
import os

import psycopg2
import psycopg2.extras
from flask import g


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


def execute(sql, params=()):
    """INSERT / UPDATE с фиксацией изменений."""
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(sql, params)
    conn.commit()
