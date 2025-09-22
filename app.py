# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os, json, csv
from Conexion.conexion import get_connection  # tu conexión a MySQL

# ---------------------------
# Configuración de Flask
# ---------------------------
app = Flask(__name__)
app.secret_key = "clave_secreta"

# Carpeta de datos
RUTA_TXT = "datos/datos.txt"
RUTA_JSON = "datos/datos.json"
RUTA_CSV = "datos/datos.csv"

# ---------------------------
# Configuración SQLite
# ---------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'database', 'usuarios.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ---------------------------
# Modelo SQLite / Login
# ---------------------------
class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

with app.app_context():
    os.makedirs(os.path.join(BASE_DIR, 'database'), exist_ok=True)
    db.create_all()

# ---------------------------
# Configuración Flask-Login
# ---------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# ---------------------------
# Rutas principales
# ---------------------------
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template("dashboard.html", nombre=current_user.nombre)

# ---------------------------
# Registro y login
# ---------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        if Usuario.query.filter_by(email=email).first():
            flash("Email ya registrado")
            return redirect(url_for('register'))

        nuevo_usuario = Usuario(nombre=nombre, email=email, password=password)
        db.session.add(nuevo_usuario)
        db.session.commit()
        flash('Usuario registrado correctamente')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Usuario.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales incorrectas')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ---------------------------
# Persistencia con TXT
# ---------------------------
@app.route('/guardar_txt', methods=['POST'])
def guardar_txt():
    dato = request.form.get("dato")
    os.makedirs(os.path.dirname(RUTA_TXT), exist_ok=True)
    with open(RUTA_TXT, "a") as f:
        f.write(dato + "\n")
    return "Dato guardado en TXT"

@app.route('/leer_txt')
def leer_txt():
    if not os.path.exists(RUTA_TXT):
        return "No hay datos aún."
    with open(RUTA_TXT, "r") as f:
        contenido = f.readlines()
    return render_template("resultado.html", datos=contenido)

# ---------------------------
# Persistencia con JSON
# ---------------------------
@app.route('/guardar_json', methods=['POST'])
def guardar_json():
    dato = request.form.get("dato")
    datos = []

    if os.path.exists(RUTA_JSON):
        with open(RUTA_JSON, "r") as f:
            try:
                datos = json.load(f)
            except:
                datos = []

    datos.append(dato)
    os.makedirs(os.path.dirname(RUTA_JSON), exist_ok=True)
    with open(RUTA_JSON, "w") as f:
        json.dump(datos, f)

    return "Dato guardado en JSON"

@app.route('/leer_json')
def leer_json():
    if not os.path.exists(RUTA_JSON):
        return jsonify([])
    with open(RUTA_JSON, "r") as f:
        datos = json.load(f)
    return jsonify(datos)

# ---------------------------
# Persistencia con CSV
# ---------------------------
@app.route('/guardar_csv', methods=['POST'])
def guardar_csv():
    dato = request.form.get("dato")
    os.makedirs(os.path.dirname(RUTA_CSV), exist_ok=True)
    with open(RUTA_CSV, "a", newline="") as f:
        escritor = csv.writer(f)
        escritor.writerow([dato])
    return "Dato guardado en CSV"

@app.route('/leer_csv')
def leer_csv():
    if not os.path.exists(RUTA_CSV):
        return "No hay datos en CSV"
    with open(RUTA_CSV, "r") as f:
        lector = csv.reader(f)
        datos = [fila for fila in lector]
    return render_template("resultado.html", datos=datos)

# ---------------------------
# Persistencia con MySQL
# ---------------------------
@app.route('/guardar_mysql', methods=['POST'])
def guardar_mysql():
    nombre = request.form.get("dato")
    email = request.form.get("email", "")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (nombre, email) VALUES (%s, %s)", (nombre, email))
        conn.commit()
        cursor.close()
        conn.close()
        return "Usuario guardado en MySQL ✅"
    except Exception as e:
        return f"Error al guardar en MySQL: {e}"

@app.route('/leer_mysql')
def leer_mysql():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, email FROM usuarios")
        datos = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template("resultado.html", datos=[f"{n} ({m})" for n, m in datos])
    except Exception as e:
        return f"Error al leer de MySQL: {e}"

# ---------------------------
# Ejecutar la app
# ---------------------------
if __name__ == '__main__':
    app.run(debug=True)
from models import User  # tu modelo de usuario para MySQL