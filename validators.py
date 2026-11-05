"""Проверка данных форм. Чистые функции — их удобно покрыть тестами в ЛР7.

Повторяют ограничения БД, чтобы пользователь сразу видел понятную ошибку.
"""
import re
from datetime import date

from errors import ValidationError

MIN_YEAR = 2016  # год создания Московского Политеха
STUDY_FORMS = ("очная", "очно-заочная", "заочная")
REPORT_FORMS = ("экзамен", "зачёт", "зачёт с оценкой")
STUDENT_STATUSES = ("обучается", "академический отпуск", "отпуск по беременности и родам",
                    "отпуск по уходу за ребёнком", "отчислен", "выпускник")
EXAM_GRADES = ("5", "4", "3", "2")
CREDIT_GRADES = ("зачтено", "не зачтено")
NO_SHOW = "не явился"
ALL_GRADES = EXAM_GRADES + CREDIT_GRADES + (NO_SHOW,)
ATTEMPTS = (1, 2, 3)
RECORD_STATUSES = ("черновик", "зафиксирован")

DIRECTION_CODE_RE = r"[0-9]{2}\.0[345]\.[0-9]{2}"
GROUP_NAME_RE = r"[0-9]{3}-[0-9]{3,4}"
STUDENT_NO_RE = r"[0-9]{1,10}"


def _text(form, field, title, required=True, max_len=150):
    value = (form.get(field) or "").strip()
    if required and not value:
        raise ValidationError(f"Поле «{title}» обязательно")
    if len(value) > max_len:
        raise ValidationError(f"Поле «{title}» длиннее {max_len} символов")
    return value or None


def _int(form, field, title, low, high):
    value = (form.get(field) or "").strip()
    if not value.isdigit():
        raise ValidationError(f"Поле «{title}» должно быть целым числом")
    number = int(value)
    if not low <= number <= high:
        raise ValidationError(f"Поле «{title}» должно быть от {low} до {high}")
    return number


def _choice(value, allowed, title):
    if value not in allowed:
        raise ValidationError(f"Поле «{title}»: допустимо {', '.join(map(str, allowed))}")
    return value


def _pattern(value, regex, title, example):
    if not re.fullmatch(regex, value or ""):
        raise ValidationError(f"Поле «{title}» должно иметь вид {example}")
    return value


def _year(form, field, title, today=None):
    current = (today or date.today()).year
    return _int(form, field, title, MIN_YEAR, current)


def validate_study_form(value):
    return _choice(value, STUDY_FORMS, "Форма обучения")


def validate_program(form, today=None):
    return {
        "direction_code": _pattern((form.get("direction_code") or "").strip(),
                                   DIRECTION_CODE_RE, "Код направления", "09.03.01"),
        "profile": _text(form, "profile", "Профиль"),
        "cohort_year": _year(form, "cohort_year", "Год набора", today),
        "study_form": validate_study_form(form.get("study_form")),
        "revision_no": _int(form, "revision_no", "Версия плана", 1, 32767),
        "semester_count": _int(form, "semester_count", "Количество семестров", 1, 14),
    }


def validate_group(form):
    return {
        "group_name": _pattern((form.get("group_name") or "").strip(),
                               GROUP_NAME_RE, "Номер группы", "241-326 или 241-3210"),
        "program_id": _int(form, "program_id", "Образовательная программа", 1, 2**31 - 1),
    }


def validate_student(form, today=None):
    return {
        "last_name": _text(form, "last_name", "Фамилия", max_len=60),
        "first_name": _text(form, "first_name", "Имя", max_len=60),
        "patronymic": _text(form, "patronymic", "Отчество", required=False, max_len=60),
        "student_no": _pattern((form.get("student_no") or "").strip(), STUDENT_NO_RE,
                               "Номер зачётной книжки", "до 10 цифр, например 2410001"),
        "admission_year": _year(form, "admission_year", "Год поступления", today),
        "group_id": _int(form, "group_id", "Группа", 1, 2**31 - 1),
        "status": _choice(form.get("status"), STUDENT_STATUSES, "Статус"),
    }


def validate_plan(form):
    return {
        "program_id": _int(form, "program_id", "Образовательная программа", 1, 2**31 - 1),
        "discipline": _text(form, "discipline", "Дисциплина"),
        "semester": _int(form, "semester", "Семестр", 1, 14),
        "hours": _int(form, "hours", "Количество часов", 1, 32767),
        "report_form": _choice(form.get("report_form"), REPORT_FORMS, "Форма аттестации"),
    }


def validate_semester(semester, semester_count):
    """Семестр не позже последнего семестра программы."""
    if semester > semester_count:
        raise ValidationError(
            f"Семестр {semester} выходит за пределы программы (семестров: {semester_count})")
    return semester


def validate_date(value, today=None):
    """Дата сдачи: существующая дата не раньше 2016 года и не в будущем."""
    try:
        result = date.fromisoformat((value or "").strip())
    except ValueError as exc:
        raise ValidationError("Укажите существующую дату сдачи") from exc
    if not date(MIN_YEAR, 1, 1) <= result <= (today or date.today()):
        raise ValidationError(f"Дата сдачи должна быть с {MIN_YEAR} года и не позже сегодняшней")
    return result


def validate_grade(grade, report_form):
    """Экзамен и зачёт с оценкой — 2–5, зачёт — зачтено/не зачтено; неявка — для любой формы."""
    allowed = (CREDIT_GRADES if report_form == "зачёт" else EXAM_GRADES) + (NO_SHOW,)
    if grade not in allowed:
        raise ValidationError(
            f"Для формы «{report_form}» допустимы оценки: {', '.join(allowed)}")
    return grade


def validate_grade_form(form, today=None):
    """Поля записи журнала, которые проверяются без обращения к БД."""
    return {
        "student_id": _int(form, "student_id", "Студент", 1, 2**31 - 1),
        "plan_id": _int(form, "plan_id", "Дисциплина", 1, 2**31 - 1),
        "attempt_no": _int(form, "attempt_no", "Номер попытки", 1, 3),
        "assessed_on": validate_date(form.get("assessed_on"), today),
        "grade": _choice(form.get("grade"), ALL_GRADES, "Оценка"),
        "basis_ref": _text(form, "basis_ref", "Основание", max_len=64),
        "record_status": _choice(form.get("record_status"), RECORD_STATUSES, "Состояние записи"),
    }


def study_year(day):
    """Учебный год по дате: сентябрь–декабрь — год начала, январь–август — предыдущий."""
    start = day.year if day.month >= 9 else day.year - 1
    return f"{start}/{start + 1}"


def credit_units(hours):
    """Зачётные единицы: 1 з.е. = 36 академических часов."""
    return round(hours / 36, 2)
