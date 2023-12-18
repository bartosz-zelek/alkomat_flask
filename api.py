from flask import Blueprint, jsonify, request, abort, current_app, flash
from db import get_db
from flask_login import login_required
import sqlite3
import sys
import traceback
from datetime import datetime, timedelta
from helpers import get_readings_internal, add_employee_to_database, check_for_block, get_sober_readings_data, get_sober_readings_histogram, get_blocks_number_data, get_blocks_number_histogram

api = Blueprint('api', __name__)


# Define a route to get readings from the database
@api.route("/get_readings", defaults={"id": None})
@api.route("/get_readings/<id>")
#@login_required  # Add this decorator to protect the route
def get_readings(id):
    try:
        count = request.args.get("count", default=50, type=int)
        offset = request.args.get("offset", default=0, type=int)
        # Try to get readings from the database
        list_of_readings = get_readings_internal(count, offset, id)
        return jsonify(list_of_readings), 200
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500
    

@api.route("/check_rfid/<rfid>")
def check_rfid(rfid):
    try:
        db = get_db()
        cur = db.execute("SELECT * FROM users WHERE rfid = ?", (rfid,))
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
        # Check if an employee with the given RFID exists
        cur = db.execute("SELECT * FROM USERS WHERE RFID = ?", (rfid,))
        user = cur.fetchone()
        if not user:
            # User does not exist, return error message
            return jsonify({"message": "User does not exist"}), 404
        # Check if an employee is blocked
        cur = db.execute("SELECT BLOCKED FROM USERS WHERE RFID = ?", (rfid,))
        blocked_status = cur.fetchone()
        print(f"Bloked status: {blocked_status[0]}")
        if blocked_status[0] == 1:
            # User is blocked, return error message
            return jsonify({"message": "User is blocked"}), 403
        db.execute(
            "INSERT INTO readings (rfid, date_time, value) VALUES (?, ?, ?)",
            (rfid, datetime.now(), value),
        )
        db.commit()
        try:
            # Check if user should be blocked
            if check_for_block(rfid, block_time=1) == 1:
                return jsonify({"message": "Reading added. User blocked."}), 200
        except Exception as e:
            return jsonify({"message": str(e)}), 500
        return "Added", 200
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500
    

# Define route to get plots from helpers.py
@api.route("/get_plots")
def get_plots():
    try:
        # Try to get plots from the database
        drunk_threshold = 0.2
        sober_readings_data, timestamp = get_sober_readings_data(drunk_threshold)
        sober_readings_histogram = get_sober_readings_histogram(drunk_threshold=drunk_threshold, histogram_data=sober_readings_data, timestamp=timestamp)
        blocks_number_data = get_blocks_number_data()
        blocks_number_histogram = get_blocks_number_histogram(blocks_number_data)
        return jsonify({"sober_readings_data": sober_readings_data, "sober_readings_histogram": sober_readings_histogram, "blocks_number_data": blocks_number_data, "blocks_number_histogram": blocks_number_histogram}), 200
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500