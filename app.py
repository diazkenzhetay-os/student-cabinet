from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "student_secret_key"


# ---------------- DATABASE ----------------

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Таблица пользователей
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # Таблица оценок
    c.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject TEXT,
            grade INTEGER
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ---------------- HOME ----------------

@app.route("/")
def home():
    return redirect("/login")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        # Проверяем существует ли пользователь
        c.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )

        existing_user = c.fetchone()

        if existing_user:
            conn.close()
            return "Пользователь уже существует"

        # Хешируем пароль
        hashed_password = generate_password_hash(password)

        # Добавляем пользователя
        c.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_password)
        )

        conn.commit()

        # Получаем ID пользователя
        user_id = c.lastrowid

        # Добавляем пример оценок
        subjects = [
            ("Mathematics", 95),
            ("Physics", 88),
            ("Programming", 100),
            ("English", 90)
        ]

        for subject, grade in subjects:
            c.execute(
                "INSERT INTO grades (user_id, subject, grade) VALUES (?, ?, ?)",
                (user_id, subject, grade)
            )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )

        user = c.fetchone()

        conn.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            return redirect("/profile")

        return "Неверный логин или пароль"

    return render_template("login.html")


# ---------------- PROFILE ----------------

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Пользователь
    c.execute(
        "SELECT * FROM users WHERE id=?",
        (session["user_id"],)
    )

    user = c.fetchone()

    # Оценки
    c.execute(
        "SELECT subject, grade FROM grades WHERE user_id=?",
        (session["user_id"],)
    )

    grades = c.fetchall()

    conn.close()

    # Средний балл
    grades_list = [g[1] for g in grades]

    avg = (
        sum(grades_list) / len(grades_list)
        if grades_list else 0
    )

    return render_template(
        "profile.html",
        user=user,
        grades=grades,
        avg=avg
    )


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
