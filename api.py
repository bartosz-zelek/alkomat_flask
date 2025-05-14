import sqlite3
import sys
import traceback
from datetime import datetime

from db import get_db
from flask import Blueprint, abort, jsonify, request
from helpers import (
    check_for_block,
    get_blocks_number_data,
    get_blocks_number_histogram,
    get_readings_internal,
    get_sober_readings_data,
    get_sober_readings_histogram,
)

api = Blueprint("api", __name__)


# Define a route to get readings from the database
@api.route("/get_readings", defaults={"id": None})
@api.route("/get_readings/<id>")
# @login_required  # Add this decorator to protect the route
def get_readings(id):
    try:
        # Get count and offset parameters from the request or use default values
        count = request.args.get("count", default=50, type=int)
        offset = request.args.get("offset", default=0, type=int)

        # Try to get readings from the database
        list_of_readings = get_readings_internal(count, offset, id)
        return jsonify(list_of_readings), 200
    except sqlite3.Error:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500


@api.route("/uuid/<uuid>")
def get_uuid(uuid):
    try:
        # Try to get readings from the database
        db = get_db()
        cur = db.execute("SELECT * FROM uuids WHERE uuid = ?", (uuid,))
        uuid_info = cur.fetchone()
        if uuid_info:
            return (
                jsonify(
                    {
                        "id": uuid_info[0],
                        "user_id": uuid_info[1],
                        "uuid": uuid_info[2],
                        "photo": uuid_info[3],
                    }
                ),
                200,
            )
        else:
            # If the UUID is not found, insert new UUID into the database
            db.execute(
                "INSERT INTO uuids (uuid) VALUES (?)",
                (uuid,),
            )
            db.commit()
            return (
                jsonify(
                    {
                        "id": None,
                        "user_id": None,
                        "uuid": uuid,
                        "photo": None,
                    }
                ),
                200,
            )
    except sqlite3.Error:
        abort(404)


@api.route("/check_user_id/<user_id>")
def check_user_id(user_id):
    try:
        db = get_db()
        cur = db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cur.fetchone()
        if user:
            return (
                jsonify(
                    {
                        "id": user[0],
                        "name": user[1],
                        "surname": user[2],
                        "blocked": user[3],
                    }
                ),
                200,
            )
        else:
            abort(404)
    except sqlite3.Error:
        abort(404)


# Define a route to add a reading to the database
@api.route("/add_reading/<user_id>/<int:value>", methods=["GET"])
def add_reading(user_id, value):
    try:
        # Try to insert the reading into the database
        db = get_db()

        # Check if an employee with the given user_id exists
        cur = db.execute("SELECT * FROM USERS WHERE user_id = ?", (user_id,))
        user = cur.fetchone()
        if not user:
            # User does not exist, return error message
            return jsonify({"message": "USER DOESN'T EXIST"}), 404

        # Check if an employee is blocked
        cur = db.execute("SELECT BLOCKED FROM USERS WHERE user_id = ?", (user_id,))
        blocked_status = cur.fetchone()
        print(f"Bloked status: {blocked_status[0]}")
        if blocked_status[0] == 1:
            # User is blocked, return error message
            return jsonify({"message": "USER BLOCKED"}), 403

        # Insert the reading into the database
        insert_value = max(0, 0.00417 * value - 3.000)
        print(f"Insert value: {insert_value}")
        db.execute(
            "INSERT INTO readings (user_id, date_time, value) VALUES (?, ?, ?)",
            (user_id, datetime.now(), round(insert_value, 2)),
        )
        db.commit()

        # Check if user should be blocked
        try:
            is_drunk = insert_value > 0.2
            if is_drunk:
                check_for_block(user_id)
                return jsonify({"message": "ENTRY BLOCKED"}), 200
        except Exception as e:
            return jsonify({"message": str(e)}), 500

        print(f"Accepted reading for user {user_id}: {value}")

        return jsonify({"message": "ACCEPTED"}), 200
    except sqlite3.Error:
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
        if sober_readings_data == "No records found":
            return jsonify({"message": "No records found"}), 404
        sober_readings_histogram = get_sober_readings_histogram(
            drunk_threshold=drunk_threshold,
            histogram_data=sober_readings_data,
            timestamp=timestamp,
        )
        blocks_number_data = get_blocks_number_data()
        if blocks_number_data == "No records found":
            return jsonify({"message": "No records found"}), 404
        blocks_number_histogram = get_blocks_number_histogram(blocks_number_data)
        return (
            jsonify(
                {
                    "sober_readings_data": sober_readings_data,
                    "sober_readings_histogram": sober_readings_histogram,
                    "blocks_number_data": blocks_number_data,
                    "blocks_number_histogram": blocks_number_histogram,
                }
            ),
            200,
        )
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500
