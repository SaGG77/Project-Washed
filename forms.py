from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Email, Length

class RegistroForm(FlaskForm):
    nombre             = StringField('Nombre', validators=[DataRequired()])
    email              = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    contraseña         = PasswordField('Contraseña', validators=[
        DataRequired(), 
        Length(min=8, message='La contraseña debe tener al menos 8 caracteres')
        ]
    )
    repetir_contraseña = PasswordField(
        'Repetir Contraseña',
        validators=[
            DataRequired(),
            EqualTo('contraseña', message='Las contraseñas deben coincidir'),
            Length(min=8)
        ]
    )
    submit             = SubmitField('Registrarse')

class LoginForm(FlaskForm):
    email             = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    contraseña        = PasswordField('Contraseña', validators=[DataRequired()])
    submit            = SubmitField('Ingresar')