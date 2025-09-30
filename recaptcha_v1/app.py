from flask import Flask, render_template, request, flash
import requests, os

app = Flask(__name__)

# Buenas prácticas: claves desde variables de entorno
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "se sugiere cambiar_esta_clave_en_produccion")
RECAPTCHA_SECRET_KEY = os.environ.get(
    "RECAPTCHA_SECRET_KEY",
    "6Lc2ktQrAAAAAKAtXejIV4Jm-S4SJABhEdAsK8Jk"  
)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        recaptcha_response = request.form.get('g-recaptcha-response', '')
        payload = {
            'secret': RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload, timeout=10)
        result = r.json()

        if result.get('success'):
            flash('¡Verificación reCAPTCHA exitosa!', 'success')
        else:
            flash('reCAPTCHA falló. Inténtalo de nuevo.', 'danger')

    return render_template('index.html', page_title='Formulario con reCAPTCHA')

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8094)
