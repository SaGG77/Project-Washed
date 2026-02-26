# LIBRERIAS
from flask import Flask, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
from dotenv import load_dotenv
# FORMS
from forms import RegistroForm, LoginForm
# BASES DE DATOS
from extensions import db, migrate
from models.user import User
from models.media_item import MediaItem
from models.habit import Habit
from models.habit_log import HabitLog
# BLUEPRINTS
from routes.auth_routes import auth_bp
from routes.media_routes import media_bp
from routes.habit_routes import habit_bp

load_dotenv()
app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev_key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate.init_app(app, db)

app.register_blueprint(auth_bp)
app.register_blueprint(media_bp)
app.register_blueprint(habit_bp)

@app.route("/")
def home():
    return render_template("home.html")
