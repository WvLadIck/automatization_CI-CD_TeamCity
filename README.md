# Учёт успеваемости студентов

Веб-приложение для учёта контингента студентов, учебного плана и журнала успеваемости.
Учебный проект по дисциплине «Автоматизация процессов жизненного цикла программных средств».

## Функционал

| № | Требование | Где в приложении |
|---|---|---|
| 1 | Количество студентов указанной формы обучения | Деканат → Студенты |
| 2 | Часы и формы отчётности по указанной дисциплине | Студент |
| 3 | Добавление и изменение студентов, учебных планов, журнала | Деканат, Преподаватель |
| 4 | Добавление и изменение записей журнала успеваемости | Преподаватель |

Пользовательские исключительные ситуации обрабатываются хуками (`errors.py`):
ошибка записывается в `logs/app.log`, пользователь видит понятное сообщение.
Примеры: оценка «5» по зачёту, учебный год не в формате 2025/2026, несуществующий студент.

## Роли пользователей

- **Деканат** – студенты и учебный план (`routes/dean.py`)
- **Преподаватель** — журнал успеваемости (`routes/teacher.py`)
- **Студент** — часы по дисциплинам и свои оценки (`routes/student.py`)

## База данных

PostgreSQL, 3 таблицы (`db/schema.sql`):

- `students` — ФИО, год поступления, форма обучения, группа
- `study_plans` — специальность, дисциплина, семестр, часы, форма отчётности
- `grades` — учебный год, студент, дисциплина (из учебного плана), оценка

Тестовые данные — `db/seed.sql`.

## Структура проекта

```
app.py              точка входа
db.py               подключение к БД
errors.py           пользовательские исключения и хуки
validators.py       проверка данных форм
routes/             страницы по ролям
templates/          HTML-шаблоны
db/                 схема и тестовые данные БД
Dockerfile          сборка образа приложения
docker-compose.yaml приложение + PostgreSQL
```

## Запуск в Docker 

```bash
cp .env.example .env        # задайте свой пароль в .env
docker compose up -d --build 
```

Приложение: http://localhost:5000
Данные БД хранятся в `db/data/`, логи — в `logs/`.

## Запуск без Docker (Ubuntu)

```bash
sudo apt install -y python3 python3-venv postgresql
sudo -u postgres psql -c "CREATE USER app_user WITH PASSWORD 'ваш_пароль';"
sudo -u postgres psql -c "CREATE DATABASE students OWNER app_user;"
PGPASSWORD='ваш_пароль' psql -h localhost -U app_user -d students -f db/schema.sql
PGPASSWORD='ваш_пароль' psql -h localhost -U app_user -d students -f db/seed.sql

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL='postgresql://app_user:ваш_пароль@localhost:5432/students'
python3 app.py
```

## Команда

Группа 241-326: Соловьева А. Н., Набиуллин А. Ф., Усанов В. Н.

## Лицензия

MIT — см. файл [LICENSE](LICENSE).
