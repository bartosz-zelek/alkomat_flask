from flask import Blueprint, jsonify, request, abort
from boss import Boss
from db import get_db
from flask_login import login_required
import sqlite3
import sys
import traceback

api = Blueprint('api', __name__)


# Define a route to get readings from the database
@api.route("/get_readings", defaults={"id": None})
@api.route("/get_readings/<int:id>")
@login_required  # Add this decorator to protect the route
def get_readings(id):
    try:
        count = request.args.get("count", default=50, type=int)
        offset = request.args.get("offset", default=0, type=int)
        # Try to get readings from the database
        db = get_db()
        if id:
            cur = db.execute(
                "SELECT date_time, name, surname, value FROM users INNER JOIN readings ON users.rfid = readings.fk_rfid WHERE users.rfid = ? ORDER BY readings.date_time DESC LIMIT ? OFFSET ?", (id, count, offset)
            )
        else:
            cur = db.execute(
                "SELECT date_time, name, surname, value FROM users INNER JOIN readings ON users.rfid = readings.fk_rfid ORDER BY readings.date_time DESC LIMIT ? OFFSET ?", (count, offset)
            )
        list_of_readings = cur.fetchall()
        return jsonify(list_of_readings), 200
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500
    

@api.route("/check_rfid/<int:rfid>")
def check_rfid(rfid):
    try:
        db = get_db()
        cur = db.execute("SELECT * FROM users WHERE rfid = ?", (rfid,))
        #don't throw when not found
        user = cur.fetchone()
        if user:
            return jsonify({"id": user[0], "name": user[1], "surname": user[2], "blocked": user[3]}), 200
        else:
            abort(404)
    except sqlite3.Error as er:
        abort(404)
