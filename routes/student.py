"""Студент: часы и форма аттестации по дисциплине (функция 2), свои оценки."""
from flask import Blueprint, render_template, request

from db import query
from errors import NotFoundError
from validators import credit_units, study_year

bp = Blueprint("student", __name__, url_prefix="/student")


@bp.route("/")
def index():
    disciplines = query("SELECT DISTINCT discipline FROM study_plans ORDER BY discipline")
    programs = query("SELECT * FROM educational_programs "
                     "ORDER BY direction_code, profile, cohort_year DESC, study_form, revision_no")
    students = query("SELECT s.id, s.last_name, s.first_name, g.group_name "
                     "FROM students s JOIN student_groups g ON g.id = s.group_id "
                     "ORDER BY s.last_name, s.first_name")

    # Функция 2: часы и формы аттестации по дисциплине в программе
    discipline = (request.args.get("discipline") or "").strip()
    program_id = request.args.get("program_id", type=int)
    plan_rows, total_hours = None, None
    if discipline and program_id:
        plan_rows = query(
            "SELECT semester, hours, report_form FROM study_plans "
            "WHERE discipline = %s AND program_id = %s ORDER BY semester",
            (discipline, program_id),
        )
        if not plan_rows:
            raise NotFoundError(f"Дисциплины «{discipline}» нет в плане выбранной программы")
        for row in plan_rows:
            row["credits"] = credit_units(row["hours"])
        total_hours = sum(row["hours"] for row in plan_rows)

    # Результаты аттестации выбранного студента
    student_id = request.args.get("student_id", type=int)
    student, my_grades = None, None
    if student_id:
        student = query("SELECT * FROM students WHERE id = %s", (student_id,), one=True)
        if student is None:
            raise NotFoundError(f"Студент с id={student_id} не найден")
        my_grades = query(
            "SELECT g.assessed_on, g.attempt_no, g.grade, g.record_status, "
            "p.semester, p.discipline, p.report_form "
            "FROM grades g JOIN study_plans p ON p.id = g.plan_id "
            "WHERE g.student_id = %s ORDER BY g.assessed_on, p.discipline, g.attempt_no",
            (student_id,),
        )
        for row in my_grades:
            row["study_year"] = study_year(row["assessed_on"])

    return render_template(
        "student.html", disciplines=disciplines, programs=programs, students=students,
        discipline=discipline, program_id=program_id, plan_rows=plan_rows,
        total_hours=total_hours, total_credits=credit_units(total_hours or 0),
        student=student, my_grades=my_grades,
    )
