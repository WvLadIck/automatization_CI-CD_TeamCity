"""Преподаватель: журнал успеваемости (функции 3 и 4)."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from db import execute, query
from errors import NotFoundError, ValidationError
from validators import (ALL_GRADES, ATTEMPTS, RECORD_STATUSES, study_year,
                        validate_grade, validate_grade_form)

bp = Blueprint("teacher", __name__, url_prefix="/teacher")

GRADES_SQL = """
    SELECT g.*, s.last_name || ' ' || s.first_name AS student, sg.group_name,
           p.discipline, p.semester, p.report_form
    FROM grades g
    JOIN students s ON s.id = g.student_id
    JOIN student_groups sg ON sg.id = s.group_id
    JOIN study_plans p ON p.id = g.plan_id
    ORDER BY g.assessed_on DESC, student, p.discipline, g.attempt_no
"""


def _form_options():
    students = query("SELECT s.id, s.last_name, s.first_name, g.group_name "
                     "FROM students s JOIN student_groups g ON g.id = s.group_id "
                     "ORDER BY s.last_name, s.first_name")
    plans = query("SELECT sp.id, sp.discipline, sp.semester, sp.report_form, ep.direction_code, "
                  "ep.cohort_year, ep.study_form FROM study_plans sp "
                  "JOIN educational_programs ep ON ep.id = sp.program_id "
                  "ORDER BY sp.discipline, ep.direction_code, ep.cohort_year, sp.semester")
    return students, plans


def _render_form(record):
    students, plans = _form_options()
    return render_template("grade_form.html", record=record, students=students, plans=plans,
                           grades=ALL_GRADES, attempts=ATTEMPTS, record_statuses=RECORD_STATUSES)


def _validate(form):
    """Проверяет форму журнала и возвращает данные для записи в БД."""
    data = validate_grade_form(form)
    student = query("SELECT g.program_id FROM students s "
                    "JOIN student_groups g ON g.id = s.group_id WHERE s.id = %s",
                    (data["student_id"],), one=True)
    if student is None:
        raise NotFoundError("Выбранный студент не найден")
    plan = query("SELECT program_id, report_form FROM study_plans WHERE id = %s",
                 (data["plan_id"],), one=True)
    if plan is None:
        raise NotFoundError("Выбранная дисциплина не найдена в учебном плане")
    if plan["program_id"] != student["program_id"]:
        raise ValidationError("Дисциплина не входит в учебный план студента")
    validate_grade(data["grade"], plan["report_form"])
    return data


@bp.route("/grades")
def grades():
    rows = query(GRADES_SQL)
    for row in rows:
        row["study_year"] = study_year(row["assessed_on"])
    return render_template("grades.html", grades=rows)


@bp.route("/grades/new", methods=["GET", "POST"])
def grade_new():
    if request.method == "POST":
        data = _validate(request.form)
        execute(
            "INSERT INTO grades (student_id, plan_id, attempt_no, assessed_on, grade, "
            "basis_ref, record_status) VALUES (%(student_id)s, %(plan_id)s, %(attempt_no)s, "
            "%(assessed_on)s, %(grade)s, %(basis_ref)s, %(record_status)s)",
            data,
        )
        flash("Запись добавлена в журнал")
        return redirect(url_for("teacher.grades"))
    return _render_form(None)


@bp.route("/grades/<int:grade_id>/edit", methods=["GET", "POST"])
def grade_edit(grade_id):
    record = query("SELECT * FROM grades WHERE id = %s", (grade_id,), one=True)
    if record is None:
        raise NotFoundError(f"Запись журнала с id={grade_id} не найдена")
    if record["record_status"] == "зафиксирован":
        raise ValidationError("Запись зафиксирована (ведомость закрыта) и не может изменяться")
    if request.method == "POST":
        data = _validate(request.form)
        data["id"] = grade_id
        execute(
            "UPDATE grades SET student_id = %(student_id)s, plan_id = %(plan_id)s, "
            "attempt_no = %(attempt_no)s, assessed_on = %(assessed_on)s, grade = %(grade)s, "
            "basis_ref = %(basis_ref)s, record_status = %(record_status)s WHERE id = %(id)s",
            data,
        )
        flash("Изменения сохранены")
        return redirect(url_for("teacher.grades"))
    return _render_form(record)
