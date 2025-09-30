# con estas librerías podemos crear la app, manejar sesiones, formularios y CSRF    
from flask import Flask, render_template, flash, redirect, url_for, session, request
# con dotenv cargamos las variables de entorno desde el archivo .env
from dotenv import load_dotenv
# para proteger formularios contra CSRF
from flask_wtf import CSRFProtect
# para manejar variables de entorno y funciones decoradoras
import os
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

# ----------------- Rutas protegidas -----------------
@app.route("/dashboard") # ruta protegida para el dashboard
@verified_required
def dashboard():
    return render_template("dashboard.html", data=session.get("payload")) # pasamos los datos de sesión al template con data=session.get("payload")

@app.route("/perfil") # ruta protegida para el perfil
@verified_required
def perfil():
    return render_template("perfil.html", data=session.get("payload")) # pasamos los datos de sesión al template con data=session.get("payload")

@app.route("/reportes") # ruta protegida para reportes
@verified_required
def reportes():
    return render_template("reportes.html", data=session.get("payload")) # pasamos los datos de sesión al template con data=session.get("payload")
# recordemos que payload es la info del usuario, que contiene nombre y correo
# ----------------------------------------------------

@app.route("/salir", methods=["POST"]) # ruta para cerrar sesión, solo POST para mayor seguridad
def salir():
    session.clear()                   # limpiamos toda la sesión al cerrar sesión
    flash("Sesión cerrada. Verifícate de nuevo para acceder.", "info")
    return redirect(url_for("index")) # redirigimos a index tras cerrar sesión


if __name__ == "__main__": 
    app.run(debug=True, host="0.0.0.0", port=8095)
