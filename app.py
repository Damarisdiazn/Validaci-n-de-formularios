from flask import Flask, render_template, request, jsonify
import os, json, csv
from flask_sqlalchemy import SQLAlchemy
from Conexion.conexion import get_connection  # Conexión a MySQL

app = Flask(__name__)

# --- Rutas de archivos ---
RUTA_TXT = "datos/datos.txt"
RUTA_JSON = "datos/datos.json"
RUTA_CSV = "datos/datos.csv"

# -----------------------
# Configuración SQLite
# -----------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'database', 'usuarios.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# -----------------------
# Modelo SQLite
# -----------------------
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()

# -----------------------
# Rutas principales
# -----------------------
@app.route('/')
def index():
    return render_template("index.html")

# -----------------------
# Persistencia con TXT
# -----------------------
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

# -----------------------
# Persistencia con JSON
# -----------------------
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

# -----------------------
# Persistencia con CSV
# -----------------------
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

# -----------------------
# Persistencia con SQLite
# -----------------------
@app.route('/guardar_sqlite', methods=['POST'])
def guardar_sqlite():
    nombre = request.form.get("dato")
    nuevo_usuario = Usuario(nombre=nombre)
    db.session.add(nuevo_usuario)
    db.session.commit()
    return "Usuario guardado en SQLite"

@app.route('/leer_sqlite')
def leer_sqlite():
    usuarios = Usuario.query.all()
    return render_template("resultado.html", datos=[u.nombre for u in usuarios])

# -----------------------
# Persistencia con MySQL
# -----------------------
@app.route('/guardar_mysql', methods=['POST'])
def guardar_mysql():
    nombre = request.form.get("dato")
    mail = request.form.get("mail", "")  # opcional
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO usuarios (nombre, mail) VALUES (%s, %s)", (nombre, mail))
    conn.commit()
    cursor.close()
    conn.close()
    return "Usuario guardado en MySQL"

@app.route('/leer_mysql')
def leer_mysql():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, mail FROM usuarios")
    datos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("resultado.html", datos=[f"{n} ({m})" for n, m in datos])

# -----------------------
# Ejecutar la app
# -----------------------
if __name__ == "__main__":
    app.run(debug=True)
from flask_sqlalchemy import SQLAlchemy

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database/usuarios.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Modelo de la tabla
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)

# Crear base de datos
with app.app_context():
    db.create_all()

# Guardar en SQLite
@app.route('/guardar_sqlite', methods=['POST'])
def guardar_sqlite():
    nombre = request.form.get("dato")
    nuevo_usuario = Usuario(nombre=nombre)
    db.session.add(nuevo_usuario)
    db.session.commit()
    return "Usuario guardado en SQLite"

# Leer desde SQLite
@app.route('/leer_sqlite')
def leer_sqlite():
    usuarios = Usuario.query.all()
    return render_template("resultado.html", datos=[u.nombre for u in usuarios])
# -----------------------
# PERSISTENCIA CON MySQL
# -----------------------
from mysql.connector import Error

@app.route('/guardar_mysql', methods=['POST'])
def guardar_mysql():
    nombre = request.form.get("dato")
    mail = request.form.get("mail", "")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (nombre, mail) VALUES (%s, %s)", (nombre, mail))
        conn.commit()
        cursor.close()
        conn.close()
        return "Usuario guardado en MySQL ✅"
    except Error as e:
        return f"Error al guardar en MySQL: {e}"

@app.route('/leer_mysql')
def leer_mysql():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, mail FROM usuarios")
        datos = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template("resultado.html", datos=[f"{n} ({m})" for n, m in datos])
    except Error as e:
        return f"Error al leer de MySQL: {e}"
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import User
from conexion.conexion import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "clave_secreta"

# Inicializar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE id_usuario = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        return User(user['id_usuario'], user['nombre'], user['email'], user['password'])
    return None

# -------------------
# Rutas
# -------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (nombre, email, password) VALUES (%s, %s, %s)", (nombre, email, password))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Usuario registrado correctamente')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.get_by_email(email)
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


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', nombre=current_user.nombre)


if __name__ == '__main__':
    app.run(debug=True)

