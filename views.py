from flask import Blueprint, render_template, flash, request, abort, redirect, current_app
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from boss import Boss
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo
import sqlite3
import sys
import traceback
from db import get_db, init_db
from datetime import datetime
from flask import jsonify
from datetime import datetime, timedelta

views = Blueprint('views', __name__)

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register Boss')

def register_boss(username, password):
    try:
        # Hash the password
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')

        # Try to insert the boss into the BOSSES table
        db = get_db()
        db.execute("INSERT INTO BOSSES (USERNAME, PASSWORD_HASH) VALUES (?, ?)", (username, password_hash))
        db.commit()
        return "Boss registered", 200
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500
    



@views.route("/")
@login_required  # Add this decorator to protect the route
def index():
    try:
        # Try to render the home.html template
        return render_template("home.html")
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500
    

@views.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check the username and hashed password
        db = get_db()
        cur = db.execute("SELECT ID, PASSWORD_HASH FROM BOSSES WHERE USERNAME = ?", (username,))
        boss_data = cur.fetchone()

        if boss_data and check_password_hash(boss_data[1], password):
            user = Boss(id=boss_data[0], name=username)
            login_user(user)
            flash('Login successful!', 'success')
            return redirect('/')

        flash('Invalid username or password', 'danger')

    return render_template('login.html')



@views.route("/register", methods=['GET','POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Check if the username is already taken
        db = get_db()
        cur = db.execute("SELECT ID FROM BOSSES WHERE USERNAME = ?", (username,))
        if cur.fetchone():
            flash('Username already taken. Choose another one.', 'danger')
        else:
            # Register the boss
            register_boss(username, password)
            flash('Boss registered successfully!', 'success')
            return redirect('/login')

    return render_template('register.html', form=form)

@views.route('/logout')
@login_required  # Add this decorator to protect the route
def logout():
    logout_user()  # Log out the user
    flash('Logout successful!', 'info')  # Optional: Flash a message
    return redirect('/login')  # Redirect to the login page

# Define a route to add an employee to the database
@views.route("/add_employee", methods=['POST'])
@login_required
def add_employee():
    # id = request.args.get('id')
    name = request.form.get('name')
    surname = request.form.get('surname')
    try:
        # Try to insert the employee into the database
        db = get_db()
        db.execute("INSERT INTO users (NAME, SURNAME) VALUES  (?, ?)", (name, surname))
        db.commit()
        flash('Employee added successfully!', 'success')
        return redirect('/registered_workers')
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500
    
# Delete employee
@views.route("/delete_employee/<id>", methods=['GET'])
@login_required
def delete_employee(id):
    try:
        # Try to delete the employee from the database
        db = get_db()
        db.execute("DELETE FROM users WHERE rfid = ?", (id,))
        db.commit()
        flash(f'Employee with rfid {id} deleted successfully!', 'danger')
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500

    return redirect('/registered_workers')
    
@views.route("/registered_workers")
@login_required
def get_registered_workers():
    try:
        # Try to get registered workers from the database
        db = get_db()
        cur = db.execute("SELECT * FROM USERS")
        workers = [{"id": row[0], "name": row[1], "surname": row[2], "blocked": row[3]} for row in cur.fetchall()]
        return render_template("registered_workers.html", workers=workers)
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500
    
@views.route("/block_employee/<id>", methods=['GET'])
@login_required
def block_employee(id):
    try:
        # Try to update the worker status in the database
        db = get_db()
        db.execute("UPDATE users SET blocked = 1 WHERE rfid = ?", (id,))
        # Add new block to BLOCKADES table that lasts for a very long time (100 years from curdate)
        db.execute("INSERT INTO BLOCKADES (RFID, BLOCKADE_TYPE) VALUES (?, ?)", (id, "MANUAL"))
        db.commit()
        flash(f'Employee with rfid {id} blocked successfully!', 'danger')
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500

    return redirect('/registered_workers')

# Define a route to unblock a worker
@views.route("/unblock_employee/<id>", methods=['GET'])
@login_required
def unblock_employee(id):
    try:
        # Try to update the worker status in the database
        db = get_db()
        db.execute("UPDATE users SET blocked = 0 WHERE rfid = ?", (id,))
        db.commit()
        flash(f'Employee with rfid {id} unblocked successfully!', 'success')
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500

    return redirect('/registered_workers')

# Define a route to render the live_records page
@views.route("/live_records", methods=['GET'])
@login_required
def live_records():
    return render_template("live_records.html")

# Define a route to drop and reload the database
@views.route("/drop_and_reload_database", methods=['POST'])
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

        flash('Database dropped and reloaded successfully!', 'warning')
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500

    return redirect('/register')