"""Проверка данных форм. Чистые функции — их удобно покрыть тестами в ЛР7."""
import re

from errors import ValidationError

STUDY_FORMS = ("дневная", "вечерняя", "заочная")
REPORT_FORMS = ("экзамен", "зачёт")
EXAM_GRADES = ("5", "4", "3", "2")
CREDIT_GRADES = ("зачёт", "незачёт")


def _text(form, field, title, required=True, max_len=100):
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


def validate_study_form(value):
    if value not in STUDY_FORMS:
        raise ValidationError("Форма обучения: дневная, вечерняя или заочная")
    return value


def validate_student(form):
    return {
        "last_name": _text(form, "last_name", "Фамилия", max_len=50),
        "first_name": _text(form, "first_name", "Имя", max_len=50),
        "patronymic": _text(form, "patronymic", "Отчество", required=False, max_len=50),
        "admission_year": _int(form, "admission_year", "Год поступления", 1990, 2100),
        "study_form": validate_study_form(form.get("study_form")),
        "group_name": _text(form, "group_name", "Группа", max_len=20),
    }


def validate_plan(form):
    report_form = form.get("report_form")
    if report_form not in REPORT_FORMS:
        raise ValidationError("Форма отчётности: экзамен или зачёт")
    return {
        "specialty": _text(form, "specialty", "Специальность"),
        "discipline": _text(form, "discipline", "Дисциплина"),
        "semester": _int(form, "semester", "Семестр", 1, 12),
        "hours": _int(form, "hours", "Количество часов", 1, 1000),
        "report_form": report_form,
    }


def validate_study_year(value):
    """Учебный год в формате 2025/2026."""
    value = (value or "").strip()
    match = re.fullmatch(r"(\d{4})/(\d{4})", value)
    if not match or int(match.group(2)) != int(match.group(1)) + 1:
        raise ValidationError("Учебный год указывается в формате 2025/2026")
    return value


def validate_grade(grade, report_form):
    """Для экзамена — оценка 2–5, для зачёта — зачёт/незачёт."""
    allowed = EXAM_GRADES if report_form == "экзамен" else CREDIT_GRADES
    if grade not in allowed:
        raise ValidationError(
            f"Для формы «{report_form}» допустимы оценки: {', '.join(allowed)}"
        )
    return grade
