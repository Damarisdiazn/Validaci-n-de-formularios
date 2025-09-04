from flask import Flask, render_template, request, jsonify
import json, csv, os
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- Rutas de archivos ---
RUTA_TXT = "datos/datos.txt"
RUTA_JSON = "datos/datos.json"
RUTA_CSV = "datos/datos.csv"

# --- Config SQLite ---
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database/usuarios.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# --- Modelo BD ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)

with app.app_context():
    db.create_all()

# Página principal
@app.route('/')
def index():
    return render_template("index.html")


# -----------------------
# PERSISTENCIA CON TXT
# -----------------------
@app.route('/guardar_txt', methods=['POST'])
def guardar_txt():
    dato = request.form.get("dato")
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
# PERSISTENCIA CON JSON
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
# PERSISTENCIA CON CSV
# -----------------------
@app.route('/guardar_csv', methods=['POST'])
def guardar_csv():
    dato = request.form.get("dato")
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
# PERSISTENCIA CON SQLITE
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


# Ejecutar la app
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
