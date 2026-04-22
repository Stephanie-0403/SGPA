import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os

DB_NAME = "sistema_prestamos.db"

class SistemaPrestamosApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Control de Préstamos - Gestor Local")
        
        # Tamaño inicial de la ventana
        self.root.geometry("850x550")
        self.root.minsize(800, 500)
        
        # Estilo para ventanas y marcos (Tema más moderno)
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TFrame", background="#f4f6f9")
        self.style.configure("TLabel", background="#f4f6f9", font=("Segoe UI", 11))
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#2c3e50")
        
        self.root.configure(bg="#f4f6f9", padx=20, pady=20)
        
        self.create_widgets()
        
        # Verificar si la base de datos existe para advertir al usuario
        if not os.path.exists(DB_NAME):
            messagebox.showwarning(
                "Base de Datos no encontrada", 
                "⚠️ No se ha generado la base de datos aún.\n\n"
                "Asegúrate de ejecutar el archivo 'test.py' al menos una vez para inicializar las tablas."
            )
        else:
            self.cargar_alertas()

    def conectar_bd(self):
        """Abre la conexión con la base de datos SQLite."""
        return sqlite3.connect(DB_NAME)

    def create_widgets(self):
        """Configura y dibuja los componentes de la interfaz de usuario en pantalla."""
        # 1. Título principal
        lbl_titulo = ttk.Label(self.root, text="📢 Panel Principal: Monitoreo de Préstamos", style="Header.TLabel")
        lbl_titulo.pack(pady=(0, 15), anchor="w")

        # Layout principal de frames
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        # 2. Frame superior para acciones rápidas
        top_frame = ttk.LabelFrame(self.main_frame, text=" Acciones del Sistema ", padding=10)
        top_frame.pack(fill="x", pady=(0, 15))

        btn_test_db = ttk.Button(top_frame, text="🔌 Probar Conexión a BD", command=self.probar_conexion)
        btn_test_db.pack(side="left", padx=5)

        btn_refresh = ttk.Button(top_frame, text="🔄 Actualizar Alertas", command=self.cargar_alertas)
        btn_refresh.pack(side="left", padx=5)
        
        # Etiqueta de estado a la derecha
        self.lbl_estado = ttk.Label(top_frame, text="Estado: Esperando conexión...", foreground="#7f8c8d")
        self.lbl_estado.pack(side="right", padx=10)

        # 3. Frame para el Treeview (Tabla) de Alertas Vencidas
        alertas_frame = ttk.LabelFrame(self.main_frame, text=" ⚠️ Préstamos Vencidos (Alertas Automáticas) ", padding=10)
        alertas_frame.pack(fill="both", expand=True)

        # Configurar Columnas
        columnas = ("id_detalle", "usuario", "recurso", "fecha_limite", "dias_demora")
        self.tree = ttk.Treeview(alertas_frame, columns=columnas, show="headings", height=15)
        
        # Scrollbar vertical para manejar muchos registros
        scrollbar = ttk.Scrollbar(alertas_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Nombrar y dimensionar Encabezados
        self.tree.heading("id_detalle", text="ID / Ticket")
        self.tree.column("id_detalle", width=80, anchor="center")
        
        self.tree.heading("usuario", text="Usuario (Matrícula - Nombre)")
        self.tree.column("usuario", width=220)
        
        self.tree.heading("recurso", text="Recurso (SN - Nombre)")
        self.tree.column("recurso", width=250)
        
        self.tree.heading("fecha_limite", text="Fecha Límite")
        self.tree.column("fecha_limite", width=120, anchor="center")
        
        self.tree.heading("dias_demora", text="Demora (Días)")
        self.tree.column("dias_demora", width=100, anchor="center")

    def probar_conexion(self):
        """Verifica la conexión a la base de datos consultando tablas requeridas."""
        if not os.path.exists(DB_NAME):
            self.lbl_estado.config(text="Estado: ⚠️ BD no encontrada")
            messagebox.showerror("Error", "No existe la base de datos. Ejecuta 'test.py' primero.")
            return

        try:
            conexion = self.conectar_bd()
            cursor = conexion.cursor()
            
            # Consultas de prueba rápidas
            cursor.execute("SELECT count(*) FROM Usuarios")
            usuarios_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT count(*) FROM Recursos")
            recursos_count = cursor.fetchone()[0]
            
            conexion.close()
            
            # Notificar éxito
            self.lbl_estado.config(text="Estado: ✅ Conectado", foreground="#27ae60")
            messagebox.showinfo(
                "Test de Conexión", 
                f"✅ Conexión establecida a la base de datos de forma exitosa.\n\n"
                f"Estadísticas básicas encontradas:\n"
                f"👥 Usuarios registrados: {usuarios_count}\n"
                f"💻 Recursos en inventario: {recursos_count}"
            )
        except sqlite3.Error as e:
            self.lbl_estado.config(text="Estado: ❌ Error de lectura", foreground="#c0392b")
            messagebox.showerror("Error de base de datos", f"No se pudo leer la estructura:\n{e}")

    def cargar_alertas(self):
        """Consulta la vista optimizada de base de datos y dibuja las filas de morosos."""
        if not os.path.exists(DB_NAME):
            return

        # 1. Limpiar registros viejos de la tabla UI
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            conexion = self.conectar_bd()
            cursor = conexion.cursor()
            
            # 2. Consultar la Vista pre-compilada en SQLite filtrada por 'Vencido'
            query = """
                SELECT id_detalle, 
                       matricula_usuario || ' - ' || nombre_usuario AS usr, 
                       numero_serie || ' - ' || recurso AS rec, 
                       fecha_limite, 
                       dias_retraso
                FROM v_alertas_prestamos
                WHERE estado_tiempo = 'Vencido'
                ORDER BY dias_retraso DESC
            """
            cursor.execute(query)
            filas_vencidas = cursor.fetchall()
            
            # 3. Renderizar cada fila detectada
            for index, fila in enumerate(filas_vencidas):
                tags = ('oddrow',) if index % 2 == 0 else ('evenrow',)
                self.tree.insert("", "end", values=fila, tags=tags)
                
            # Dar estilo alternado a las filas (opcional, por estética)
            self.tree.tag_configure('oddrow', background="#ffffff")
            self.tree.tag_configure('evenrow', background="#f4f6f9")
            
            # Notificar en la etiqueta
            self.lbl_estado.config(text=f"Estado: ✅ Alertas cargadas ({len(filas_vencidas)} vencidos)", foreground="#27ae60")
            conexion.close()
            
        except sqlite3.Error as e:
            self.lbl_estado.config(text="Estado: ⚠️ Error consultando alertas", foreground="#e67e22")
            print(f"Error técnico leyendo alertas: {e}")

if __name__ == "__main__":
    # Arrancar la aplicación Tkinter
    root = tk.Tk()
    app = SistemaPrestamosApp(root)
    root.mainloop()
