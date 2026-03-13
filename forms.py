from flask_wtf import FlaskForm
from wtforms import (
    StringField, 
    PasswordField, 
    SubmitField, 
    IntegerField, 
    BooleanField, 
    SelectField, 
    DateField, 
    TextAreaField, 
    DecimalField
    )
from wtforms.validators import (
    DataRequired,
    EqualTo,
    Email,
    Length,
    Optional,
    NumberRange,
    ValidationError)

# --------------------------------------- USUARIO ---------------------------------------
class RegistroForm(FlaskForm):
    nombre             = StringField('Nombre', validators=[DataRequired()])
    email              = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    contraseña         = PasswordField('Contraseña', validators=[
        DataRequired(), 
        Length(min=8, message='La contraseña debe tener al menos 8 caracteres')
        ]
    )
    repetir_contraseña = PasswordField('Repetir Contraseña',
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


# --------------------------------------- MEDIA ---------------------------------------

class MediaForm(FlaskForm):
    title = StringField("Títulillo", validators=[DataRequired(), Length(max=200)])

    media_type = SelectField(
        "Tipo",
        choices=[
            ("movie", "Película"),
            ("series", "Serie"),
            ("music", "Música"),
            ("book", "Libro"),
            ("game", "Juego"),
        ],
        validators=[DataRequired()],
    )

    tags = StringField("Tags (opcional)", validators=[Optional(), Length(max=40)])

    rating = DecimalField(
        "Calificación (0.0 a 10.0)",
        places=1,
        rounding=None,
        validators=[DataRequired(), NumberRange(min=0, max=10)],
    )

    notes = TextAreaField("Notas (opcional)", validators=[Optional(), Length(max=2000)])

    status = SelectField(
        "Estado",
        choices=[
            ("planned", "Planeado"),
            ("in_progress", "En proceso"),
            ("done", "Terminado"),
            ("dropped", "Abandonado"),
        ],
        validators=[DataRequired()],
    )

    start_date = DateField("Fecha de inicio (opcional)", validators=[Optional()])
    end_date = DateField("Fecha fin (opcional)", validators=[Optional()])
    
    def validate_end_date(self, field):
        if self.start_date.data and field.data and field.data < self.start_date.data:
            raise ValidationError("La fecha fin no puede ser anterior a la fecha de inicio.")


    submit = SubmitField("Guardar")

# --------------------------------------- HABITOS ---------------------------------------
class HabitForm(FlaskForm):
    name                = StringField('Nombre', validators=[DataRequired(), Length(max=120)])
    target_minutes      = IntegerField(
        'Meta de minutos',
        validators=[Optional(), NumberRange(min=1, message="Debe ser mayor a 0")]
    )
    is_active = BooleanField('Activo (Todavía tienes este hábito)', default=True)
    
    submit = SubmitField('Guardar')

# --------------------------------------- FINANZAS ---------------------------------------

class TransactionForm(FlaskForm):
    type = SelectField('Tipo', 
    choices=[("expense", "Gasto"),("income","Ingreso")], 
    validators=[DataRequired()]
    )
    amount = StringField('Monto (COP)', validators=[Optional(),])
    date = DateField("Fecha", validators=[DataRequired()])
    category_id = SelectField('Categoría', coerce=int, validators=[DataRequired()])
    notes = TextAreaField("Notas")

    submit = SubmitField('Guardar')

class CategoryForm(FlaskForm):
    name = StringField("Nombre", validators=[DataRequired(), Length(max=120)])
    # Modificar
    kind = SelectField("Tipo", choices=[("", ""), ("", ""), ("","")], validators=[DataRequired()])

    submit = SubmitField("Guardar")