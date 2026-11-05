"""Деканат: студенты и учебный план (функции 1 и 3)."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from db import execute, query
from errors import NotFoundError
from validators import (REPORT_FORMS, STUDY_FORMS, validate_plan,
                        validate_student, validate_study_form)

bp = Blueprint("dean", __name__, url_prefix="/dean")


# ---------- Студенты ----------

@bp.route("/students")
def students():
    selected = request.args.get("study_form")
    count = None
    if selected:  # Функция 1: количество студентов формы обучения
        validate_study_form(selected)
        row = query("SELECT COUNT(*) AS cnt FROM students WHERE study_form = %s",
                    (selected,), one=True)
        count = row["cnt"]
    rows = query("SELECT * FROM students ORDER BY last_name, first_name")
    return render_template("students.html", students=rows, study_forms=STUDY_FORMS,
                           selected=selected, count=count)


@bp.route("/students/new", methods=["GET", "POST"])
def student_new():
    if request.method == "POST":
        data = validate_student(request.form)
        execute(
            "INSERT INTO students (last_name, first_name, patronymic, admission_year, "
            "study_form, group_name) VALUES (%(last_name)s, %(first_name)s, "
            "%(patronymic)s, %(admission_year)s, %(study_form)s, %(group_name)s)",
            data,
        )
        flash("Студент добавлен")
        return redirect(url_for("dean.students"))
    return render_template("student_form.html", student=None, study_forms=STUDY_FORMS)


@bp.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
def student_edit(student_id):
    student = query("SELECT * FROM students WHERE id = %s", (student_id,), one=True)
    if student is None:
        raise NotFoundError(f"Студент с id={student_id} не найден")
    if request.method == "POST":
        data = validate_student(request.form)
        data["id"] = student_id
        execute(
            "UPDATE students SET last_name = %(last_name)s, first_name = %(first_name)s, "
            "patronymic = %(patronymic)s, admission_year = %(admission_year)s, "
            "study_form = %(study_form)s, group_name = %(group_name)s WHERE id = %(id)s",
            data,
        )
        flash("Изменения сохранены")
        return redirect(url_for("dean.students"))
    return render_template("student_form.html", student=student, study_forms=STUDY_FORMS)


# ---------- Учебный план ----------

@bp.route("/plans")
def plans():
    rows = query("SELECT * FROM study_plans ORDER BY specialty, semester, discipline")
    return render_template("plans.html", plans=rows)


@bp.route("/plans/new", methods=["GET", "POST"])
def plan_new():
    if request.method == "POST":
        data = validate_plan(request.form)
        execute(
            "INSERT INTO study_plans (specialty, discipline, semester, hours, report_form) "
            "VALUES (%(specialty)s, %(discipline)s, %(semester)s, %(hours)s, %(report_form)s)",
            data,
        )
        flash("Дисциплина добавлена в учебный план")
        return redirect(url_for("dean.plans"))
    return render_template("plan_form.html", plan=None, report_forms=REPORT_FORMS)


@bp.route("/plans/<int:plan_id>/edit", methods=["GET", "POST"])
def plan_edit(plan_id):
    plan = query("SELECT * FROM study_plans WHERE id = %s", (plan_id,), one=True)
    if plan is None:
        raise NotFoundError(f"Запись учебного плана с id={plan_id} не найдена")
    if request.method == "POST":
        data = validate_plan(request.form)
        data["id"] = plan_id
        execute(
            "UPDATE study_plans SET specialty = %(specialty)s, discipline = %(discipline)s, "
            "semester = %(semester)s, hours = %(hours)s, report_form = %(report_form)s "
            "WHERE id = %(id)s",
            data,
        )
        flash("Изменения сохранены")
        return redirect(url_for("dean.plans"))
    return render_template("plan_form.html", plan=plan, report_forms=REPORT_FORMS)
