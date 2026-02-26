# Librerias
from flask import Flask, render_template
import os
from dotenv import load_dotenv
# Bases de datos y csrf
from extensions import db, migrate
from extensions import csrf
# Rutas
from routes.auth_routes import auth_bp
from routes.media_routes import media_bp
from routes.habit_routes import habit_bp

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev_key")

SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate.init_app(app, db)
csrf.init_app(app)

app.register_blueprint(auth_bp)
app.register_blueprint(media_bp)
app.register_blueprint(habit_bp)

@app.route("/")
def home():
    return render_template("home.html")
