from flask import Flask, g
from flask_login import LoginManager
from boss import Boss
from db import get_db, init_db
from api import api
from views import views
from apscheduler.schedulers.background import BackgroundScheduler
from helpers import check_blockades


# Define the path to the SQLite database file
DATABASE = "database.db"

# Create a Flask application instance
def create_app():
    app = Flask(__name__)
    app.secret_key = b"123456789"

    app.register_blueprint(views)
    app.register_blueprint(api, url_prefix="/api")

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_blockades, trigger="interval", seconds=60, args=[app])
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

