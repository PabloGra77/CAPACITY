# database.py
import sqlite3
from datetime import datetime

# Función para inicializar la base de datos
def init_db():
    """Crea la tabla de registros si no existe."""
    with sqlite3.connect('capacitacion.db') as conn:
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombres TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            cedula TEXT NOT NULL UNIQUE,
            correo TEXT NOT NULL,
            area TEXT NOT NULL,
            fecha_inicio TIMESTAMP,
            fecha_fin TIMESTAMP,
            duracion_segundos INTEGER
        )
        ''')
        conn.commit()

# Función para añadir un registro completo
def add_record(data):
    """Añade un nuevo registro de capacitación a la base de datos."""
    with sqlite3.connect('capacitacion.db') as conn:
        c = conn.cursor()
        c.execute('''
        INSERT INTO registros (nombres, apellidos, cedula, correo, area, fecha_inicio, fecha_fin, duracion_segundos)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
        conn.commit() 
