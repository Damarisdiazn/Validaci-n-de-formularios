from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import os

# ---------------------------
# Configuración Flask
# ---------------------------
app = Flask(__name__)
app.secret_key = "clave_secreta"

# ---------------------------
# Configuración SQLite para usuarios
# ---------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'database', 'usuarios.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

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
# Conexión MySQL para productos
# ---------------------------
def get_mysql_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",         # cambia según tu usuario
        password="",         # cambia según tu contraseña
        database="desarrollo_web"
    )

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
            flash('Credenciales incorrectas', "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ---------------------------
# CRUD de productos
# ---------------------------
@app.route("/productos")
def productos():
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM productos")
    productos_db = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("productos.html", productos=productos_db)

@app.route("/crear", methods=["GET", "POST"])
def crear():
    if request.method == "POST":
        nombre = request.form["nombre"]
        precio = request.form["precio"]
        stock = request.form["stock"]

        if not nombre or not precio or not stock:
            flash("Todos los campos son obligatorios", "warning")
            return redirect(url_for("crear"))

        conn = get_mysql_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO productos (nombre, precio, stock) VALUES (%s, %s, %s)",
            (nombre, precio, stock)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Producto creado exitosamente", "success")
        return redirect(url_for("productos"))

    return render_template("formulario.html")

@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    conn = get_mysql_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM productos WHERE id_producto = %s", (id,))
    producto = cursor.fetchone()

    if request.method == "POST":
        nombre = request.form["nombre"]
        precio = request.form["precio"]
        stock = request.form["stock"]

        cursor.execute("""
            UPDATE productos SET nombre=%s, precio=%s, stock=%s WHERE id_producto=%s
        """, (nombre, precio, stock, id))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Producto actualizado exitosamente", "info")
        return redirect(url_for("productos"))

    cursor.close()
    conn.close()
    return render_template("editar.html", producto=producto)

@app.route("/eliminar/<int:id>")
def eliminar(id):
    conn = get_mysql_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productos WHERE id_producto = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Producto eliminado", "danger")
    return redirect(url_for("productos"))
@app.route('/leer_csv')
def leer_csv():
    import csv, os
    RUTA_CSV = "datos/datos.csv"
    if not os.path.exists(RUTA_CSV):
        return "No hay datos en CSV"
    with open(RUTA_CSV, "r") as f:
        lector = csv.reader(f)
        datos = [fila for fila in lector]
    return render_template("resultado.html", datos=datos)


# ---------------------------
# Ejecutar la app
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
