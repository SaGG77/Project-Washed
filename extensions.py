from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Cada que haga una base de datos con SQLAlchemy tengo primero que hacer esto y luego, en el archivo
# poner un "from extensions import db"
db = SQLAlchemy()
migrate = Migrate()
