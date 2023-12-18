from flask import jsonify
import sqlite3
import sys
import traceback
from db import get_db
from datetime import datetime, timedelta

def get_readings_internal(count, offset, id = None):
    db = get_db()
    if id:
        cur = db.execute(
            "SELECT date_time, name, surname, value FROM users INNER JOIN readings ON users.rfid = readings.rfid WHERE users.rfid = ? ORDER BY readings.date_time DESC LIMIT ? OFFSET ?", (id, count, offset)
        )
    else:
        cur = db.execute(
            "SELECT date_time, name, surname, value FROM users INNER JOIN readings ON users.rfid = readings.rfid ORDER BY readings.date_time DESC LIMIT ? OFFSET ?", (count, offset)
        )
    list_of_readings = cur.fetchall()
    return list_of_readings


def add_employee_to_database(rfid, name, surname):
    try:
        # Try to insert the employee into the database
        db = get_db()
        db.execute(
            "INSERT INTO users (rfid, name, surname) VALUES (?, ?, ?)",
            (rfid, name, surname),
        )
        db.commit()
        #Return dict with employee data
        res = {"id": rfid, "name": name, "surname": surname, "blocked": 0}
        return res
    except sqlite3.Error as er:
        # If an SQLite error occurs, return the error information as a response
        exc_type, exc_value, exc_tb = sys.exc_info()
        return traceback.format_exception(exc_type, exc_value, exc_tb)[-1], 500
    
# Define checking if user should be blocked after adding reading
def check_for_block(rfid, timeframe_for_measurments = 3, drunk_threshold = 0.2, block_time = 10):
    try:
        # Get last 3 readings from
        db = get_db()
        cur = db.execute("SELECT strftime('%Y-%m-%d %H:%M:%S', DATE_TIME), VALUE FROM READINGS WHERE RFID = ? ORDER BY DATE_TIME DESC LIMIT 3", (rfid,))
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
        return e