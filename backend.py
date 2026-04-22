import sqlite3
from datetime import datetime

class BackendControlador:
    def __init__(self, db_name="sistema_prestamos.db"):
        self.db_name = db_name
        self._inicializar_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_name)

    def _inicializar_db(self):
        """Crea las tablas necesarias si no existen."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Tabla de Usuarios
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    identificacion TEXT UNIQUE NOT NULL,
                    grupo TEXT NOT NULL,
                    fecha_registro TEXT NOT NULL
                )
            ''')
            # Tabla de Materiales
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS materiales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    codigo TEXT UNIQUE NOT NULL,
                    cantidad INTEGER NOT NULL,
                    descripcion TEXT
                )
            ''')
            # Tabla de Credenciales (Simple para el ejemplo)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS credenciales (
                    usuario TEXT PRIMARY KEY,
                    password TEXT NOT NULL
                )
            ''')
            # Insertar admin por defecto si no existe
            cursor.execute("INSERT OR IGNORE INTO credenciales (usuario, password) VALUES (?, ?)", ("admin", "1234"))
            conn.commit()

    # --- Métodos de Acceso ---
    def validar_acceso(self, u, p):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM credenciales WHERE usuario = ? AND password = ?", (u, p))
            return cursor.fetchone() is not None

    # --- Métodos de Usuarios ---
    def registrar_usuario(self, nombre, ident, grupo):
        fecha = datetime.now().strftime("%Y-%m-%d")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO usuarios (nombre, identificacion, grupo, fecha_registro) 
                    VALUES (?, ?, ?, ?)
                """, (nombre, ident, grupo, fecha))
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False # Identificación duplicada

    def obtener_usuarios(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, identificacion, grupo FROM usuarios")
            rows = cursor.fetchall()
            return [{"id": r[0], "nombre": r[1], "ident": r[2], "grupo": r[3]} for r in rows]

    # --- Métodos de Materiales ---
    def registrar_material(self, nombre, codigo, cant, desc):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO materiales (nombre, codigo, cantidad, descripcion) 
                    VALUES (?, ?, ?, ?)
                """, (nombre, codigo, int(qty) if isinstance(cant, str) else cant, desc))
                conn.commit()
            return True
        except Exception:
            return False

    def obtener_materiales(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT codigo, nombre, cantidad FROM materiales")
            rows = cursor.fetchall()
            return [{"codigo": r[0], "nombre": r[1], "cant": r[2]} for r in rows]
