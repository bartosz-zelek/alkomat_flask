from flask import Flask, g, jsonify
from flask_login import LoginManager
from boss import Boss
from db import get_db, init_db
from api import api
from views import views
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta


# Define the path to the SQLite database file
DATABASE = "database.db"

# Create a Flask application instance
def create_app():
    app = Flask(__name__)
    app.secret_key = b"123456789"

    app.register_blueprint(views)
    app.register_blueprint(api, url_prefix="/api")

    def check_blockades():
        try:
            with app.app_context():
                db = get_db()
                # Get all blockades that are automatic and have ended yet and that started after last usage of this function (set in a parameter)
                cur = db.execute(F"SELECT RFID, strftime('%Y-%m-%d %H:%M:%S', END_DATE) FROM BLOCKADES WHERE BLOCKADE_TYPE = ? AND END_DATE < ? AND STATUS = 'ONGOING'", ("AUTOMATIC", datetime.now()))
                blockades = cur.fetchall()

                for blockade in blockades:
                    blockade = list(blockade)
                    # Check if blockade has ended
                    if datetime.strptime(blockade[1], f"%Y-%m-%d %H:%M:%S") < datetime.now():
                        # Blockade has ended, update the BLOCKED status of the user to 0
                        db.execute("UPDATE USERS SET BLOCKED = 0 WHERE RFID = ?", (blockade[0],))
                        db.commit()

                return jsonify({"message": "Blockades checked"}), 200

        except Exception as e:
            return jsonify({"message": str(e)}), 500
        
    check_blockades()

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_blockades, trigger="interval", seconds=60)
    scheduler.start()

    return app


app = create_app()
login_manager = LoginManager(app)

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

