"""
============================================================
SGPA - Sistema de Control de Préstamos
Versión completa con PostgreSQL + bcrypt + multas + auditoría
============================================================
Dependencias:
    pip install psycopg2-binary bcrypt tkcalendar

Pasos para iniciar:
    1. admin
    2. contraseña:12345
============================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import csv
import tkinter.filedialog as fd

try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None

try:
    import bcrypt
    BCRYPT_OK = True
except ImportError:
    BCRYPT_OK = False
    print("ADVERTENCIA: bcrypt no instalado. Las contraseñas no estarán cifradas.")

try:
    import psycopg2
    from psycopg2 import OperationalError
    PSYCOPG2_OK = True
except ImportError:
    PSYCOPG2_OK = False
    print("ERROR: psycopg2 no instalado. Ejecuta: pip install psycopg2-binary")

# ============================================================
# CONFIGURACIÓN DE BASE DE DATOS — Supabase
# ============================================================
DB_CONFIG = {
    "host":     "db.qgmfgajllgafegukuyqt.supabase.co",
    "port":     5432,
    "dbname":   "postgres",
    "user":     "postgres",
    "password": "SGPA_database123",
    "sslmode":  "require"   # Supabase requiere SSL
}


# ============================================================
# BACKEND CONTROLADOR
# ============================================================
class BackendControlador:
    def __init__(self):
        self.conn = None
        self.conectar()
        self._migrar_password_hash()

    # ── Conexión ─────────────────────────────────────────────
    def conectar(self):
        if not PSYCOPG2_OK:
            return
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.conn.autocommit = True
        except OperationalError as e:
            self.conn = None
            messagebox.showerror(
                "Error de conexión",
                f"No se pudo conectar a la base de datos:\n{e}\n\n"
                "Verifica DB_CONFIG en la parte superior del archivo."
            )

    def _cursor(self):
        if self.conn is None or self.conn.closed:
            self.conectar()
        return self.conn.cursor()

    def _migrar_password_hash(self):
        """
        Si la contraseña en BD aún es texto plano (sin bcrypt),
        la cifra automáticamente al arrancar la aplicación.
        """
        if not BCRYPT_OK or self.conn is None:
            return
        try:
            cur = self._cursor()
            cur.execute("SELECT id_acceso, password_hash FROM credenciales")
            rows = cur.fetchall()
            for id_acceso, pwd in rows:
                if not pwd.startswith("$2b$") and not pwd.startswith("$2a$"):
                    nuevo_hash = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
                    cur.execute(
                        "UPDATE credenciales SET password_hash = %s WHERE id_acceso = %s",
                        (nuevo_hash, id_acceso)
                    )
            print("Contraseñas verificadas/migradas a bcrypt.")
        except Exception as e:
            print(f"Error en migración de hash: {e}")

    # ── LOGIN ─────────────────────────────────────────────────
    def validar_acceso(self, username, password):
        try:
            cur = self._cursor()
            cur.execute(
                "SELECT password_hash FROM credenciales WHERE username = %s",
                (username,)
            )
            row = cur.fetchone()
            if not row:
                return False
            pwd_hash = row[0]
            if BCRYPT_OK:
                return bcrypt.checkpw(password.encode(), pwd_hash.encode())
            else:
                return password == pwd_hash
        except Exception as e:
            print(f"Error en login: {e}")
            return False

    # ── AUDITORÍA ─────────────────────────────────────────────
    def registrar_auditoria(self, id_usuario, detalle):
        try:
            cur = self._cursor()
            cur.execute(
                "INSERT INTO auditoria_sistema (id_usuario_accion, accion_detalle) VALUES (%s, %s)",
                (id_usuario, detalle)
            )
        except Exception as e:
            print(f"Error en auditoría: {e}")

    def obtener_auditoria(self):
        cur = self._cursor()
        cur.execute("""
            SELECT a.id_evento, u.nombre_completo, a.accion_detalle, a.fecha_hora
            FROM auditoria_sistema a
            LEFT JOIN usuarios u ON a.id_usuario_accion = u.id_usuario
            ORDER BY a.fecha_hora DESC
            LIMIT 200
        """)
        return cur.fetchall()

    # ── USUARIOS ──────────────────────────────────────────────
    def registrar_usuario(self, nombre, ident, grupo, correo="", telefono=""):
        try:
            cur = self._cursor()
            cur.execute("""
                INSERT INTO usuarios
                    (nombre_completo, num_identificacion, id_categoria, correo_electronico, telefono)
                VALUES (%s, %s,
                    (SELECT id_categoria FROM categorias_usuarios WHERE nombre_categoria = %s),
                    %s, %s)
                RETURNING id_usuario
            """, (nombre, ident, grupo, correo, telefono))
            id_nuevo = cur.fetchone()[0]
            self.registrar_auditoria(id_nuevo, f"Usuario registrado: {nombre} ({ident})")
            return True
        except Exception as e:
            print(f"Error al registrar usuario: {e}")
            return False

    def obtener_usuarios(self):
        cur = self._cursor()
        cur.execute("""
            SELECT u.id_usuario, u.nombre_completo, u.num_identificacion,
                   c.nombre_categoria, u.estatus_usuario
            FROM usuarios u
            JOIN categorias_usuarios c ON u.id_categoria = c.id_categoria
            ORDER BY u.id_usuario
        """)
        return cur.fetchall()

    def eliminar_usuario(self, id_usuario):
        try:
            cur = self._cursor()
            cur.execute("DELETE FROM usuarios WHERE id_usuario = %s", (id_usuario,))
            return True
        except Exception as e:
            print(f"Error al eliminar usuario: {e}")
            return False

    def buscar_usuario(self, termino):
        cur = self._cursor()
        cur.execute("""
            SELECT u.id_usuario, u.nombre_completo, u.num_identificacion,
                   c.nombre_categoria, u.estatus_usuario
            FROM usuarios u
            JOIN categorias_usuarios c ON u.id_categoria = c.id_categoria
            WHERE u.nombre_completo ILIKE %s OR u.num_identificacion ILIKE %s
            ORDER BY u.id_usuario
        """, (f"%{termino}%", f"%{termino}%"))
        return cur.fetchall()

    # ── MATERIALES ────────────────────────────────────────────
    def registrar_material(self, nombre, codigo, cant, desc, categoria="", ubicacion=""):
        try:
            cur = self._cursor()
            cur.execute("""
                INSERT INTO materiales
                    (nombre_material, codigo_material, cantidad_total,
                     cantidad_disponible, descripcion, categoria_material, ubicacion_fisica)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (nombre, codigo, int(cant), int(cant), desc, categoria, ubicacion))
            return True
        except Exception as e:
            print(f"Error al registrar material: {e}")
            return False

    def obtener_materiales(self):
        cur = self._cursor()
        cur.execute("""
            SELECT codigo_material, nombre_material, cantidad_total,
                   cantidad_disponible, descripcion
            FROM materiales ORDER BY nombre_material
        """)
        return cur.fetchall()

    def eliminar_material(self, codigo):
        try:
            cur = self._cursor()
            cur.execute("DELETE FROM materiales WHERE codigo_material = %s", (codigo,))
            return True
        except Exception as e:
            print(f"Error al eliminar material: {e}")
            return False

    def buscar_material(self, termino):
        cur = self._cursor()
        cur.execute("""
            SELECT codigo_material, nombre_material, cantidad_total,
                   cantidad_disponible, descripcion
            FROM materiales
            WHERE nombre_material ILIKE %s OR codigo_material ILIKE %s
            ORDER BY nombre_material
        """, (f"%{termino}%", f"%{termino}%"))
        return cur.fetchall()

    # ── PRÉSTAMOS ─────────────────────────────────────────────
    def obtener_usuarios_activos(self):
        cur = self._cursor()
        cur.execute("""
            SELECT id_usuario, nombre_completo, num_identificacion
            FROM usuarios WHERE estatus_usuario = 'Activo'
            ORDER BY nombre_completo
        """)
        return cur.fetchall()

    def obtener_materiales_disponibles(self):
        cur = self._cursor()
        cur.execute("""
            SELECT id_material, nombre_material, cantidad_disponible
            FROM materiales WHERE cantidad_disponible > 0
            ORDER BY nombre_material
        """)
        return cur.fetchall()

    def registrar_prestamo(self, id_usuario, id_material, fecha_vencimiento):
        try:
            cur = self._cursor()
            cur.execute("""
                INSERT INTO prestamos (id_usuario, id_material, fecha_vencimiento)
                VALUES (%s, %s, %s)
            """, (id_usuario, id_material, fecha_vencimiento))
            return True
        except Exception as e:
            print(f"Error al registrar préstamo: {e}")
            return False

    # ── DEVOLUCIONES ──────────────────────────────────────────
    def obtener_prestamos_activos(self):
        cur = self._cursor()
        cur.execute("""
            SELECT p.id_prestamo, u.nombre_completo, m.nombre_material, p.fecha_vencimiento
            FROM prestamos p
            JOIN usuarios u ON p.id_usuario = u.id_usuario
            JOIN materiales m ON p.id_material = m.id_material
            WHERE p.estado_prestamo = 'Activo'
            ORDER BY p.fecha_vencimiento
        """)
        return cur.fetchall()

    def registrar_devolucion(self, id_prestamo):
        try:
            cur = self._cursor()
            cur.execute("""
                UPDATE prestamos
                SET fecha_devolucion_real = CURRENT_DATE,
                    estado_prestamo = 'Devuelto'
                WHERE id_prestamo = %s
            """, (id_prestamo,))
            return True
        except Exception as e:
            print(f"Error al registrar devolución: {e}")
            return False

    # ── MULTAS ────────────────────────────────────────────────
    def obtener_multas(self, solo_pendientes=False):
        cur = self._cursor()
        query = """
            SELECT m.id_multa, u.nombre_completo, mat.nombre_material,
                   m.motivo, m.monto, m.estado_multa,
                   m.fecha_generada, m.fecha_pagada
            FROM multas m
            JOIN usuarios u   ON m.id_usuario  = u.id_usuario
            JOIN prestamos p  ON m.id_prestamo = p.id_prestamo
            JOIN materiales mat ON p.id_material = mat.id_material
        """
        if solo_pendientes:
            query += " WHERE m.estado_multa = 'Pendiente'"
        query += " ORDER BY m.fecha_generada DESC"
        cur.execute(query)
        return cur.fetchall()

    def pagar_multa(self, id_multa):
        try:
            cur = self._cursor()
            cur.execute("""
                UPDATE multas
                SET estado_multa = 'Pagada', fecha_pagada = CURRENT_DATE
                WHERE id_multa = %s AND estado_multa = 'Pendiente'
            """, (id_multa,))
            return cur.rowcount > 0
        except Exception as e:
            print(f"Error al pagar multa: {e}")
            return False

    def registrar_multa_manual(self, id_prestamo, id_usuario, motivo, monto):
        try:
            cur = self._cursor()
            cur.execute("""
                INSERT INTO multas (id_prestamo, id_usuario, motivo, monto)
                VALUES (%s, %s, %s, %s)
            """, (id_prestamo, id_usuario, motivo, monto))
            return True
        except Exception as e:
            print(f"Error al registrar multa: {e}")
            return False

    def obtener_prestamos_para_multa(self):
        cur = self._cursor()
        cur.execute("""
            SELECT p.id_prestamo, u.nombre_completo, m.nombre_material, p.id_usuario
            FROM prestamos p
            JOIN usuarios u   ON p.id_usuario  = u.id_usuario
            JOIN materiales m ON p.id_material = m.id_material
            WHERE p.estado_prestamo = 'Devuelto'
              AND p.id_prestamo NOT IN (SELECT id_prestamo FROM multas)
            ORDER BY p.id_prestamo DESC
        """)
        return cur.fetchall()

    # ── REPORTES ──────────────────────────────────────────────
    def reporte_prestamos_activos(self):
        cur = self._cursor()
        cur.execute("""
            SELECT p.id_prestamo, u.nombre_completo, m.nombre_material,
                   p.fecha_prestamo, p.fecha_vencimiento
            FROM prestamos p
            JOIN usuarios u   ON p.id_usuario  = u.id_usuario
            JOIN materiales m ON p.id_material = m.id_material
            WHERE p.estado_prestamo = 'Activo'
            ORDER BY p.fecha_vencimiento
        """)
        return cur.fetchall()

    def reporte_historial(self):
        cur = self._cursor()
        cur.execute("""
            SELECT p.id_prestamo, u.nombre_completo, m.nombre_material,
                   p.fecha_prestamo, p.fecha_devolucion_real, p.estado_prestamo
            FROM prestamos p
            JOIN usuarios u   ON p.id_usuario  = u.id_usuario
            JOIN materiales m ON p.id_material = m.id_material
            ORDER BY p.fecha_prestamo DESC
        """)
        return cur.fetchall()

    def reporte_inventario(self):
        cur = self._cursor()
        cur.execute("""
            SELECT codigo_material, nombre_material, cantidad_total, cantidad_disponible
            FROM materiales ORDER BY nombre_material
        """)
        return cur.fetchall()

    def reporte_multas(self):
        cur = self._cursor()
        cur.execute("""
            SELECT m.id_multa, u.nombre_completo, m.motivo,
                   m.monto, m.estado_multa, m.fecha_generada
            FROM multas m
            JOIN usuarios u ON m.id_usuario = u.id_usuario
            ORDER BY m.fecha_generada DESC
        """)
        return cur.fetchall()


# ============================================================
# ESTILOS
# ============================================================
def setup_styles():
    style = ttk.Style()
    if 'clam' in style.theme_names():
        style.theme_use('clam')

    BG   = "#E0E0E0"
    BTN  = "#0056b3"
    TXT  = "#000000"

    style.configure('.',            background=BG, foreground=TXT, font=('Arial', 11))
    style.configure('TFrame',       background=BG)
    style.configure('TLabel',       background=BG, font=('Arial', 11))
    style.configure('TButton',      font=('Arial', 11, 'bold'), background=BTN, foreground='white')
    style.map('TButton',            background=[('active', '#004494'), ('pressed', '#003366')])
    style.configure('Treeview',     font=('Arial', 10), rowheight=25,
                    background="white", fieldbackground="white")
    style.configure('Treeview.Heading', font=('Arial', 11, 'bold'), background="#cccccc")
    style.configure('TEntry',       fieldbackground="white", padding=5)
    style.configure('TCombobox',    fieldbackground="white", padding=5)


# ============================================================
# APLICACIÓN PRINCIPAL
# ============================================================
class SGPA_App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SGPA - Sistema de Control de Préstamos")
        self.geometry("1100x768")
        self.minsize(1024, 700)
        self.configure(bg="#E0E0E0")
        self.backend = BackendControlador()
        setup_styles()

        self.frames = {}
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        for F in (LoginScreen, MainMenu, UserManagement, MaterialManagement,
                  LoanScreen, ReturnScreen, FineScreen, ReportScreen):
            name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("LoginScreen")

    def show_frame(self, page_name):
        self.frames[page_name].tkraise()


# ============================================================
# PANTALLA 1: LOGIN
# ============================================================
class LoginScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        inner = ttk.Frame(self)
        inner.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(inner, text="SGPA - Iniciar Sesión",
                  font=('Arial', 18, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 20))

        ttk.Label(inner, text="Usuario:").grid(row=1, column=0, sticky="e", pady=10, padx=10)
        self.entry_user = ttk.Entry(inner, width=25)
        self.entry_user.grid(row=1, column=1, pady=10, padx=10)

        ttk.Label(inner, text="Contraseña:").grid(row=2, column=0, sticky="e", pady=10, padx=10)
        self.entry_pass = ttk.Entry(inner, show="*", width=25)
        self.entry_pass.grid(row=2, column=1, pady=10, padx=10)
        self.entry_pass.bind("<Return>", lambda e: self.login())

        ttk.Button(inner, text="Iniciar sesión",
                   command=self.login).grid(row=3, column=0, columnspan=2, pady=(20, 10),
                                            ipadx=20, ipady=5)
        ttk.Button(inner, text="Salir",
                   command=self.controller.quit).grid(row=4, column=0, columnspan=2,
                                                      ipadx=20, ipady=5)

    def login(self):
        user = self.entry_user.get().strip()
        pasw = self.entry_pass.get()
        if self.controller.backend.validar_acceso(user, pasw):
            self.entry_pass.delete(0, tk.END)
            self.controller.show_frame("MainMenu")
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos.")


# ============================================================
# PANTALLA 2: MENÚ PRINCIPAL
# ============================================================
class MainMenu(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Menú Principal",
                  font=('Arial', 24, 'bold')).pack(pady=40)

        btn_frame = ttk.Frame(self)
        btn_frame.pack()

        buttons = [
            ("👤  Gestión de Usuarios",    "UserManagement"),
            ("📦  Gestión de Materiales",  "MaterialManagement"),
            ("📋  Préstamos",              "LoanScreen"),
            ("↩️  Devoluciones",           "ReturnScreen"),
            ("⚠️  Multas",                 "FineScreen"),
            ("📊  Reportes",               "ReportScreen"),
        ]

        for text, frame_name in buttons:
            ttk.Button(btn_frame, text=text,
                       command=lambda f=frame_name: self.controller.show_frame(f)
                       ).pack(fill="x", pady=8, ipadx=40, ipady=10)

        ttk.Button(btn_frame, text="🚪  Cerrar sesión",
                   command=lambda: self.controller.show_frame("LoginScreen")
                   ).pack(fill="x", pady=(30, 0), ipadx=40, ipady=10)


# ============================================================
# PANTALLA 3: GESTIÓN DE USUARIOS
# ============================================================
class UserManagement(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._selected_id = None

        ttk.Label(self, text="Gestión de Usuarios",
                  font=('Arial', 18, 'bold')).pack(pady=15)

        content = ttk.Frame(self)
        content.pack(fill="both", expand=True, padx=20, pady=5)

        # ── Formulario ──────────────────────────────────────
        frm_left = ttk.Frame(content)
        frm_left.pack(side="left", fill="y", padx=15)

        fields = [
            ("Nombre completo:",        "e_name",  False),
            ("Núm. identificación:",    "e_ident", False),
            ("Correo electrónico:",     "e_mail",  False),
            ("Teléfono:",               "e_tel",   False),
        ]
        for r, (lbl, attr, disabled) in enumerate(fields):
            ttk.Label(frm_left, text=lbl).grid(row=r, column=0, sticky="e", pady=5, padx=5)
            e = ttk.Entry(frm_left, width=28)
            e.grid(row=r, column=1, pady=5, sticky="w")
            setattr(self, attr, e)

        ttk.Label(frm_left, text="Grupo:").grid(row=4, column=0, sticky="e", pady=5, padx=5)
        self.cmb_group = ttk.Combobox(frm_left, width=26,
            values=["Estudiante", "Docente", "Administrativo", "Mantenimiento", "Externo"],
            state="readonly")
        self.cmb_group.grid(row=4, column=1, pady=5, sticky="w")

        # Búsqueda
        ttk.Label(frm_left, text="Buscar:").grid(row=5, column=0, sticky="e", pady=5, padx=5)
        self.e_search = ttk.Entry(frm_left, width=20)
        self.e_search.grid(row=5, column=1, pady=5, sticky="w")
        ttk.Button(frm_left, text="🔍 Buscar",
                   command=self.buscar).grid(row=5, column=2, padx=5)

        # Botones
        frm_btns = ttk.Frame(frm_left)
        frm_btns.grid(row=6, column=0, columnspan=3, pady=15)

        ttk.Button(frm_btns, text="Registrar",
                   command=self.registrar_usuario).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(frm_btns, text="Eliminar",
                   command=self.eliminar).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frm_btns, text="Limpiar",
                   command=self.limpiar).grid(row=1, column=0, columnspan=2,
                                              padx=5, pady=5, sticky="ew")

        ttk.Button(frm_left, text="← Volver al Menú",
                   command=lambda: self.controller.show_frame("MainMenu")
                   ).grid(row=7, column=0, columnspan=3, pady=20)

        # ── Tabla ────────────────────────────────────────────
        frm_right = ttk.Frame(content)
        frm_right.pack(side="right", fill="both", expand=True)

        cols = ("ID", "Nombre", "Identificación", "Grupo", "Estatus")
        self.tree = ttk.Treeview(frm_right, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor="center", width=120)
        self.tree.column("Nombre", width=160)

        scroll = ttk.Scrollbar(frm_right, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        self.actualizar_tabla()

    def actualizar_tabla(self, datos=None):
        for i in self.tree.get_children():
            self.tree.delete(i)
        rows = datos if datos is not None else self.controller.backend.obtener_usuarios()
        for row in rows:
            self.tree.insert("", "end", values=row)

    def on_select(self, event):
        sel = self.tree.selection()
        if sel:
            vals = self.tree.item(sel[0])["values"]
            self._selected_id = vals[0]

    def registrar_usuario(self):
        nom  = self.e_name.get().strip()
        ide  = self.e_ident.get().strip()
        grp  = self.cmb_group.get()
        mail = self.e_mail.get().strip()
        tel  = self.e_tel.get().strip()
        if not nom or not ide or not grp:
            messagebox.showwarning("Atención", "Nombre, identificación y grupo son obligatorios.")
            return
        if self.controller.backend.registrar_usuario(nom, ide, grp, mail, tel):
            messagebox.showinfo("Éxito", "Usuario registrado correctamente.")
            self.limpiar()
            self.actualizar_tabla()
        else:
            messagebox.showerror("Error", "No se pudo registrar. Verifique que la identificación no esté repetida.")

    def eliminar(self):
        if not self._selected_id:
            messagebox.showwarning("Atención", "Selecciona un usuario de la tabla.")
            return
        if messagebox.askyesno("Confirmar", f"¿Eliminar usuario ID {self._selected_id}?"):
            if self.controller.backend.eliminar_usuario(self._selected_id):
                messagebox.showinfo("Éxito", "Usuario eliminado.")
                self._selected_id = None
                self.actualizar_tabla()
            else:
                messagebox.showerror("Error", "No se pudo eliminar (puede tener préstamos activos).")

    def buscar(self):
        termino = self.e_search.get().strip()
        if termino:
            self.actualizar_tabla(self.controller.backend.buscar_usuario(termino))
        else:
            self.actualizar_tabla()

    def limpiar(self):
        for attr in ("e_name", "e_ident", "e_mail", "e_tel", "e_search"):
            getattr(self, attr).delete(0, tk.END)
        self.cmb_group.set("")
        self._selected_id = None
        self.actualizar_tabla()


# ============================================================
# PANTALLA 4: GESTIÓN DE MATERIALES
# ============================================================
class MaterialManagement(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._selected_code = None

        ttk.Label(self, text="Gestión de Materiales",
                  font=('Arial', 18, 'bold')).pack(pady=15)

        content = ttk.Frame(self)
        content.pack(fill="both", expand=True, padx=20, pady=5)

        frm_left = ttk.Frame(content)
        frm_left.pack(side="left", fill="y", padx=15)

        ttk.Label(frm_left, text="Nombre material:").grid(row=0, column=0, sticky="e", pady=5)
        self.e_name = ttk.Entry(frm_left, width=28)
        self.e_name.grid(row=0, column=1, pady=5, sticky="w")

        ttk.Label(frm_left, text="Código material:").grid(row=1, column=0, sticky="e", pady=5)
        self.e_code = ttk.Entry(frm_left, width=28)
        self.e_code.grid(row=1, column=1, pady=5, sticky="w")

        ttk.Label(frm_left, text="Categoría:").grid(row=2, column=0, sticky="e", pady=5)
        self.e_cat = ttk.Entry(frm_left, width=28)
        self.e_cat.grid(row=2, column=1, pady=5, sticky="w")

        ttk.Label(frm_left, text="Cantidad:").grid(row=3, column=0, sticky="e", pady=5)
        self.spin_qty = tk.Spinbox(frm_left, from_=0, to=9999, width=10, font=('Arial', 11))
        self.spin_qty.grid(row=3, column=1, pady=5, sticky="w")

        ttk.Label(frm_left, text="Ubicación:").grid(row=4, column=0, sticky="e", pady=5)
        self.e_ubic = ttk.Entry(frm_left, width=28)
        self.e_ubic.grid(row=4, column=1, pady=5, sticky="w")

        ttk.Label(frm_left, text="Descripción:").grid(row=5, column=0, sticky="ne", pady=5)
        self.txt_desc = tk.Text(frm_left, width=28, height=4, font=('Arial', 10))
        self.txt_desc.grid(row=5, column=1, pady=5, sticky="w")

        # Búsqueda
        ttk.Label(frm_left, text="Buscar:").grid(row=6, column=0, sticky="e", pady=5)
        self.e_search = ttk.Entry(frm_left, width=20)
        self.e_search.grid(row=6, column=1, pady=5, sticky="w")
        ttk.Button(frm_left, text="🔍",
                   command=self.buscar).grid(row=6, column=2, padx=3)

        frm_btns = ttk.Frame(frm_left)
        frm_btns.grid(row=7, column=0, columnspan=3, pady=15)
        ttk.Button(frm_btns, text="Registrar",
                   command=self.registrar_material).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(frm_btns, text="Eliminar",
                   command=self.eliminar).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frm_btns, text="Limpiar",
                   command=self.limpiar).grid(row=1, column=0, columnspan=2,
                                              padx=5, pady=5, sticky="ew")

        ttk.Button(frm_left, text="← Volver al Menú",
                   command=lambda: self.controller.show_frame("MainMenu")
                   ).grid(row=8, column=0, columnspan=3, pady=15)

        # ── Tabla ────────────────────────────────────────────
        frm_right = ttk.Frame(content)
        frm_right.pack(side="right", fill="both", expand=True)

        cols = ("Código", "Nombre", "Total", "Disponible", "Descripción")
        self.tree = ttk.Treeview(frm_right, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor="center", width=110)
        self.tree.column("Nombre", width=160)
        self.tree.column("Descripción", width=180)

        scroll = ttk.Scrollbar(frm_right, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        self.actualizar_tabla()

    def actualizar_tabla(self, datos=None):
        for i in self.tree.get_children():
            self.tree.delete(i)
        rows = datos if datos is not None else self.controller.backend.obtener_materiales()
        for row in rows:
            self.tree.insert("", "end", values=row)

    def on_select(self, event):
        sel = self.tree.selection()
        if sel:
            self._selected_code = self.tree.item(sel[0])["values"][0]

    def registrar_material(self):
        nom  = self.e_name.get().strip()
        cod  = self.e_code.get().strip()
        qty  = self.spin_qty.get()
        desc = self.txt_desc.get("1.0", tk.END).strip()
        cat  = self.e_cat.get().strip()
        ubic = self.e_ubic.get().strip()
        if not nom or not cod:
            messagebox.showwarning("Atención", "Nombre y código son obligatorios.")
            return
        if self.controller.backend.registrar_material(nom, cod, qty, desc, cat, ubic):
            messagebox.showinfo("Éxito", f"Material '{nom}' registrado.")
            self.limpiar()
            self.actualizar_tabla()
        else:
            messagebox.showerror("Error", "No se pudo registrar. Verifique que el código no esté repetido.")

    def eliminar(self):
        if not self._selected_code:
            messagebox.showwarning("Atención", "Selecciona un material de la tabla.")
            return
        if messagebox.askyesno("Confirmar", f"¿Eliminar material '{self._selected_code}'?"):
            if self.controller.backend.eliminar_material(self._selected_code):
                messagebox.showinfo("Éxito", "Material eliminado.")
                self._selected_code = None
                self.actualizar_tabla()
            else:
                messagebox.showerror("Error", "No se pudo eliminar (puede tener préstamos activos).")

    def buscar(self):
        termino = self.e_search.get().strip()
        if termino:
            self.actualizar_tabla(self.controller.backend.buscar_material(termino))
        else:
            self.actualizar_tabla()

    def limpiar(self):
        self.e_name.delete(0, tk.END)
        self.e_code.delete(0, tk.END)
        self.e_cat.delete(0, tk.END)
        self.e_ubic.delete(0, tk.END)
        self.e_search.delete(0, tk.END)
        self.spin_qty.delete(0, "end")
        self.spin_qty.insert(0, "0")
        self.txt_desc.delete("1.0", tk.END)
        self._selected_code = None
        self.actualizar_tabla()


# ============================================================
# PANTALLA 5: PRÉSTAMOS
# ============================================================
class LoanScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._usuarios   = []
        self._materiales = []

        ttk.Label(self, text="Registro de Préstamos",
                  font=('Arial', 18, 'bold')).pack(pady=30)

        frm = ttk.Frame(self)
        frm.pack(pady=10)

        ttk.Label(frm, text="Usuario:").grid(row=0, column=0, sticky="e", pady=10, padx=10)
        self.cmb_user = ttk.Combobox(frm, state="readonly", width=35)
        self.cmb_user.grid(row=0, column=1, pady=10, padx=10)

        ttk.Label(frm, text="Material:").grid(row=1, column=0, sticky="e", pady=10, padx=10)
        self.cmb_material = ttk.Combobox(frm, state="readonly", width=35)
        self.cmb_material.grid(row=1, column=1, pady=10, padx=10)

        ttk.Label(frm, text="Fecha préstamo:").grid(row=2, column=0, sticky="e", pady=10, padx=10)
        self.e_date_loan = ttk.Entry(frm, width=37)
        self.e_date_loan.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.e_date_loan.configure(state="disabled")
        self.e_date_loan.grid(row=2, column=1, pady=10, padx=10)

        ttk.Label(frm, text="Fecha devolución:").grid(row=3, column=0, sticky="e", pady=10, padx=10)
        if DateEntry:
            self.date_return = DateEntry(frm, width=34, date_pattern='yyyy-mm-dd')
            self.date_return.grid(row=3, column=1, pady=10, padx=10)
        else:
            self.date_return = ttk.Entry(frm, width=37)
            self.date_return.insert(0, "YYYY-MM-DD")
            self.date_return.grid(row=3, column=1, pady=10, padx=10)

        frm_btns = ttk.Frame(frm)
        frm_btns.grid(row=4, column=0, columnspan=2, pady=30)
        ttk.Button(frm_btns, text="Registrar Préstamo",
                   command=self.registrar).grid(row=0, column=0, padx=10, ipadx=10, ipady=5)
        ttk.Button(frm_btns, text="← Cancelar",
                   command=lambda: self.controller.show_frame("MainMenu")
                   ).grid(row=0, column=1, padx=10, ipadx=10, ipady=5)

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        self.cargar_combos()

    def cargar_combos(self):
        self._usuarios = self.controller.backend.obtener_usuarios_activos()
        self.cmb_user["values"] = [f"{r[1]}  ({r[2]})" for r in self._usuarios]

        self._materiales = self.controller.backend.obtener_materiales_disponibles()
        self.cmb_material["values"] = [f"{r[1]}  (Disp: {r[2]})" for r in self._materiales]

    def registrar(self):
        ui = self.cmb_user.current()
        mi = self.cmb_material.current()
        if ui == -1 or mi == -1:
            messagebox.showerror("Error", "Selecciona usuario y material.")
            return

        id_usuario  = self._usuarios[ui][0]
        id_material = self._materiales[mi][0]
        fecha_venc  = (self.date_return.get_date()
                       if DateEntry else self.date_return.get())

        if self.controller.backend.registrar_prestamo(id_usuario, id_material, fecha_venc):
            messagebox.showinfo("Éxito", "Préstamo registrado correctamente.")
            self.cmb_user.set("")
            self.cmb_material.set("")
            self.cargar_combos()
        else:
            messagebox.showerror("Error", "No se pudo registrar el préstamo.")


# ============================================================
# PANTALLA 6: DEVOLUCIONES
# ============================================================
class ReturnScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._prestamos = []

        ttk.Label(self, text="Registro de Devoluciones",
                  font=('Arial', 18, 'bold')).pack(pady=40)

        frm = ttk.Frame(self)
        frm.pack(pady=10)

        ttk.Label(frm, text="Préstamo activo:").grid(row=0, column=0, sticky="e", pady=10, padx=10)
        self.cmb_loan = ttk.Combobox(frm, state="readonly", width=45)
        self.cmb_loan.grid(row=0, column=1, pady=10, padx=10)

        ttk.Label(frm, text="Fecha devolución:").grid(row=1, column=0, sticky="e", pady=10, padx=10)
        self.e_date = ttk.Entry(frm, width=47)
        self.e_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.e_date.configure(state="disabled")
        self.e_date.grid(row=1, column=1, pady=10, padx=10)

        frm_btns = ttk.Frame(frm)
        frm_btns.grid(row=2, column=0, columnspan=2, pady=40)
        ttk.Button(frm_btns, text="Registrar Devolución",
                   command=self.registrar).grid(row=0, column=0, padx=10, ipadx=10, ipady=5)
        ttk.Button(frm_btns, text="← Cancelar",
                   command=lambda: self.controller.show_frame("MainMenu")
                   ).grid(row=0, column=1, padx=10, ipadx=10, ipady=5)

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        self.cargar_prestamos()

    def cargar_prestamos(self):
        self._prestamos = self.controller.backend.obtener_prestamos_activos()
        self.cmb_loan["values"] = [
            f"PR-{r[0]:03d}  |  {r[1]}  —  {r[2]}  (vence: {r[3]})"
            for r in self._prestamos
        ]

    def registrar(self):
        idx = self.cmb_loan.current()
        if idx == -1:
            messagebox.showerror("Error", "Selecciona un préstamo activo.")
            return
        id_prestamo = self._prestamos[idx][0]
        if self.controller.backend.registrar_devolucion(id_prestamo):
            messagebox.showinfo(
                "Éxito",
                "Devolución registrada.\n"
                "Stock actualizado automáticamente.\n"
                "Si hubo retraso, la multa fue generada por el sistema."
            )
            self.cmb_loan.set("")
            self.cargar_prestamos()
        else:
            messagebox.showerror("Error", "No se pudo registrar la devolución.")


# ============================================================
# PANTALLA 7: MULTAS
# ============================================================
class FineScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self._multas    = []
        self._prestamos = []

        ttk.Label(self, text="Gestión de Multas",
                  font=('Arial', 18, 'bold')).pack(pady=15)

        # Filtro
        frm_filtro = ttk.Frame(self)
        frm_filtro.pack()

        self.solo_pendientes = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm_filtro, text="Solo pendientes",
                        variable=self.solo_pendientes,
                        command=self.cargar_tabla).pack(side="left", padx=10)
        ttk.Button(frm_filtro, text="↻ Actualizar",
                   command=self.cargar_tabla).pack(side="left", padx=5)

        # Tabla
        frm_tabla = ttk.Frame(self)
        frm_tabla.pack(fill="both", expand=True, padx=20, pady=10)

        cols = ("ID", "Usuario", "Material", "Motivo", "Monto", "Estado", "F. Generada", "F. Pagada")
        self.tree = ttk.Treeview(frm_tabla, columns=cols, show="headings", height=12)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor="center", width=105)
        self.tree.column("Usuario",  width=160)
        self.tree.column("Motivo",   width=150)

        scroll = ttk.Scrollbar(frm_tabla, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.tree.tag_configure("pendiente", background="#ffe0e0")
        self.tree.tag_configure("pagada",    background="#e0ffe0")

        # Botones
        frm_acc = ttk.Frame(self)
        frm_acc.pack(pady=10)
        ttk.Button(frm_acc, text="✔ Marcar como Pagada",
                   command=self.pagar_multa).grid(row=0, column=0, padx=10, ipadx=10, ipady=5)
        ttk.Button(frm_acc, text="+ Agregar Multa Manual",
                   command=self.abrir_form_manual).grid(row=0, column=1, padx=10, ipadx=10, ipady=5)

        ttk.Button(self, text="← Volver al Menú",
                   command=lambda: self.controller.show_frame("MainMenu")
                   ).pack(pady=10, ipadx=10, ipady=5)

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)
        self.cargar_tabla()

    def cargar_tabla(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self._multas = self.controller.backend.obtener_multas(self.solo_pendientes.get())
        for row in self._multas:
            estado = row[5]
            tag    = "pendiente" if estado == "Pendiente" else "pagada"
            vals   = (row[0], row[1], row[2], row[3],
                      f"${row[4]:,.2f}", estado,
                      row[6], row[7] if row[7] else "—")
            self.tree.insert("", "end", values=vals, tags=(tag,))

    def pagar_multa(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atención", "Selecciona una multa de la tabla.")
            return
        vals   = self.tree.item(sel[0])["values"]
        id_multa = vals[0]
        if vals[5] == "Pagada":
            messagebox.showinfo("Info", "Esta multa ya fue pagada.")
            return
        if messagebox.askyesno("Confirmar", f"¿Marcar multa #{id_multa} como pagada?"):
            if self.controller.backend.pagar_multa(id_multa):
                messagebox.showinfo("Éxito", "Multa registrada como pagada.")
                self.cargar_tabla()
            else:
                messagebox.showerror("Error", "No se pudo actualizar.")

    def abrir_form_manual(self):
        self._prestamos = self.controller.backend.obtener_prestamos_para_multa()
        if not self._prestamos:
            messagebox.showinfo("Info", "No hay préstamos devueltos sin multa registrada.")
            return

        win = tk.Toplevel(self)
        win.title("Registrar Multa Manual")
        win.geometry("440x330")
        win.resizable(False, False)
        win.grab_set()

        ttk.Label(win, text="Registrar Multa Manual",
                  font=('Arial', 14, 'bold')).pack(pady=15)

        frm = ttk.Frame(win)
        frm.pack(padx=20)

        ttk.Label(frm, text="Préstamo:").grid(row=0, column=0, sticky="e", pady=8, padx=5)
        cmb_prestamo = ttk.Combobox(frm, state="readonly", width=32,
            values=[f"PR-{r[0]:03d} | {r[1]} — {r[2]}" for r in self._prestamos])
        cmb_prestamo.grid(row=0, column=1, pady=8)

        ttk.Label(frm, text="Motivo:").grid(row=1, column=0, sticky="e", pady=8, padx=5)
        cmb_motivo = ttk.Combobox(frm, width=32,
            values=["Daño al material", "Pérdida del material", "Entrega incompleta", "Otro"])
        cmb_motivo.grid(row=1, column=1, pady=8)

        ttk.Label(frm, text="Monto ($):").grid(row=2, column=0, sticky="e", pady=8, padx=5)
        e_monto = ttk.Entry(frm, width=34)
        e_monto.insert(0, "0.00")
        e_monto.grid(row=2, column=1, pady=8)

        def guardar():
            idx    = cmb_prestamo.current()
            motivo = cmb_motivo.get().strip()
            if idx == -1 or not motivo:
                messagebox.showwarning("Atención", "Completa préstamo y motivo.", parent=win)
                return
            try:
                monto = float(e_monto.get().strip())
            except ValueError:
                messagebox.showerror("Error", "Monto inválido.", parent=win)
                return
            p = self._prestamos[idx]   # (id_prestamo, nombre, material, id_usuario)
            if self.controller.backend.registrar_multa_manual(p[0], p[3], motivo, monto):
                messagebox.showinfo("Éxito", "Multa registrada.", parent=win)
                win.destroy()
                self.cargar_tabla()
            else:
                messagebox.showerror("Error", "No se pudo guardar.", parent=win)

        ttk.Button(win, text="Guardar Multa",
                   command=guardar).pack(pady=20, ipadx=15, ipady=5)


# ============================================================
# PANTALLA 8: REPORTES
# ============================================================
class ReportScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ttk.Label(self, text="Generación de Reportes",
                  font=('Arial', 18, 'bold')).pack(pady=30)

        frm_opts = ttk.Frame(self)
        frm_opts.pack(pady=10)

        self.report_var = tk.StringVar(value="activos")
        opciones = [
            ("Préstamos activos",              "activos"),
            ("Historial de préstamos",         "historial"),
            ("Inventario de materiales",       "inventario"),
            ("Multas",                         "multas"),
            ("Auditoría del sistema",          "auditoria"),
        ]
        for texto, val in opciones:
            ttk.Radiobutton(frm_opts, text=texto,
                            variable=self.report_var, value=val
                            ).pack(anchor="w", pady=6, padx=20)

        frm_btns = ttk.Frame(self)
        frm_btns.pack(pady=25)
        ttk.Button(frm_btns, text="📋 Ver reporte",
                   command=self.generar).grid(row=0, column=0, padx=10, ipadx=10, ipady=5)
        ttk.Button(frm_btns, text="💾 Exportar CSV",
                   command=self.exportar).grid(row=0, column=1, padx=10, ipadx=10, ipady=5)

        ttk.Button(self, text="← Volver al Menú",
                   command=lambda: self.controller.show_frame("MainMenu")
                   ).pack(pady=10, ipadx=10, ipady=5)

    def _obtener_datos(self):
        tipo = self.report_var.get()
        if tipo == "activos":
            datos = self.controller.backend.reporte_prestamos_activos()
            cols  = ("ID", "Usuario", "Material", "F. Préstamo", "F. Vencimiento")
        elif tipo == "historial":
            datos = self.controller.backend.reporte_historial()
            cols  = ("ID", "Usuario", "Material", "F. Préstamo", "F. Devolución", "Estado")
        elif tipo == "inventario":
            datos = self.controller.backend.reporte_inventario()
            cols  = ("Código", "Material", "Total", "Disponible")
        elif tipo == "multas":
            datos = self.controller.backend.reporte_multas()
            cols  = ("ID", "Usuario", "Motivo", "Monto", "Estado", "F. Generada")
        else:
            datos = self.controller.backend.obtener_auditoria()
            cols  = ("ID Evento", "Usuario", "Detalle", "Fecha/Hora")
        return datos, cols, tipo

    def generar(self):
        datos, cols, tipo = self._obtener_datos()

        win = tk.Toplevel(self)
        win.title(f"Reporte: {tipo}")
        win.geometry("900x450")

        tree = ttk.Treeview(win, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor="center",
                        width=max(100, 800 // len(cols)))
        for row in datos:
            tree.insert("", "end", values=row)

        scroll_y = ttk.Scrollbar(win, orient="vertical",   command=tree.yview)
        scroll_x = ttk.Scrollbar(win, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        tree.pack(fill="both", expand=True, padx=10, pady=10)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")

    def exportar(self):
        datos, cols, tipo = self._obtener_datos()
        ruta = fd.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"reporte_{tipo}_{datetime.now().strftime('%Y%m%d')}.csv"
        )
        if ruta:
            with open(ruta, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(cols)
                w.writerows(datos)
            messagebox.showinfo("Éxito", f"Archivo exportado en:\n{ruta}")


# ============================================================
# INICIO
# ============================================================
if __name__ == "__main__":
    app = SGPA_App()
    app.mainloop()
