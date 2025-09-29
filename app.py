from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from xhtml2pdf import pisa
from io import BytesIO
from datetime import datetime
from flask_migrate import Migrate
import os

# ---------------------------
# Configuración Flask
# ---------------------------
app = Flask(__name__)
app.secret_key = os.urandom(24)  # clave más segura

# ---------------------------
# Configuración SQLAlchemy
# ---------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/desarrollo_web'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ---------------------------
# Modelos
# ---------------------------
class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id = db.Column('id_usuario', db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Compra(db.Model):
    __tablename__ = 'compras'
    id_compra = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)

class DetalleCompra(db.Model):
    __tablename__ = 'detalle_compra'
    id_detalle = db.Column(db.Integer, primary_key=True)
    id_compra = db.Column(db.Integer, db.ForeignKey('compras.id_compra'), nullable=False)
    id_producto = db.Column(db.Integer, nullable=False)
    nombre_producto = db.Column(db.String(100), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    imagen = db.Column(db.String(100), nullable=False)

# ---------------------------
# Flask-Login
# ---------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# ---------------------------
# Catálogo de productos
# ---------------------------
CATALOGO = [
    {"id_producto": 1, "nombre": "Galleta Pink Star", "precio": 2.5, "imagen": "galleta1.png"},
    {"id_producto": 2, "nombre": "Galleta Cute Heart", "precio": 3.0, "imagen": "galleta2.png"},
    {"id_producto": 3, "nombre": "Galleta Mini Bunny", "precio": 2.0, "imagen": "galleta3.png"},
    {"id_producto": 4, "nombre": "Galleta Sweet Cloud", "precio": 2.8, "imagen": "galleta4.png"},
    {"id_producto": 5, "nombre": "Galleta Lovely Cupcake", "precio": 3.5, "imagen": "galleta5.png"},
]

# ---------------------------
# Rutas principales
# ---------------------------
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']

        if Usuario.query.filter_by(email=email).first():
            flash('El correo ya está registrado', 'warning')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        nuevo_usuario = Usuario(nombre=nombre, email=email, password=hashed_password)
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('Usuario registrado con éxito. Ahora puedes iniciar sesión.', 'success')
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
            return redirect(url_for('catalogo'))
        else:
            flash('Credenciales incorrectas', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('carrito', None)
    return redirect(url_for('login'))

@app.route('/catalogo')
@login_required
def catalogo():
    return render_template("catalogo.html", productos=CATALOGO)

# ---------------------------
# Carrito
# ---------------------------
@app.route('/carrito')
@login_required
def ver_carrito():
    carrito = session.get('carrito', {})
    productos = []
    total = 0

    for id_str, cantidad in carrito.items():
        producto = next((p for p in CATALOGO if p["id_producto"] == int(id_str)), None)
        if producto:
            subtotal = float(producto["precio"]) * int(cantidad)
            total += subtotal
            productos.append({
                "id_producto": producto["id_producto"],
                "nombre": producto["nombre"],
                "precio": producto["precio"],
                "imagen": producto["imagen"],
                "cantidad": cantidad,
                "subtotal": subtotal
            })

    return render_template('carrito.html', productos=productos, total=total)

@app.route('/agregar/<int:producto_id>', methods=['POST'])
@login_required
def agregar_al_carrito(producto_id):
    producto = next((p for p in CATALOGO if p["id_producto"] == producto_id), None)
    if not producto:
        flash("Producto no encontrado", "danger")
        return redirect(url_for('catalogo'))

    carrito = session.get('carrito', {})
    id_str = str(producto_id)
    carrito[id_str] = carrito.get(id_str, 0) + 1
    session['carrito'] = carrito
    session.modified = True
    flash(f'{producto["nombre"]} se agregó a tu canasta 🛒', 'success')
    return redirect(url_for('catalogo'))

@app.route('/actualizar_carrito/<int:producto_id>', methods=['POST'])
@login_required
def actualizar_carrito(producto_id):
    accion = request.form['accion']
    carrito = session.get('carrito', {})
    id_str = str(producto_id)
    if id_str in carrito:
        if accion == 'sumar':
            carrito[id_str] += 1
        elif accion == 'restar' and carrito[id_str] > 1:
            carrito[id_str] -= 1
    session['carrito'] = carrito
    session.modified = True
    return redirect(url_for('ver_carrito'))

@app.route('/eliminar/<int:producto_id>')
@login_required
def eliminar_del_carrito(producto_id):
    carrito = session.get('carrito', {})
    carrito.pop(str(producto_id), None)
    session['carrito'] = carrito
    session.modified = True
    flash('Producto eliminado de la canasta 🗑️', 'info')
    return redirect(url_for('ver_carrito'))

# ---------------------------
# Finalizar compra
# ---------------------------
@app.route('/finalizar_compra', methods=['POST'])
@login_required
def finalizar_compra():
    carrito = session.get('carrito', {})
    if not carrito:
        flash('Tu canasta está vacía', 'info')
        return redirect(url_for('catalogo'))

    total = sum(
        float(next(p for p in CATALOGO if p["id_producto"] == int(id_str))["precio"]) * int(cantidad)
        for id_str, cantidad in carrito.items()
    )

    num_facturas_usuario = Compra.query.filter_by(id_usuario=current_user.id).count()
    num_factura_usuario = num_facturas_usuario + 1

    nueva_compra = Compra(
        id_usuario=current_user.id,
        total=round(total, 2),
        fecha=datetime.utcnow()
    )
    db.session.add(nueva_compra)
    db.session.commit()

    for id_str, cantidad in carrito.items():
        producto = next((p for p in CATALOGO if p["id_producto"] == int(id_str)), None)
        if producto:
            detalle = DetalleCompra(
                id_compra=nueva_compra.id_compra,
                id_producto=producto["id_producto"],
                nombre_producto=producto["nombre"],
                cantidad=int(cantidad),
                precio=float(producto["precio"]),
                imagen=producto["imagen"]
            )
            db.session.add(detalle)
    db.session.commit()

    session.pop('carrito')
    flash(f'Compra finalizada con éxito. Factura #{num_factura_usuario} - Total: ${total:.2f}', 'success')
    return redirect(url_for('mis_compras'))

# ---------------------------
# Historial de compras
# ---------------------------
@app.route('/mis_compras')
@login_required
def mis_compras():
    compras = Compra.query.filter_by(id_usuario=current_user.id).order_by(Compra.fecha.asc()).all()
    detalles = {c.id_compra: DetalleCompra.query.filter_by(id_compra=c.id_compra).all() for c in compras}

    # Asignar número temporal para cada compra
    for idx, compra in enumerate(compras, start=1):
        compra.numero_usuario = idx

    return render_template('mis_compras.html', compras=compras, detalles=detalles)

# ---------------------------
# Factura PDF
# ---------------------------
@app.route('/factura/<int:id_compra>')
@login_required
def factura(id_compra):
    compra = Compra.query.get_or_404(id_compra)
    if compra.id_usuario != current_user.id:
        flash("No tienes permiso para ver esta factura", "danger")
        return redirect(url_for('mis_compras'))

    detalles = DetalleCompra.query.filter_by(id_compra=id_compra).all()
    total = sum(d.precio * d.cantidad for d in detalles)

    rendered = render_template('factura_pdf.html', compra=compra, detalles=detalles, usuario=current_user, total=total)
    pdf = BytesIO()
    result = pisa.CreatePDF(rendered, dest=pdf)
    if result.err:
        flash("Error al generar PDF", "danger")
        return redirect(url_for('mis_compras'))

    pdf.seek(0)
    return send_file(pdf, as_attachment=True, download_name=f"factura_{compra.id_compra}.pdf", mimetype='application/pdf')

# ---------------------------
# Ejecutar app
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
