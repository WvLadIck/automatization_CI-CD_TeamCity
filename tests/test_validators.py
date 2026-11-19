from datetime import date

import pytest

from errors import ValidationError
from validators import (study_year, validate_grade, validate_plan, validate_student,
                        validate_study_form)

TODAY = date(2026, 11, 18)
STUDENT = {
    "last_name": " Иванов ", "first_name": "Иван", "patronymic": "",
    "student_no": "0241005", "admission_year": "2024", "group_id": "1",
    "status": "обучается",
}
PLAN = {
    "program_id": "1", "discipline": "Физика", "semester": "2",
    "hours": "108", "report_form": "зачёт с оценкой",
}


def test_study_form():
    assert validate_study_form("заочная") == "заочная"
    with pytest.raises(ValidationError, match="Форма обучения"):
        validate_study_form("дневная")


def test_student_normalized():
    data = validate_student(STUDENT, today=TODAY)
    assert data["last_name"] == "Иванов"
    assert data["patronymic"] is None
    assert data["student_no"] == "0241005"
    assert data["admission_year"] == 2024
    assert data["group_id"] == 1


@pytest.mark.parametrize(("field", "value", "message"), [
    ("last_name", " ", "Фамилия"), ("first_name", "", "Имя"),
    ("student_no", "AB123", "Номер зачётной книжки"),
    ("admission_year", "2015", "Год поступления"),
    ("admission_year", "2027", "Год поступления"),
    ("admission_year", "abc", "Год поступления"),
    ("group_id", "0", "Группа"), ("status", "неизвестен", "Статус"),
])
def test_student_invalid(field, value, message):
    with pytest.raises(ValidationError, match=message):
        validate_student({**STUDENT, field: value}, today=TODAY)


def test_plan_normalized():
    assert validate_plan(PLAN) == {
        **PLAN, "program_id": 1, "semester": 2, "hours": 108,
    }


@pytest.mark.parametrize(("field", "value", "message"), [
    ("program_id", "0", "Образовательная программа"),
    ("discipline", " ", "Дисциплина"), ("semester", "15", "Семестр"),
    ("hours", "0", "Количество часов"), ("report_form", "курсовая", "Форма аттестации"),
])
def test_plan_invalid(field, value, message):
    with pytest.raises(ValidationError, match=message):
        validate_plan({**PLAN, field: value})


@pytest.mark.parametrize(("grade", "report_form"), [
    ("5", "экзамен"), ("2", "зачёт с оценкой"),
    ("зачтено", "зачёт"), ("не зачтено", "зачёт"), ("не явился", "экзамен"),
])
def test_grade_valid(grade, report_form):
    assert validate_grade(grade, report_form) == grade


@pytest.mark.parametrize(("grade", "report_form"), [
    ("5", "зачёт"), ("зачтено", "экзамен"),
])
def test_grade_invalid(grade, report_form):
    with pytest.raises(ValidationError, match="допустимы оценки"):
        validate_grade(grade, report_form)


@pytest.mark.parametrize(("day", "expected"), [
    (date(2025, 8, 31), "2024/2025"),
    (date(2025, 9, 1), "2025/2026"),
])
def test_study_year(day, expected):
    assert study_year(day) == expected
