# con estas librerías podemos crear la app, manejar sesiones, formularios y CSRF    
from flask import Flask, render_template, flash, redirect, url_for, session, request
# con dotenv cargamos las variables de entorno desde el archivo .env
from dotenv import load_dotenv
# para proteger formularios contra CSRF
from flask_wtf import CSRFProtect
# para manejar variables de entorno y funciones decoradoras
import os
import random
import time
from functools import wraps # para crear funciones decoradoras. wrasps mantiene el nombre y docstring de la función original
# importamos el formulario seguro desde forms.py
# nuestro formulario seguro con reCAPTCHA
from forms import SecureForm

load_dotenv() # cargamos las variables de entorno desde el archivo .env

app = Flask(__name__) # creamos la app Flask
# configuramos la app con las variables de entorno o valores por defecto para desarrollo
app.config.update(
    SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "dev_secret_change_me"),
    WTF_CSRF_SECRET_KEY=os.getenv("WTF_CSRF_SECRET_KEY", "dev_csrf_change_me"),
    RECAPTCHA_PUBLIC_KEY=os.getenv("RECAPTCHA_SITE_KEY"),
    RECAPTCHA_PRIVATE_KEY=os.getenv("RECAPTCHA_SECRET_KEY"),
    RECAPTCHA_PARAMETERS={"hl": "es"},
)

csrf = CSRFProtect(app) # inicializamos CSRFProtect para proteger formularios contra CSRF

# Diccionario para almacenar CAPTCHAs activos
active_captchas = {}

def generate_math_captcha():
    """Genera un CAPTCHA matemático simple"""
    num1 = random.randint(1, 20)
    num2 = random.randint(1, 20)
    operator = random.choice(['+', '-', '*'])
    
    if operator == '+':
        answer = num1 + num2
        question = f"{num1} + {num2} = ?"
    elif operator == '-':
        # Asegurar que el resultado no sea negativo
        num1, num2 = max(num1, num2), min(num1, num2)
        answer = num1 - num2
        question = f"{num1} - {num2} = ?"
    else:  # *
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 5)
        answer = num1 * num2
        question = f"{num1} × {num2} = ?"
    
    captcha_id = f"math_{int(time.time())}"
    return captcha_id, question, str(answer)

def generate_sequence_captcha():
    """Genera un CAPTCHA de secuencia lógica"""
    sequences = [
        {
            'question': "2, 4, 6, 8, ?",
            'options': ["10", "9", "12", "7"],
            'answer': "10"
        },
        {
            'question': "A, C, E, G, ?",
            'options': ["H", "I", "J", "K"],
            'answer': "I"
        },
        {
            'question': "5, 10, 15, 20, ?",
            'options': ["25", "30", "35", "40"],
            'answer': "25"
        },
        {
            'question': "Z, Y, X, W, ?",
            'options': ["V", "U", "T", "S"],
            'answer': "V"
        },
        {
            'question': "1, 4, 9, 16, ?",
            'options': ["25", "20", "36", "24"],
            'answer': "25"
        }
    ]
    
    seq = random.choice(sequences)
    captcha_id = f"seq_{int(time.time())}"
    return captcha_id, seq['question'], seq['options'], seq['answer']

def generate_security_captcha():
    """Genera un CAPTCHA de pregunta de seguridad"""
    questions = [
        {
            'question': "¿Cuántos lados tiene un triángulo?",
            'answer': "3",
            'hint': "Escribe el número en texto"
        },
        {
            'question': "¿Qué animal se conoce como el mejor amigo del hombre?",
            'answer': "perro",
            'hint': "Escríbelo en minúsculas"
        },
        {
            'question': "¿En qué continente se encuentra España?",
            'answer': "europa",
            'hint': "Escríbelo en minúsculas"
        },
        {
            'question': "¿Cuántos días tiene una semana?",
            'answer': "7",
            'hint': "Escribe el número en texto"
        },
        {
            'question': "¿Qué color se forma mezclando azul y amarillo?",
            'answer': "verde",
            'hint': "Escríbelo en minúsculas"
        }
    ]
    
    q = random.choice(questions)
    captcha_id = f"sec_{int(time.time())}"
    return captcha_id, q['question'], q['answer'], q.get('hint', '')

def cleanup_old_captchas():
    """Limpia CAPTCHAs más antiguos de 10 minutos"""
    current_time = time.time()
    expired = []
    for captcha_id in active_captchas.keys():
        try:
            captcha_time = int(captcha_id.split('_')[1])
            if current_time - captcha_time > 600:  # 10 minutos
                expired.append(captcha_id)
        except (IndexError, ValueError):
            expired.append(captcha_id)
    
    for captcha_id in expired:
        active_captchas.pop(captcha_id, None)

# -------- Protección de páginas verificadas ----------
def verified_required(view_func): # función decoradora para proteger rutas que requieren verificación
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("verified"):
            flash("Debes completar la verificación primero.", "warning")
            # si venimos de una URL protegida, la guardamos para volver luego
            session["next"] = request.path # con session["next"] guardamos la URL a la que se quería acceder
            return redirect(url_for("index"))
        return view_func(*args, **kwargs)
    return wrapped
# -----------------------------------------------------

@app.route("/", methods=["GET", "POST"]) # ruta principal con métodos GET y POST para el formulario 
def index():
    # Si ya hay sesión verificada y es un GET, no mostramos el form
    if request.method == "GET" and session.get("verified"):
        # elige a dónde enviarlo: "exito" o "dashboard"
        return redirect(url_for("exito"))   # o url_for("dashboard")

    form = SecureForm() # instanciamos el formulario seguro
    if form.validate_on_submit():
        session["payload"] = {
            "nombre": form.nombre.data.strip(),
            "correo": (form.correo.data or "").strip()
        }
        session["verified"] = True # marcamos la sesión como verificada
        flash("¡Verificación exitosa!", "success")
        next_url = session.pop("next", None)
        return redirect(next_url or url_for("exito")) # redirigimos a la URL guardada o a "exito" cuando es exitoso el form

    elif form.is_submitted():   # si el formulario fue enviado pero no validado
        for field, errors in form.errors.items():
            label = getattr(getattr(form, field), "label", field).text if hasattr(getattr(form, field), "label") else field
            for err in errors:
                flash(f"{label}: {err}", "danger")  # mostramos errores con flash
        flash("Revisa el formulario.", "warning")   # aviso general para revisar el formulario
        return redirect(url_for("index", _anchor="form"))

    return render_template("index.html", form=form) # renderizamos el template con el formulario cuando es GET o no validó

@app.route("/exito") # ruta de éxito tras verificación para mostrar datos en sesión
def exito():
    data = session.get("payload")  # payload es la info del usuario, que contiene nombre y correo, no lo hacemos pop para que se vea en el menú también, pop es para eliminarlo de la sesión
     # si no hay datos en sesión o no está verificada, redirigimos a index
    if not session.get("verified"):
        flash("No hay datos para mostrar. Completa el formulario primero.", "info")
        return redirect(url_for("index")) # redirigimos a index si no está verificada
     # si hay datos, renderizamos el template de éxito con los datos
    return render_template("exito.html", data=data)

# Rutas para los CAPTCHAs
@app.route("/verify_captcha1", methods=["GET", "POST"])
@verified_required
def verify_captcha1():
    if request.method == "POST":
        captcha_id = request.form.get('captcha_id')
        user_answer = request.form.get('answer', '').strip()
        
        if captcha_id in active_captchas:
            correct_answer = active_captchas[captcha_id]
            # Limpiar CAPTCHAs antiguos
            cleanup_old_captchas()
            
            if user_answer == correct_answer:
                session['captcha1_passed'] = True
                flash("¡CAPTCHA verificado correctamente!", "success")
                return redirect(url_for('perfil'))
            else:
                flash("Respuesta incorrecta. Intenta nuevamente.", "danger")
        
        return redirect(url_for('verify_captcha1'))
    
    # GET request - generar nuevo CAPTCHA
    captcha_id, question, answer = generate_math_captcha()
    active_captchas[captcha_id] = answer
    return render_template('captcha1.html', 
                         captcha_question=question, 
                         captcha_id=captcha_id)

@app.route("/verify_captcha2", methods=["GET", "POST"])
@verified_required
def verify_captcha2():
    if request.method == "POST":
        captcha_id = request.form.get('captcha_id')
        user_answer = request.form.get('answer', '').strip()
        
        if captcha_id in active_captchas:
            correct_answer = active_captchas[captcha_id]
            cleanup_old_captchas()
            
            if user_answer == correct_answer:
                session['captcha2_passed'] = True
                flash("¡CAPTCHA verificado correctamente!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Respuesta incorrecta. Intenta nuevamente.", "danger")
        
        return redirect(url_for('verify_captcha2'))
    
    captcha_id, question, options, answer = generate_sequence_captcha()
    active_captchas[captcha_id] = answer
    return render_template('captcha2.html', 
                         captcha_question=question, 
                         options=options,
                         captcha_id=captcha_id)

@app.route("/verify_captcha3", methods=["GET", "POST"])
@verified_required
def verify_captcha3():
    if request.method == "POST":
        captcha_id = request.form.get('captcha_id')
        user_answer = request.form.get('answer', '').strip().lower()
        
        if captcha_id in active_captchas:
            correct_answer = active_captchas[captcha_id]
            cleanup_old_captchas()
            
            if user_answer == correct_answer.lower():
                session['captcha3_passed'] = True
                flash("¡CAPTCHA verificado correctamente!", "success")
                return redirect(url_for('reportes'))
            else:
                flash("Respuesta incorrecta. Intenta nuevamente.", "danger")
        
        return redirect(url_for('verify_captcha3'))
    
    captcha_id, question, answer, hint = generate_security_captcha()
    active_captchas[captcha_id] = answer
    return render_template('captcha3.html', 
                         captcha_question=question, 
                         hint=hint,
                         captcha_id=captcha_id)

# ----------------- Rutas protegidas con CAPTCHAs -----------------
@app.route("/dashboard") # ruta protegida para el dashboard
@verified_required
def dashboard():
    if not session.get('captcha2_passed'):
        return redirect(url_for('verify_captcha2'))
    return render_template("dashboard.html", data=session.get("payload"))

@app.route("/perfil") # ruta protegida para el perfil
@verified_required
def perfil():
    if not session.get('captcha1_passed'):
        return redirect(url_for('verify_captcha1'))
    return render_template("perfil.html", data=session.get("payload"))

@app.route("/reportes") # ruta protegida para reportes
@verified_required
def reportes():
    if not session.get('captcha3_passed'):
        return redirect(url_for('verify_captcha3'))
    return render_template("reportes.html", data=session.get("payload"))
# recordemos que payload es la info del usuario, que contiene nombre y correo
# ----------------------------------------------------

@app.route("/salir", methods=["POST"]) # ruta para cerrar sesión, solo POST para mayor seguridad
def salir():
    session.clear()                   # limpiamos toda la sesión al cerrar sesión
    active_captchas.clear()           # limpiamos todos los CAPTCHAs activos
    flash("Sesión cerrada. Verifícate de nuevo para acceder.", "info")
    return redirect(url_for("index")) # redirigimos a index tras cerrar sesión

# Ruta para limpiar CAPTCHAs expirados (opcional, puede llamarse periódicamente)
@app.route("/cleanup_captchas")
def cleanup_captchas_route():
    cleanup_old_captchas()
    return "CAPTCHAs expirados limpiados"

if __name__ == "__main__": 
    app.run(debug=True, host="0.0.0.0", port=8095)