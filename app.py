import sqlite3
import sys
import traceback
from datetime import datetime
from flask import Flask, render_template, g, jsonify, flash, request, abort, redirect
from flask_login import login_user, login_required, logout_user, current_user, LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
from boss import Boss
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo



# Define the path to the SQLite database file
DATABASE = "static/database.db"

# Create a Flask application instance
app = Flask(__name__)
app.secret_key = b"123456789"

login_manager = LoginManager(app)

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

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register Boss')

@app.route("/register", methods=['GET','POST'])
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

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    cur = db.execute("SELECT USERNAME FROM BOSSES WHERE ID = ?", (user_id,))
    boss_data = cur.fetchone()
    if boss_data:
        return Boss(id=user_id, name=boss_data[0])
    return None

# Updated login route
@app.route('/login', methods=['GET', 'POST'])
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

@app.route('/logout')
@login_required  # Add this decorator to protect the route
def logout():
    logout_user()  # Log out the user
    flash('Logout successful!', 'info')  # Optional: Flash a message
    return redirect('/login')  # Redirect to the login page

# Define the route for the home page
@app.route("/")
@login_required  # Add this decorator to protect the route
def index():
    try:
        # Try to render the home.html template
        return render_template("home.html")
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500

# Define a route to add an employee to the database
@app.route("/add_employee/<int:id>/<name>/<surname>")
def add_employee(id, name, surname):
    try:
        # Try to insert the employee into the database
        db = get_db()
        db.execute("INSERT INTO users VALUES (?, ?, ?)", (id, name, surname))
        db.commit()
        return "Added", 200
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500

# Define a route to add a reading to the database
@app.route("/add_reading/<rfid>/<float:value>")
def add_reading(rfid, value):
    try:
        # Try to insert the reading into the database
        db = get_db()
        db.execute(
            "INSERT INTO readings (fk_rfid, date_time, value) VALUES (?, ?, ?)",
            (rfid, datetime.now(), value),
        )
        db.commit()
        return "Added", 200
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500

# Define a route to get readings from the database
@app.route("/get_readings/<rfid>")
@login_required  # Add this decorator to protect the route
def get_readings(rfid):
    try:
        # Try to get readings from the database
        if rfid == "all":
            db = get_db()
            cur = db.execute(
                "SELECT date_time, name, surname, value FROM users INNER JOIN readings ON users.rfid = readings.fk_rfid ORDER BY readings.date_time DESC"
            )
            list_of_readings = cur.fetchall()
            return jsonify(list_of_readings), 200
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500

# Function to get a database connection
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Function to close the database connection when the app context is torn down
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

# Function to initialize the database with some initial data
def init_db():
    with app.app_context():
        db = get_db()
        with open("static/schema.sql", mode="r") as f:
            db.cursor().executescript(f.read())
        db.commit()
        print("Initialization complete.")

# Run the Flask app if the script is executed directly
if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True)

