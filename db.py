import sqlite3
from flask import g

DATABASE = "database.db"

# Function to get a database connection
def get_db():
    db = getattr(g,"database.db", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

# Function to initialize the database with some initial data
def init_db(app):
    with app.app_context():
        db = get_db()
        with open("schema.sql", mode="r") as f:
            db.cursor().executescript(f.read())
        db.commit()
        print("Initialization complete.")