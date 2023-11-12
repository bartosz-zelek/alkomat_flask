import sqlite3
import sys, traceback
from datetime import datetime
from flask import Flask, render_template, g, jsonify

DATABASE = "static/database.db"

app = Flask(__name__)


@app.route("/")
def index():
    try:
        return render_template("home.html")
    except sqlite3.Error as er:
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500


@app.route("/add_employee/<int:id>/<name>/<surname>")
def add_employee(id, name, surname):
    try:
        db = get_db()
        db.execute("INSERT INTO users VALUES (?, ?, ?)", (id, name, surname))
        db.commit()
        return "Added", 200
    except sqlite3.Error as er:
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500


@app.route("/add_reading/<rfid>/<float:value>")
def add_reading(rfid, value):
    try:
        db = get_db()
        db.execute(
            "INSERT INTO readings (fk_rfid, date_time, value) VALUES (?, ?, ?)",
            (rfid, datetime.now(), value),
        )
        db.commit()
        return "Added", 200
    except sqlite3.Error as er:
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500


@app.route("/get_readings/<rfid>")
def get_readings(rfid):
    try:
        if rfid == "all":
            db = get_db()
            cur = db.execute(
                "SELECT date_time, name, surname, value FROM users INNER JOIN readings ON users.rfid = readings.fk_rfid ORDER BY readings.date_time DESC"
            )
            list_of_readings = cur.fetchall()
            return jsonify(list_of_readings), 200
    except sqlite3.Error as er:
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        with open("static/schema.sql", mode="r") as f:
            db.cursor().executescript(f.read())
        db.execute("INSERT INTO users VALUES (?, ?, ?)", ("1", "Bartosz", "Żelek"))
        db.execute(
            "INSERT INTO readings VALUES (?, ?, ?, ?)", ("1", "1", datetime.now(), 0.2)
        )
        db.commit()
