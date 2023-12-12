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
from db import get_db, init_db
from api import api
from views import views



# Define the path to the SQLite database file
DATABASE = "database.db"

# Create a Flask application instance
app = Flask(__name__)
app.secret_key = b"123456789"


login_manager = LoginManager(app)

app.register_blueprint(views)
app.register_blueprint(api, url_prefix="/api")

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    cur = db.execute("SELECT USERNAME FROM BOSSES WHERE ID = ?", (user_id,))
    boss_data = cur.fetchone()
    if boss_data:
        return Boss(id=user_id, name=boss_data[0])
    return None

# Function to close the database connection when the app context is torn down
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()



# Run the Flask app if the script is executed directly
if __name__ == "__main__":
    with app.app_context():
        init_db(app)
    app.run(debug=True)

