from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "student_secret_key"


# ---------------- DATABASE ----------------

def init_db():

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # USERS
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    # GRADES
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

        # Проверка пользователя
        c.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )

        existing_user = c.fetchone()

        if existing_user:
            conn.close()
            return "Пользователь уже существует"

        # Хеш пароля
        hashed_password = generate_password_hash(password)

        # Добавление пользователя
        c.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_password)
        )

        conn.commit()

        user_id = c.lastrowid

        # Оценки
        subjects = [
            ("Математика", 95),
            ("Физика", 88),
            ("Программирование", 100),
            ("Английский", 90)
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

        # ЛОГИН ПРЕПОДА
        if username == "teacher" and password == "teacher123":

            session["teacher"] = True

            return redirect("/admin")

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

    # USER
    c.execute(
        "SELECT * FROM users WHERE id=?",
        (session["user_id"],)
    )

    user = c.fetchone()

    # GRADES
    c.execute(
        "SELECT subject, grade FROM grades WHERE user_id=?",
        (session["user_id"],)
    )

    grades = c.fetchall()

    conn.close()

    # AVERAGE
    grades_list = [g[1] for g in grades]

    avg = (
        round(sum(grades_list) / len(grades_list), 2)
        if grades_list else 0
    )

    return render_template(
        "profile.html",
        user=user,
        grades=grades,
        avg=avg
    )


# ---------------- ADMIN PANEL ----------------

@app.route("/admin")
def admin():

    if "teacher" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT id, username FROM users")

    users = c.fetchall()

    students = []

    for user in users:

        user_id = user[0]
        username = user[1]

        c.execute(
            "SELECT subject, grade FROM grades WHERE user_id=?",
            (user_id,)
        )

        grades = c.fetchall()

        grade_dict = {
            "username": username,
            "math": "-",
            "physics": "-",
            "programming": "-",
            "english": "-",
            "average": 0
        }

        grade_values = []

        for subject, grade in grades:

            if subject == "Математика":
                grade_dict["math"] = grade

            elif subject == "Физика":
                grade_dict["physics"] = grade

            elif subject == "Программирование":
                grade_dict["programming"] = grade

            elif subject == "Английский":
                grade_dict["english"] = grade

            grade_values.append(grade)

        if grade_values:

            grade_dict["average"] = round(
                sum(grade_values) / len(grade_values), 2
            )

        students.append(grade_dict)

    conn.close()

    return render_template(
        "admin.html",
        students=students
    )


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
