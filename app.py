from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret_key_123"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT,
            group_name TEXT
        )
    """)

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
    if "user_id" in session:
        return redirect("/profile")
    return redirect("/login")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        email = request.form["email"]
        group_name = request.form["group_name"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        try:
            c.execute("""
                INSERT INTO users (username, password, email, group_name)
                VALUES (?, ?, ?, ?)
            """, (username, password, email, group_name))

            user_id = c.lastrowid

            # 🔥 стартовые оценки (чтобы не было пусто)
            subjects = ["Math", "Physics", "IT"]
            grades = [85, 90, 95]

            for s, g in zip(subjects, grades):
                c.execute("""
                    INSERT INTO grades (user_id, subject, grade)
                    VALUES (?, ?, ?)
                """, (user_id, s, g))

            conn.commit()

        except:
            return "User already exists"

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
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            return redirect("/profile")

        return "Wrong username or password"

    return render_template("login.html")

# ---------------- PROFILE ----------------
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # user info
    c.execute("SELECT * FROM users WHERE id=?", (session["user_id"],))
    user = c.fetchone()

    # grades
    c.execute("SELECT subject, grade FROM grades WHERE user_id=?", (session["user_id"],))
    grades = c.fetchall()

    conn.close()

    # 🔥 FIX: защита от пустых оценок
    grades_list = [g[1] for g in grades]
    avg = sum(grades_list) / len(grades_list) if grades_list else 0

    return render_template("profile.html", user=user, grades=grades, avg=avg)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/login")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
