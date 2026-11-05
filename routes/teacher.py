"""Преподаватель: журнал успеваемости (функции 3 и 4)."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from db import execute, query
from errors import NotFoundError, ValidationError
from validators import validate_grade, validate_study_year

bp = Blueprint("teacher", __name__, url_prefix="/teacher")

GRADES_SQL = """
    SELECT g.id, g.study_year, g.grade,
           s.last_name || ' ' || s.first_name AS student, s.group_name,
           p.discipline, p.semester, p.report_form
    FROM grades g
    JOIN students s ON s.id = g.student_id
    JOIN study_plans p ON p.id = g.plan_id
"""


def _form_options():
    students = query("SELECT id, last_name, first_name, group_name FROM students "
                     "ORDER BY last_name, first_name")
    plans = query("SELECT id, discipline, semester, report_form FROM study_plans "
                  "ORDER BY discipline, semester")
    return students, plans


def _validate(form):
    """Проверяет форму журнала и возвращает данные для записи в БД."""
    try:
        student_id = int(form.get("student_id", ""))
        plan_id = int(form.get("plan_id", ""))
    except ValueError as exc:
        raise ValidationError("Выберите студента и дисциплину") from exc

    if query("SELECT id FROM students WHERE id = %s", (student_id,), one=True) is None:
        raise NotFoundError("Выбранный студент не найден")
    plan = query("SELECT report_form FROM study_plans WHERE id = %s", (plan_id,), one=True)
    if plan is None:
        raise NotFoundError("Выбранная дисциплина не найдена в учебном плане")

    return {
        "study_year": validate_study_year(form.get("study_year")),
        "student_id": student_id,
        "plan_id": plan_id,
        "grade": validate_grade(form.get("grade"), plan["report_form"]),
    }


def _check_duplicate(data, exclude_id=None):
    row = query(
        "SELECT id FROM grades WHERE study_year = %(study_year)s "
        "AND student_id = %(student_id)s AND plan_id = %(plan_id)s",
        data, one=True,
    )
    if row and row["id"] != exclude_id:
        raise ValidationError("У студента уже есть оценка по этой дисциплине за этот год")


@bp.route("/grades")
def grades():
    rows = query(GRADES_SQL + " ORDER BY g.study_year DESC, student, p.discipline")
    return render_template("grades.html", grades=rows)


@bp.route("/grades/new", methods=["GET", "POST"])
def grade_new():
    if request.method == "POST":
        data = _validate(request.form)
        _check_duplicate(data)
        execute(
            "INSERT INTO grades (study_year, student_id, plan_id, grade) "
            "VALUES (%(study_year)s, %(student_id)s, %(plan_id)s, %(grade)s)",
            data,
        )
        flash("Оценка добавлена в журнал")
        return redirect(url_for("teacher.grades"))
    students, plans = _form_options()
    return render_template("grade_form.html", record=None, students=students, plans=plans)


@bp.route("/grades/<int:grade_id>/edit", methods=["GET", "POST"])
def grade_edit(grade_id):
    record = query("SELECT * FROM grades WHERE id = %s", (grade_id,), one=True)
    if record is None:
        raise NotFoundError(f"Запись журнала с id={grade_id} не найдена")
    if request.method == "POST":
        data = _validate(request.form)
        _check_duplicate(data, exclude_id=grade_id)
        data["id"] = grade_id
        execute(
            "UPDATE grades SET study_year = %(study_year)s, student_id = %(student_id)s, "
            "plan_id = %(plan_id)s, grade = %(grade)s WHERE id = %(id)s",
            data,
        )
        flash("Изменения сохранены")
        return redirect(url_for("teacher.grades"))
    students, plans = _form_options()
    return render_template("grade_form.html", record=record, students=students, plans=plans)
