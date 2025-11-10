import sqlite3
import os

# Ruta donde se guardará la base de datos (tu Escritorio)
db_path = r"C:\Users\vale\Desktop\plantlist.db"

print("📂 Creando base de datos en:", db_path)

# Crear o conectar la base de datos en el Escritorio
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Crear tabla principal de equipos
cursor.execute("""
CREATE TABLE IF NOT EXISTS equipos (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    TIPO_EQUIPO TEXT,
    EQUIPO TEXT,
    NUM_SERIE TEXT,
    CAPACIDAD TEXT,
    STATUS TEXT,
    LOCATION TEXT,
    OBSERVACIONES TEXT,
    PROPIETARIO TEXT,
    ARRENDAMIENTO TEXT,
    MODELO TEXT,
    FABRICANTE TEXT,
    FABRICACION TEXT,
    FABRICANTE_ENGINE TEXT,
    FABRICANTE_TRANSMISION TEXT,
    PUESTA_MARCHA TEXT,
    FECHA_CREACION TEXT
)
""")

# Crear tabla para registrar cambios de status
cursor.execute("""
CREATE TABLE IF NOT EXISTS cambios_status (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    TIPO_EQUIPO TEXT,
    EQUIPO TEXT,
    STATUS TEXT,
    LOCATION TEXT,
    OBSERVACIONES TEXT,
    PROPIETARIO TEXT,
    ARRENDAMIENTO TEXT,
    FECHA_CAMBIO TEXT DEFAULT (datetime('now','localtime'))
)
""")

conn.commit()
conn.close()

print("✅ Base de datos y tablas creadas correctamente en el Escritorio.")
