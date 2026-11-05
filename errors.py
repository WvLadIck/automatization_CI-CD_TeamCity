"""Пользовательские исключения и хуки, которые срабатывают на них."""
from flask import render_template


class AppError(Exception):
    """Базовая ошибка приложения."""
    status = 400

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    """Пользователь ввёл некорректные данные."""
    status = 400


class NotFoundError(AppError):
    """Запись не найдена в БД."""
    status = 404


def register_error_hooks(app):
    """Хуки: пишут ошибку в лог и показывают понятную страницу."""

    @app.errorhandler(AppError)
    def handle_app_error(err):
        app.logger.warning("%s: %s", type(err).__name__, err.message)
        return render_template("error.html", message=err.message), err.status

    @app.errorhandler(404)
    def handle_404(_err):
        return render_template("error.html", message="Страница не найдена"), 404
