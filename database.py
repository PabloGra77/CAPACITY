# database.py

# =========================================================
# ESTE ES UN ESQUELETO DE EJEMPLO PARA CORREGIR EL IMPORTERROR
# DEBES IMPLEMENTAR LA LÓGICA DE SQLITE REAL AQUÍ
# =========================================================

def init_db():
    """Inicializa la base de datos (crea las tablas 'users' y 'records')."""
    # Lógica de SQLite para crear tablas de usuarios y registros.
    print("Base de datos inicializada (simulado).")
    pass # Reemplazar con la lógica de conexión y creación de tablas

def add_record(record_data):
    """Añade un nuevo registro de capacitación."""
    # Lógica de SQLite para insertar un nuevo registro.
    print(f"Registro añadido (simulado): {record_data}")
    pass # Reemplazar con la lógica de inserción

def check_user_credentials(username, password):
    """Verifica credenciales y devuelve datos del usuario si son válidas."""
    # Lógica REAL: Conectarse a la DB, buscar usuario, verificar hash de contraseña (bcrypt).
    
    # --- MOCKUP DE DATOS (REEMPLAZAR) ---
    if username == "admin" and password == "admin123":
        return {
            "role": "admin",
            "nombres": "Admin",
            "apellidos": "Master",
            "cedula": "00000",
            "correo": "admin@empresa.com",
            "area": "TI"
        }
    elif username == "testuser" and password == "pass123":
        return {
            "role": "user",
            "nombres": "Usuario",
            "apellidos": "Prueba",
            "cedula": "12345",
            "correo": "test@empresa.com",
            "area": "Ventas"
        }
    else:
        return None
    # ------------------------------------
