"""Учёт успеваемости студентов — точка входа."""
import logging
import os

from flask import Flask, render_template

from db import close_db
from errors import register_error_hooks
from routes.dean import bp as dean_bp
from routes.student import bp as student_bp
from routes.teacher import bp as teacher_bp


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or os.urandom(16).hex()

    # Логи пишутся в папку logs/ (в Docker она подключается как volume)
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler("logs/app.log", encoding="utf-8"),
                  logging.StreamHandler()],
    )

    app.register_blueprint(dean_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)
    register_error_hooks(app)
    app.teardown_appcontext(close_db)

    @app.route("/")
    def index():
        return render_template("index.html")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
