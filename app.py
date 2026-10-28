
import os
from functools import wraps
from io import BytesIO

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify, send_file
)
from werkzeug.security import generate_password_hash, check_password_hash

import config

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "local-development-key-change-me"
)

# Use only for local HTTP development.
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False


def get_db():
    return config.connect()


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper


def fetch_all(sql, params=()):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()


def fetch_one(sql, params=()):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(sql, params)
        return cursor.fetchone()
    finally:
        cursor.close()
        db.close()


def ensure_user_table():
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL
            )
        """)
        db.commit()
    finally:
        cursor.close()
        db.close()


@app.route("/")
@login_required
def home():
    return render_template("index.html", username=session.get("username"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or len(password) < 8:
            flash("Enter a username and a password of at least 8 characters.")
            return render_template("register.html")

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute(
                "INSERT INTO app_users (username, password_hash) VALUES (%s, %s)",
                (username, generate_password_hash(password))
            )
            db.commit()
        except Exception:
            db.rollback()
            flash("Registration failed. That username may already exist.")
            return render_template("register.html")
        finally:
            cursor.close()
            db.close()

        flash("Registration successful. Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = fetch_one(
            "SELECT user_id, username, password_hash FROM app_users WHERE username = %s",
            (username,)
        )

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            return redirect(url_for("home"))

        flash("Incorrect username or password.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# API routes for dashboard data
@app.route("/patients")
@login_required
def patients():
    return jsonify(fetch_all("SELECT * FROM patients"))


@app.route("/visits")
@login_required
def visits():
    return jsonify(fetch_all("SELECT * FROM visits"))


@app.route("/measurements")
@login_required
def measurements():
    return jsonify(fetch_all("SELECT * FROM measurements"))


@app.route("/risk-indicators")
@login_required
def risk_indicators():
    return jsonify(fetch_all("SELECT * FROM risk_indicators"))


@app.route("/analytics/departments")
@login_required
def department_analytics():
    sql = """
        SELECT d.department_name,
               COUNT(v.visit_id) AS total_visits
        FROM departments d
        LEFT JOIN visits v ON d.department_id = v.department_id
        GROUP BY d.department_id, d.department_name
        ORDER BY total_visits DESC
    """
    return jsonify(fetch_all(sql))


@app.route("/department-chart")
@login_required
def department_chart():
    data = fetch_all("""
        SELECT d.department_name,
               COUNT(v.visit_id) AS total_visits
        FROM departments d
        LEFT JOIN visits v ON d.department_id = v.department_id
        GROUP BY d.department_id, d.department_name
        ORDER BY total_visits DESC
    """)

    names = [row["department_name"] for row in data]
    counts = [int(row["total_visits"]) for row in data]

    fig, ax = plt.subplots(figsize=(9, 5))
    try:
        ax.bar(names, counts)
        ax.set_title("Hospital Department Visit Analytics")
        ax.set_xlabel("Department")
        ax.set_ylabel("Total Visits")
        ax.tick_params(axis="x", rotation=25)
        fig.tight_layout()

        image = BytesIO()
        fig.savefig(image, format="png", dpi=120)
        image.seek(0)
        return send_file(image, mimetype="image/png")
    finally:
        plt.close(fig)


@app.route("/predict-diabetes", methods=["POST"])
@login_required
def predict_diabetes():
    # This endpoint validates the form, but does not claim to predict
    # diabetes until a trained and validated model is connected.
    try:
        glucose = float(request.form["glucose"])
        bmi = float(request.form["bmi"])
        age = int(request.form["age"])
    except (KeyError, ValueError):
        return jsonify({"error": "Enter valid glucose, BMI, and age values."}), 400

    if glucose <= 0 or bmi <= 0 or age <= 0:
        return jsonify({"error": "All values must be greater than zero."}), 400

    return jsonify({
        "message": "Inputs accepted. Connect a trained model before showing a risk prediction.",
        "inputs": {"glucose": glucose, "bmi": bmi, "age": age}
    })


if __name__ == "__main__":
    ensure_user_table()
    app.run(debug=True)
