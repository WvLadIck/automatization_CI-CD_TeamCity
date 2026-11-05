"""Студент: часы и форма отчётности по дисциплине (функция 2), свои оценки."""
from flask import Blueprint, render_template, request

from db import query
from errors import NotFoundError

bp = Blueprint("student", __name__, url_prefix="/student")


@bp.route("/")
def index():
    disciplines = query("SELECT DISTINCT discipline FROM study_plans ORDER BY discipline")
    students = query("SELECT id, last_name, first_name, group_name FROM students "
                     "ORDER BY last_name, first_name")

    # Функция 2: часы и формы отчётности по дисциплине
    discipline = (request.args.get("discipline") or "").strip()
    plan_rows, total_hours = None, None
    if discipline:
        plan_rows = query(
            "SELECT semester, hours, report_form FROM study_plans "
            "WHERE discipline = %s ORDER BY semester",
            (discipline,),
        )
        if not plan_rows:
            raise NotFoundError(f"Дисциплины «{discipline}» нет в учебном плане")
        total_hours = sum(row["hours"] for row in plan_rows)

    # Оценки выбранного студента
    student_id = request.args.get("student_id", type=int)
    student, my_grades = None, None
    if student_id:
        student = query("SELECT * FROM students WHERE id = %s", (student_id,), one=True)
        if student is None:
            raise NotFoundError(f"Студент с id={student_id} не найден")
        my_grades = query(
            "SELECT g.study_year, p.semester, p.discipline, p.report_form, g.grade "
            "FROM grades g JOIN study_plans p ON p.id = g.plan_id "
            "WHERE g.student_id = %s ORDER BY g.study_year, p.semester, p.discipline",
            (student_id,),
        )

    return render_template(
        "student.html", disciplines=disciplines, students=students,
        discipline=discipline, plan_rows=plan_rows, total_hours=total_hours,
        student=student, my_grades=my_grades,
    )
