import sqlite3
import sys
import traceback
from datetime import datetime
from flask import Flask, render_template, g, jsonify

# Define the path to the SQLite database file
DATABASE = "static/database.db"

# Create a Flask application instance
app = Flask(__name__)

# Define the route for the home page
@app.route("/")
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

# Run the Flask app if the script is executed directly
if __name__ == "__main__":
    app.run(debug=True)
