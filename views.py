import os
import shutil
import sqlite3
import sys
import traceback

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
)
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo

from boss import Boss
from db import get_db, init_db
from helpers import add_employee_to_database, run_training

views = Blueprint("views", __name__)


class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Register Boss")


def register_boss(username, password):
    try:
        # Hash the password
        password_hash = generate_password_hash(password, method="pbkdf2:sha256")

        # Check if the username is already taken
        db = get_db()
        cur = db.execute("SELECT ID FROM BOSSES WHERE USERNAME = ?", (username,))
        if cur.fetchone():
            # Username already taken, return error message
            return "Username already taken", 400

        # Try to insert the boss into the BOSSES table
        db.execute(
            "INSERT INTO BOSSES (USERNAME, PASSWORD_HASH) VALUES (?, ?)",
            (username, password_hash),
        )
        db.commit()
        return "Boss registered", 200
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500


@views.route("/")
# @login_required  # Add this decorator to protect the route
def index():
    try:
        if not current_user.is_authenticated:
            return redirect("/login")
        # Try to render the home.html template
        return render_template("home.html")
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500


@views.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Check the username and hashed password
        db = get_db()
        cur = db.execute(
            "SELECT ID, PASSWORD_HASH FROM BOSSES WHERE USERNAME = ?", (username,)
        )
        boss_data = cur.fetchone()

        if boss_data and check_password_hash(boss_data[1], password):
            user = Boss(id=boss_data[0], name=username)
            login_user(user)
            flash("Login successful!", "success")
            try:
                return redirect("/")
            except Exception as e:
                return jsonify({"message": str(e)}), 500

        flash("Invalid username or password", "danger")

    return render_template("login.html")


@views.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Check if the username is already taken
        db = get_db()
        cur = db.execute("SELECT ID FROM BOSSES WHERE USERNAME = ?", (username,))
        if cur.fetchone():
            flash("Username already taken. Choose another one.", "danger")
        else:
            # Register the boss
            register_boss(username, password)
            flash("Boss registered successfully!", "success")
            return redirect("/login")

    return render_template("register.html", form=form)


@views.route("/logout", methods=["POST"])
@login_required  # Add this decorator to protect the route
def logout():
    logout_user()  # Log out the user
    flash("Logout successful!", "info")  # Optional: Flash a message
    return redirect("/login")  # Redirect to the login page


# Define a route to add an employee to the database
@views.route("/add_employee", methods=["POST"])
@login_required
def add_employee():
    # Use add_employee_to_database from api.py
    try:
        user_id = request.form["user_id"]
        name = request.form["name"]
        surname = request.form["surname"]

        # Check if the employee with the given user_id already exists
        db = get_db()
        cur = db.execute("SELECT * FROM USERS WHERE user_id = ?", (user_id,))
        user = cur.fetchone()
        if user:
            # Employee already exists, return error message
            return jsonify({"message": "Employee already exists"}), 400

        # Add employee to database
        add_employee_to_database(user_id, name, surname)
        flash(f"Employee with user_id {user_id} added successfully!", "success")
        return redirect("/registered_workers")
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500


# Delete employee
@views.route("/delete_employee/<id>", methods=["GET"])
@login_required
def delete_employee(id):
    try:
        # Try to delete the employee from the database
        db = get_db()
        db.execute("DELETE FROM users WHERE user_id = ?", (id,))
        db.commit()

        os.system(f"rm -rf /home/bartox7777/alkomat_flask/dataset/{id}")
        run_training()

        flash(f"Employee with user_id {id} deleted successfully!", "danger")
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500

    return redirect("/registered_workers")


@views.route("/registered_workers")
@login_required
def get_registered_workers():
    try:
        # Try to get registered workers from the database
        db = get_db()
        cur = db.execute("SELECT * FROM USERS")
        workers = [
            {"id": row[0], "name": row[1], "surname": row[2], "blocked": row[3]}
            for row in cur.fetchall()
        ]
        return render_template("registered_workers.html", workers=workers)
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500


@views.route("/block_employee/<id>", methods=["GET"])
@login_required
def block_employee(id):
    try:
        # Try to update the worker status in the database
        db = get_db()
        db.execute("UPDATE users SET blocked = 1 WHERE user_id = ?", (id,))
        # Add new block to BLOCKADES table that lasts for a very long time (100 years from curdate)
        db.execute(
            "INSERT INTO BLOCKADES (user_id, BLOCKADE_TYPE, STATUS) VALUES (?, ?, ?)",
            (id, "MANUAL", "ONGOING"),
        )
        db.commit()
        flash(f"Employee with user_id {id} blocked successfully!", "danger")
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500

    return redirect("/registered_workers")


# Define a route to unblock a worker
@views.route("/unblock_employee/<id>", methods=["GET"])
@login_required
def unblock_employee(id):
    try:
        # Try to update the worker status in the database
        db = get_db()
        db.execute("UPDATE users SET blocked = 0 WHERE user_id = ?", (id,))
        db.execute(
            "UPDATE BLOCKADES SET STATUS = 'DONE' WHERE user_id = ? AND STATUS = 'ONGOING'",
            (id,),
        )
        db.commit()
        flash(f"Employee with user_id {id} unblocked successfully!", "success")
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500

    return redirect("/registered_workers")


# Define a route to render the live_records page
@views.route("/live_records", methods=["GET"])
@login_required
def live_records():
    return render_template("live_records.html")


# Define a route to drop and reload the database
@views.route("/drop_and_reload_database", methods=["POST"])
@login_required
def drop_and_reload_database():
    try:
        # Try to drop and reload the database
        with current_app.app_context():
            db = get_db()
            # Drop all tables
            db.execute("DROP TABLE IF EXISTS users")
            db.execute("DROP TABLE IF EXISTS readings")
            db.execute("DROP TABLE IF EXISTS bosses")
            db.execute("DROP TABLE IF EXISTS blockades")

            # Recreate tables and reload the schema
            init_db(current_app)

            # Remove png plots in static folder if they exist
            if os.path.isfile("static/sober_readings_histogram.png"):
                os.remove("static/sober_readings_histogram.png")
                shutil.copy("default_plots/sober_readings_histogram.png", "static")
            if os.path.isfile("static/blocks_number_histogram.png"):
                os.remove("static/blocks_number_histogram.png")
                shutil.copy("default_plots/blocks_number_histogram.png", "static")

        flash("Database dropped and reloaded successfully!", "warning")
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500

    return redirect("/register")


@views.route("/readings_table/<id>")
# @login_required
def readings_table(id):
    # Make a request to the get_readings API
    return render_template("records_for_single_user.html", user_id=id)


@views.route("/statistics")
@login_required
def statistics():
    return render_template("statistics.html")
