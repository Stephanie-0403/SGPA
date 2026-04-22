import sqlite3
import os
from datetime import datetime

# Usaremos un nombre de base de datos especifico
DB_NAME = "sgpa_local.db"

def get_db_path():
    """Devuelve la ruta absoluta a la base de datos para asegurar compatibilidad desde cualquier directorio."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, DB_NAME)

def get_connection():
    """Devuelve una conexión a la base de datos con row_factory como diccionarios y PRAGMA foreign_keys = ON"""
    conn = sqlite3.connect(get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Inicializa la base de datos si no existe, recreando todas las tablas."""
    conn = get_connection()
    cursor = conn.cursor()

    # Creación de tablas
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS categorias_usuarios (
            id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_categoria TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS usuarios (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_completo TEXT NOT NULL,
            num_identificacion TEXT UNIQUE NOT NULL,
            id_categoria INTEGER REFERENCES categorias_usuarios(id_categoria),
            correo_electronico TEXT,
            telefono TEXT,
            fecha_registro DATE DEFAULT CURRENT_DATE,
            estatus_usuario TEXT DEFAULT 'Activo'
        );

        CREATE TABLE IF NOT EXISTS credenciales (
            id_acceso INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER UNIQUE REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, 
            rol_sistema TEXT DEFAULT 'Admin'
        );

        CREATE TABLE IF NOT EXISTS materiales (
            id_material INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_material TEXT NOT NULL,
            codigo_material TEXT UNIQUE NOT NULL,
            categoria_material TEXT,
            cantidad_total INTEGER DEFAULT 0,
            cantidad_disponible INTEGER DEFAULT 0,
            descripcion TEXT,
            ubicacion_fisica TEXT
        );

        CREATE TABLE IF NOT EXISTS prestamos (
            id_prestamo INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER REFERENCES usuarios(id_usuario),
            id_material INTEGER REFERENCES materiales(id_material),
            fecha_prestamo DATE DEFAULT CURRENT_DATE,
            fecha_vencimiento DATE NOT NULL,
            fecha_devolucion_real DATE,
            estado_prestamo TEXT DEFAULT 'Activo'
        );

        CREATE TABLE IF NOT EXISTS auditoria_sistema (
            id_evento INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario_accion INTEGER REFERENCES usuarios(id_usuario),
            accion_detalle TEXT NOT NULL,
            fecha_hora DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # Triggers para control de stock
    cursor.executescript('''
        DROP TRIGGER IF EXISTS tr_restar_stock;
        CREATE TRIGGER tr_restar_stock AFTER INSERT ON prestamos
        BEGIN
            UPDATE materiales SET cantidad_disponible = cantidad_disponible - 1 WHERE id_material = NEW.id_material;
        END;

        DROP TRIGGER IF EXISTS tr_sumar_stock;
        CREATE TRIGGER tr_sumar_stock AFTER UPDATE OF fecha_devolucion_real ON prestamos
        WHEN NEW.fecha_devolucion_real IS NOT NULL AND OLD.fecha_devolucion_real IS NULL
        BEGIN
            UPDATE materiales SET cantidad_disponible = cantidad_disponible + 1 WHERE id_material = NEW.id_material;
        END;
    ''')

    # Insertar valores por defecto si la base de datos es nueva
    cursor.execute("SELECT count(*) FROM categorias_usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.executescript('''
            INSERT INTO categorias_usuarios (nombre_categoria) VALUES 
            ('Estudiante'), ('Docente'), ('Administrativo'), ('Mantenimiento'), ('Externo');

            INSERT INTO usuarios (nombre_completo, num_identificacion, id_categoria) 
            VALUES ('Administrador Global', 'ADMIN-01', 3);

            INSERT INTO credenciales (id_usuario, username, password_hash, rol_sistema) 
            VALUES ((SELECT id_usuario FROM usuarios WHERE num_identificacion = 'ADMIN-01' LIMIT 1), 'admin', '1234', 'Admin');

            INSERT INTO materiales (nombre_material, codigo_material, cantidad_total, cantidad_disponible) 
            VALUES ('Laptop HP', 'HP-001', 5, 5);
        ''')

    conn.commit()
    conn.close()

# --- FUNCIONES DE AUTENTICACIÓN ---
def validar_login(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT c.*, u.nombre_completo, u.num_identificacion
        FROM credenciales c
        JOIN usuarios u ON c.id_usuario = u.id_usuario
        WHERE c.username = ? AND c.password_hash = ?
    """, (username, password))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None

# --- FUNCIONES DE USUARIOS ---
def obtener_usuarios():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT u.id_usuario, u.nombre_completo, u.num_identificacion, cat.nombre_categoria as grupo
        FROM usuarios u
        LEFT JOIN categorias_usuarios cat ON u.id_categoria = cat.id_categoria
        WHERE u.estatus_usuario = 'Activo'
    ''')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- FUNCIONES DE MATERIALES ---
def obtener_materiales():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id_material, codigo_material, nombre_material, cantidad_disponible, cantidad_total FROM materiales")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# --- FUNCIONES DE PRÉSTAMOS ---
def obtener_prestamos_activos():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT p.id_prestamo, u.nombre_completo, m.nombre_material, p.fecha_prestamo, p.fecha_vencimiento
        FROM prestamos p
        JOIN usuarios u ON p.id_usuario = u.id_usuario
        JOIN materiales m ON p.id_material = m.id_material
        WHERE p.estado_prestamo = 'Activo' AND p.fecha_devolucion_real IS NULL
    ''')
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def registrar_prestamo(id_usuario, id_material, fecha_vencimiento):
    conn = get_connection()
    c = conn.cursor()
    try:
        # Verificar stock
        c.execute("SELECT cantidad_disponible FROM materiales WHERE id_material = ?", (id_material,))
        disp = c.fetchone()
        if not disp or disp['cantidad_disponible'] <= 0:
            return False, "Material sin stock disponible."
            
        c.execute('''
            INSERT INTO prestamos (id_usuario, id_material, fecha_vencimiento)
            VALUES (?, ?, ?)
        ''', (id_usuario, id_material, fecha_vencimiento))
        conn.commit()
        return True, "Préstamo registrado exitosamente. (Stock reducido vía trigger)"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def registrar_devolucion(id_prestamo):
    conn = get_connection()
    c = conn.cursor()
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    try:
        c.execute("SELECT fecha_devolucion_real FROM prestamos WHERE id_prestamo = ?", (id_prestamo,))
        prestamo = c.fetchone()
        if not prestamo:
            return False, "Préstamo no encontrado."
        if prestamo['fecha_devolucion_real'] is not None:
             return False, "Este préstamo ya ha sido devuelto."

        c.execute('''
            UPDATE prestamos 
            SET fecha_devolucion_real = ?, estado_prestamo = 'Devuelto'
            WHERE id_prestamo = ?
        ''', (fecha_actual, id_prestamo))
        conn.commit()
        return True, "Devolución registrada exitosamente. (Stock reabastecido vía trigger)"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

# Auto-Setup de la base de datos al importar el módulo por primera vez
init_db()
