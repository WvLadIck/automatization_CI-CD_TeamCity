"""Деканат: программы, группы, студенты и учебный план (функции 1 и 3)."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from db import execute, query
from errors import NotFoundError
from validators import (REPORT_FORMS, STUDENT_STATUSES, STUDY_FORMS, credit_units,
                        validate_group, validate_plan, validate_program, validate_semester,
                        validate_student, validate_study_form)

bp = Blueprint("dean", __name__, url_prefix="/dean")

PROGRAMS_SQL = ("SELECT * FROM educational_programs "
                "ORDER BY direction_code, profile, cohort_year DESC, study_form, revision_no")
GROUPS_SQL = """
    SELECT g.id, g.group_name, g.program_id, p.direction_code, p.profile,
           p.cohort_year, p.study_form, p.revision_no
    FROM student_groups g JOIN educational_programs p ON p.id = g.program_id
    ORDER BY g.group_name
"""


def _get_or_404(sql, item_id, message):
    row = query(sql, (item_id,), one=True)
    if row is None:
        raise NotFoundError(message)
    return row


# ---------- Образовательные программы ----------

@bp.route("/programs")
def programs():
    return render_template("programs.html", programs=query(PROGRAMS_SQL))


@bp.route("/programs/new", methods=["GET", "POST"])
def program_new():
    if request.method == "POST":
        data = validate_program(request.form)
        execute(
            "INSERT INTO educational_programs (direction_code, profile, cohort_year, "
            "study_form, revision_no, semester_count) VALUES (%(direction_code)s, "
            "%(profile)s, %(cohort_year)s, %(study_form)s, %(revision_no)s, %(semester_count)s)",
            data,
        )
        flash("Программа добавлена")
        return redirect(url_for("dean.programs"))
    return render_template("program_form.html", program=None, study_forms=STUDY_FORMS)


@bp.route("/programs/<int:program_id>/edit", methods=["GET", "POST"])
def program_edit(program_id):
    program = _get_or_404("SELECT * FROM educational_programs WHERE id = %s", program_id,
                          f"Программа с id={program_id} не найдена")
    if request.method == "POST":
        data = validate_program(request.form)
        data["id"] = program_id
        execute(
            "UPDATE educational_programs SET direction_code = %(direction_code)s, "
            "profile = %(profile)s, cohort_year = %(cohort_year)s, study_form = %(study_form)s, "
            "revision_no = %(revision_no)s, semester_count = %(semester_count)s "
            "WHERE id = %(id)s",
            data,
        )
        flash("Изменения сохранены")
        return redirect(url_for("dean.programs"))
    return render_template("program_form.html", program=program, study_forms=STUDY_FORMS)


# ---------- Учебные группы ----------

@bp.route("/groups")
def groups():
    return render_template("groups.html", groups=query(GROUPS_SQL))


@bp.route("/groups/new", methods=["GET", "POST"])
def group_new():
    if request.method == "POST":
        data = validate_group(request.form)
        execute("INSERT INTO student_groups (group_name, program_id) "
                "VALUES (%(group_name)s, %(program_id)s)", data)
        flash("Группа добавлена")
        return redirect(url_for("dean.groups"))
    return render_template("group_form.html", group=None, programs=query(PROGRAMS_SQL))


@bp.route("/groups/<int:group_id>/edit", methods=["GET", "POST"])
def group_edit(group_id):
    group = _get_or_404("SELECT * FROM student_groups WHERE id = %s", group_id,
                        f"Группа с id={group_id} не найдена")
    if request.method == "POST":
        data = validate_group(request.form)
        data["id"] = group_id
        execute("UPDATE student_groups SET group_name = %(group_name)s, "
                "program_id = %(program_id)s WHERE id = %(id)s", data)
        flash("Изменения сохранены")
        return redirect(url_for("dean.groups"))
    return render_template("group_form.html", group=group, programs=query(PROGRAMS_SQL))


# ---------- Студенты ----------

@bp.route("/students")
def students():
    selected = request.args.get("study_form")
    count = None
    if selected:  # Функция 1: количество обучающихся по форме обучения
        validate_study_form(selected)
        row = query(
            "SELECT COUNT(*) AS cnt FROM students s "
            "JOIN student_groups g ON g.id = s.group_id "
            "JOIN educational_programs p ON p.id = g.program_id "
            "WHERE p.study_form = %s AND s.status = 'обучается'",
            (selected,), one=True,
        )
        count = row["cnt"]
    rows = query(
        "SELECT s.*, g.group_name, p.study_form FROM students s "
        "JOIN student_groups g ON g.id = s.group_id "
        "JOIN educational_programs p ON p.id = g.program_id "
        "ORDER BY s.last_name, s.first_name"
    )
    return render_template("students.html", students=rows, study_forms=STUDY_FORMS,
                           selected=selected, count=count)


def _student_form(student):
    return render_template("student_form.html", student=student, groups=query(GROUPS_SQL),
                           statuses=STUDENT_STATUSES)


@bp.route("/students/new", methods=["GET", "POST"])
def student_new():
    if request.method == "POST":
        data = validate_student(request.form)
        execute(
            "INSERT INTO students (last_name, first_name, patronymic, student_no, "
            "admission_year, group_id, status) VALUES (%(last_name)s, %(first_name)s, "
            "%(patronymic)s, %(student_no)s, %(admission_year)s, %(group_id)s, %(status)s)",
            data,
        )
        flash("Студент добавлен")
        return redirect(url_for("dean.students"))
    return _student_form(None)


@bp.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
def student_edit(student_id):
    student = _get_or_404("SELECT * FROM students WHERE id = %s", student_id,
                          f"Студент с id={student_id} не найден")
    if request.method == "POST":
        data = validate_student(request.form)
        data["id"] = student_id
        execute(
            "UPDATE students SET last_name = %(last_name)s, first_name = %(first_name)s, "
            "patronymic = %(patronymic)s, student_no = %(student_no)s, "
            "admission_year = %(admission_year)s, group_id = %(group_id)s, "
            "status = %(status)s WHERE id = %(id)s",
            data,
        )
        flash("Изменения сохранены")
        return redirect(url_for("dean.students"))
    return _student_form(student)


# ---------- Учебный план ----------

@bp.route("/plans")
def plans():
    rows = query(
        "SELECT sp.*, p.direction_code, p.profile, p.cohort_year, p.study_form, p.revision_no "
        "FROM study_plans sp JOIN educational_programs p ON p.id = sp.program_id "
        "ORDER BY p.direction_code, p.profile, p.cohort_year DESC, p.study_form, "
        "p.revision_no, sp.semester, sp.discipline"
    )
    for row in rows:
        row["credits"] = credit_units(row["hours"])
    return render_template("plans.html", plans=rows)


def _validated_plan(form):
    data = validate_plan(form)
    program = _get_or_404("SELECT semester_count FROM educational_programs WHERE id = %s",
                          data["program_id"], "Выбранная программа не найдена")
    validate_semester(data["semester"], program["semester_count"])
    return data


def _plan_form(plan):
    return render_template("plan_form.html", plan=plan, programs=query(PROGRAMS_SQL),
                           report_forms=REPORT_FORMS)


@bp.route("/plans/new", methods=["GET", "POST"])
def plan_new():
    if request.method == "POST":
        data = _validated_plan(request.form)
        execute(
            "INSERT INTO study_plans (program_id, discipline, semester, hours, report_form) "
            "VALUES (%(program_id)s, %(discipline)s, %(semester)s, %(hours)s, %(report_form)s)",
            data,
        )
        flash("Дисциплина добавлена в учебный план")
        return redirect(url_for("dean.plans"))
    return _plan_form(None)


@bp.route("/plans/<int:plan_id>/edit", methods=["GET", "POST"])
def plan_edit(plan_id):
    plan = _get_or_404("SELECT * FROM study_plans WHERE id = %s", plan_id,
                       f"Запись учебного плана с id={plan_id} не найдена")
    if request.method == "POST":
        data = _validated_plan(request.form)
        data["id"] = plan_id
        execute(
            "UPDATE study_plans SET program_id = %(program_id)s, discipline = %(discipline)s, "
            "semester = %(semester)s, hours = %(hours)s, report_form = %(report_form)s "
            "WHERE id = %(id)s",
            data,
        )
        flash("Изменения сохранены")
        return redirect(url_for("dean.plans"))
    return _plan_form(plan)
