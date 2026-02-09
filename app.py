from flask import Flask, render_template #redirect, url_for, flash, session
#from werkzeug.security import generate_password_hash, check_password_hash
#from forms import RegistroForm, LoginForm
from extensions import db, migrate
from models.media_item import MediaItem

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clavesegura'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate.init_app(app, db)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/perfil')
def perfil():
    return render_template('perfil.html')

@app.route('/register', methods=['GET','POST'])
def register():
    form = RegistroForm()
    if form.validate_on_submit():
        nuevo = User(
            nombre=form.nombre.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.contraseña.data)
        )
        db.session.add(nuevo)
        db.session.commit()
        session['user_id'] = nuevo.id
        return redirect(url_for('perfil'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.contraseña.data):
            session['user_id'] = user.id
            return redirect(url_for('perfil'))
        flash('Alguno de tus datos fueron incorrectos', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))
