from flask import jsonify
import sqlite3
import sys
import traceback
from db import get_db
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

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
    
# Prepare data for a histogram showing percentage of readings below drunk threshold for each employee
def get_sober_readings_data(drunk_threshold):
    try:
        db = get_db()
        cur = db.execute("SELECT R.RFID, U.NAME, U.SURNAME, COUNT(*), (SELECT COUNT(*) FROM READINGS WHERE RFID = R.RFID) FROM READINGS R LEFT JOIN USERS U ON R.RFID = U.RFID WHERE VALUE < ? GROUP BY R.RFID", (drunk_threshold,))
        histogram_data = cur.fetchall()

        if not histogram_data:
            return "No records found.", datetime.now()

        # Turn data into dict
        histogram_data = [{"id": row[0], "name": row[1], "surname": row[2], "sober_readings": row[3], "total_readings": row[4]} for row in histogram_data]

        # Add timestamp of when the data was fetched
        return histogram_data, datetime.now()
    except Exception as e:
        return str(e), datetime.now()

# Prepare a matplotlib histogram showing percentage of readings below drunk threshold for each employee
def get_sober_readings_histogram(histogram_data, timestamp, drunk_threshold = 0.2):
    try:
        # Get data from the histogram_data dict
        ids = [histogram_data[i]["id"] for i in range(len(histogram_data))]
        names = [histogram_data[i]["name"] for i in range(len(histogram_data))]
        surnames = [histogram_data[i]["surname"] for i in range(len(histogram_data))]
        sober_readings = [histogram_data[i]["sober_readings"] for i in range(len(histogram_data))]
        total_readings = [histogram_data[i]["total_readings"] for i in range(len(histogram_data))]
        sober_percentages = [sober_readings[i] / total_readings[i] * 100 for i in range(len(histogram_data))]
        # Create a matplotlib histogram
        plt.bar(ids, sober_percentages)
        plt.xticks(ids, [f"{name} {surname}" for name, surname in zip(names, surnames)])
        plt.xlabel("Employee")
        plt.ylabel("Percentage of sober readings")
        plt.title(f"Percentage of sober readings for each employee on {timestamp.strftime('%d.%m.%Y at %H:%M')}\nFor drunk threshold of {drunk_threshold}")
        plt.savefig("static/sober_readings_histogram.png")
        plt.close()
    except Exception as e:
        return str(e)

# Prepare data for a histogram showing how many time each employee was blocked
def get_blocks_number_data():
    try:
        db = get_db()
        cur = db.execute("SELECT B.RFID, U.NAME, U.SURNAME, COUNT(*) FROM BLOCKADES B LEFT JOIN USERS U ON B.RFID = U.RFID GROUP BY B.RFID")
        histogram_data = cur.fetchall()

        if not histogram_data:
            return "No records found."

        # Turn data into dict
        histogram_data = [{"id": row[0], "name": row[1], "surname": row[2], "blocks_number": row[3]} for row in histogram_data]

        return histogram_data
    except Exception as e:
        return str(e)

# Prepare a matplotlib histogram showing how many time each employee was blocked
def get_blocks_number_histogram(histogram_data):
    try:
        # Get data from the histogram_data dict
        ids = [row["id"] for row in histogram_data]
        names = [row["name"] for row in histogram_data]
        surnames = [row["surname"] for row in histogram_data]
        blocks_number = [row["blocks_number"] for row in histogram_data]

        # Create a matplotlib histogram
        plt.bar(ids, blocks_number)
        plt.xticks(ids, [f"{name} {surname}" for name, surname in zip(names, surnames)])
        plt.xlabel("Employee")
        plt.ylabel("Number of blocks")
        plt.title(f"Number of blocks for each employee")
        plt.savefig("static/blocks_number_histogram.png")
        plt.close()
    except Exception as e:
        return str(e)
