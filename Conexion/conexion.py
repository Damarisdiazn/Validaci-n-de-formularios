# Conexion/conexion.py
import mysql.connector

def get_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="usuario_flask",  # el usuario que creaste en phpMyAdmin
        password="tu_contraseña",
        database="desarrollo_web"
    )
    return connection
