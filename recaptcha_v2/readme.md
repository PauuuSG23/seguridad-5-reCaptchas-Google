# Estructura del proytecto

recaptcha_v2/
├─ app.py
├─ forms.py                  # manejo del formulario de entrada con CSRF
├─ requirements.txt          # instalaciones
├─ .env                      # claves reCAPTCHA (pública/privada)
├─ templates/
│  ├─ base.html
│  └─ index.html             # usa form.csrf_token y form.recaptcha
└─ static/
   └─ css/custom.css




# Pasos para correr el proyecto

- 1. Crear y activar entorno virtual:
python -m venv .venv
.\.venv\Scripts\Activate.ps1

- 2. Instalar dependencias:
pip install -r requirements.txt

-------------------------


