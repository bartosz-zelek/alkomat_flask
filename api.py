from flask import Blueprint, jsonify, request, abort, current_app
from db import get_db
from flask_login import login_required
import sqlite3
import sys
import traceback
from datetime import datetime, timedelta

api = Blueprint('api', __name__)


# Define a route to get readings from the database
@api.route("/get_readings", defaults={"id": None})
@api.route("/get_readings/<int:id>")
#@login_required  # Add this decorator to protect the route
def get_readings(id):
    try:
        count = request.args.get("count", default=50, type=int)
        offset = request.args.get("offset", default=0, type=int)
        # Try to get readings from the database
        db = get_db()
        if id:
            cur = db.execute(
                "SELECT date_time, name, surname, value FROM users INNER JOIN readings ON users.rfid = readings.rfid WHERE users.rfid = ? ORDER BY readings.date_time DESC LIMIT ? OFFSET ?", (id, count, offset)
            )
            list_of_readings = cur.fetchall()
            return jsonify(list_of_readings)
        else:
            cur = db.execute(
                "SELECT date_time, name, surname, value FROM users INNER JOIN readings ON users.rfid = readings.rfid ORDER BY readings.date_time DESC LIMIT ? OFFSET ?", (count, offset)
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


# Define a route to add a reading to the database
@api.route("/add_reading/<rfid>/<float:value>", methods=['GET'])
def add_reading(rfid, value):
    try:
        # Try to insert the reading into the database
        db = get_db()
        # Check if an employee is blocked
        cur = db.execute("SELECT BLOCKED FROM USERS WHERE RFID = ?", (rfid))
        blocked_status = cur.fetchone()
        if blocked_status[0] == 1:
            # User is blocked, return error message
            return jsonify({"message": "User is blocked"}), 403
        db.execute(
            "INSERT INTO readings (rfid, date_time, value) VALUES (?, ?, ?)",
            (rfid, datetime.now(), value),
        )
        db.commit()
        if check_for_block(rfid, block_time = 1) == 1:
            return jsonify({"message": "Reading added, User is blocked"}), 200
        return "Added", 200
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500
    
# Define checking if user should be blocked after adding reading
def check_for_block(rfid, timeframe_for_measurments = 3, drunk_threshold = 0.2, block_time = 10):
    try:
        # Get last 3 readings from
        db = get_db()
        cur = db.execute(f"SELECT strftime('%Y-%m-%d %H:%M:%S', DATE_TIME), VALUE FROM READINGS WHERE RFID = ? ORDER BY DATE_TIME DESC LIMIT 3", (rfid))
        readings = cur.fetchall()

        # Check if al of these reading were done in the last timeframe_for_measurments minutes
        timeframe_for_measurments = 3
        date_format = f"%Y-%m-%d %H:%M:%S"
        if len(readings) < 3:
            # There are not enough readings, return
            return
        for reading in readings:
            reading = list(reading)
            reading[0] = datetime.strptime(reading[0], date_format)
            if reading[0] < datetime.now() - timedelta(minutes=timeframe_for_measurments):
                # One of the readings was too old, return
                return
            if reading[1] < drunk_threshold:
                # One of the readings was below drunk_threshold, return
                return
            
        # If the loop ends, the employee is drunk, block him for block_time minutes
        db.execute("UPDATE USERS SET BLOCKED = 1 WHERE RFID = ?", (rfid,))
        db.execute("INSERT INTO BLOCKADES (RFID, START_DATE, END_DATE, BLOCKADE_TYPE, STATUS) VALUES (?, ?, ?, ?, ?)", (rfid, datetime.now(), datetime.now() + timedelta(minutes=block_time), "AUTOMATIC", "ONGOING"))
        db.commit()
        return 1
    except Exception as e:
        return jsonify({"message": str(e)}), 500