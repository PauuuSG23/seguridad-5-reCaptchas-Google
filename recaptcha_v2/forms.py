from flask_wtf import FlaskForm, RecaptchaField # acá importamos RecaptchaField para el campo reCAPTCHA
from wtforms import StringField, EmailField, SubmitField # si usamos EmailField, instalamos previamente email-validator
from wtforms.validators import DataRequired, Length, Email # si usamos EmailField, importamos Email

class SecureForm(FlaskForm): # nuestro formulario seguro con reCAPTCHA para verificar humanos
    nombre = StringField(    # StringField para texto corto
        "Usuario",
        validators=[DataRequired("El usuario es obligatorio."), Length(min=3, max=50)],
        render_kw={"placeholder": "Tu usuario"}
    )

    correo = EmailField(    # EmailField para correos electrónicos
        "Correo",
        validators=[
            DataRequired("El correo es obligatorio."),
            Email("Correo inválido.")
        ],
        render_kw={"placeholder": "tucorreo@usta.com"}  
    )

    recaptcha = RecaptchaField()   # campo reCAPTCHA
    submit = SubmitField("Enviar") # botón de envío
