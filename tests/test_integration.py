import pytest

STUDENT = {
    "last_name": "Тестов", "first_name": "Пётр", "student_no": "9000001",
    "admission_year": "2025", "group_id": "1", "status": "обучается",
}
PLAN = {
    "program_id": "1", "discipline": "Тестовая дисциплина", "semester": "8",
    "hours": "108", "report_form": "зачёт с оценкой",
}
GRADE = {
    "student_id": "1", "plan_id": "3", "attempt_no": "1", "assessed_on": "2025-10-10",
    "grade": "4", "basis_ref": "Ведомость № 3", "record_status": "черновик",
}


def _text(response):
    return response.get_data(as_text=True)


def test_count_students_by_form(client):
    response = client.get("/dean/students", query_string={"study_form": "заочная"})
    assert response.status_code == 200
    assert "Форма «заочная»: <strong>1</strong>" in _text(response)


@pytest.mark.parametrize(("program", "hours"), [(1, 180), (2, 108)])
def test_discipline_hours(client, program, hours):
    response = client.get("/student/", query_string={
        "program_id": program, "discipline": "Дискретная математика",
    })
    assert response.status_code == 200
    assert f"<strong>{hours}</strong> ч." in _text(response)
    assert "<td>экзамен</td>" in _text(response)
    if program == 1:
        assert "<td>зачёт</td>" in _text(response)


def test_add_student(client):
    response = client.post("/dean/students/new", data=STUDENT, follow_redirects=True)
    assert response.status_code == 200
    assert "Студент добавлен" in _text(response)
    assert "9000001" in _text(response)


def test_edit_student(client):
    form = {**STUDENT, "student_no": "2410153", "last_name": "Смирнов",
            "first_name": "Дмитрий", "group_id": "2", "status": "академический отпуск"}
    response = client.post("/dean/students/4/edit", data=form, follow_redirects=True)
    assert response.status_code == 200
    assert "Изменения сохранены" in _text(response)
    assert 'value="академический отпуск" selected' in _text(client.get("/dean/students/4/edit"))


def test_missing_student(client):
    response = client.get("/dean/students/999/edit")
    assert response.status_code == 404
    assert "Студент с id=999 не найден" in _text(response)


def test_add_plan(client):
    response = client.post("/dean/plans/new", data=PLAN, follow_redirects=True)
    assert response.status_code == 200
    assert "Дисциплина добавлена" in _text(response)
    assert "Тестовая дисциплина" in _text(response)


def test_edit_plan(client):
    form = {**PLAN, "discipline": "Базы данных", "hours": "180",
            "semester": "3", "report_form": "экзамен"}
    response = client.post("/dean/plans/5/edit", data=form, follow_redirects=True)
    assert response.status_code == 200
    assert "Изменения сохранены" in _text(response)
    assert 'name="hours" type="number" required min="1" value="180"' in _text(
        client.get("/dean/plans/5/edit")
    )


def test_add_grade(client):
    response = client.post("/teacher/grades/new", data=GRADE, follow_redirects=True)
    assert response.status_code == 200
    assert "Запись добавлена в журнал" in _text(response)
    assert "Ведомость № 3" in _text(response)
    assert "2025/2026" in _text(response)


def test_grade_must_match_form(client):
    response = client.post("/teacher/grades/new", data={**GRADE, "plan_id": "4", "grade": "5"})
    assert response.status_code == 400
    assert "Для формы «зачёт» допустимы оценки" in _text(response)


def test_duplicate_grade(client):
    duplicate = {**GRADE, "plan_id": "1", "assessed_on": "2025-01-20"}
    response = client.post("/teacher/grades/new", data=duplicate)
    assert response.status_code == 400
    assert "уже есть" in _text(response)


def test_edit_grade(client):
    form = {**GRADE, "plan_id": "5", "assessed_on": "2026-01-19", "grade": "3"}
    response = client.post("/teacher/grades/13/edit", data=form, follow_redirects=True)
    assert response.status_code == 200
    assert "Изменения сохранены" in _text(response)
    assert 'value="3" selected' in _text(client.get("/teacher/grades/13/edit"))


def test_average_grade(client):
    response = client.get("/student/", query_string={"student_id": 1})
    assert response.status_code == 200
    assert "Средний балл по итоговым оценкам: <strong>5.00</strong>" in _text(response)
