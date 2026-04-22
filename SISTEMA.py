import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None
    
class BackendControlador:
    def __init__(self):
        self.usuarios_db = []
        self.materiales_db = []
        self.credenciales = {"admin": "1234"}

    def validar_acceso(self, u, p):
        return u in self.credenciales and self.credenciales[u] == p

    def registrar_usuario(self, nombre, ident, grupo):
        self.usuarios_db.append({"id": len(self.usuarios_db)+1, "nombre": nombre, "ident": ident, "grupo": grupo})
        return True

    def registrar_material(self, nombre, codigo, cant, desc):
        self.materiales_db.append({"codigo": codigo, "nombre": nombre, "cant": cant, "desc": desc})
        return True

# Custom styling para la aplicación
def setup_styles():
    style = ttk.Style()
    if 'clam' in style.theme_names():
        style.theme_use('clam')
        
    # Colores definidos
    bg_color = "#E0E0E0"  # Gris Claro
    btn_color = "#0056b3" # Azul
    text_color = "#000000" # Negro
    
    style.configure('.', background=bg_color, foreground=text_color, font=('Arial', 11))
    style.configure('TFrame', background=bg_color)
    style.configure('TLabel', background=bg_color, font=('Arial', 11))
    
    # Botones
    style.configure('TButton', font=('Arial', 11, 'bold'), background=btn_color, foreground='white')
    style.map('TButton', background=[('active', '#004494'), ('pressed', '#003366')])
    
    # Tablas (Treeview)
    style.configure('Treeview', font=('Arial', 10), rowheight=25, background="white", fieldbackground="white")
    style.configure('Treeview.Heading', font=('Arial', 11, 'bold'), background="#cccccc")
    
    # Entradas de texto y listas desplegables
    style.configure('TEntry', fieldbackground="white", padding=5)
    style.configure('TCombobox', fieldbackground="white", padding=5)

class SGPA_App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SGPA - Sistema de Control de Préstamos")
        self.geometry("1024x768")
        self.backend = BackendControlador()
        self.minsize(1024, 768)
        self.configure(bg="#E0E0E0")
        
        setup_styles()
        
        self.frames = {}
        
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        # Inicializar todas las pantallas
        for F in (LoginScreen, MainMenu, UserManagement, MaterialManagement, LoanScreen, ReturnScreen, ReportScreen):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        self.show_frame("LoginScreen")
        
    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

# ---- PANTALLA 1: LOGIN ----
class LoginScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Contenedor central
        inner = ttk.Frame(self)
        inner.place(relx=0.5, rely=0.5, anchor="center")
        
        lbl_title = ttk.Label(inner, text="SGPA - Iniciar Sesión", font=('Arial', 18, 'bold'))
        lbl_title.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        ttk.Label(inner, text="Usuario:").grid(row=1, column=0, sticky="e", pady=10, padx=10)
        self.entry_user = ttk.Entry(inner, width=25)
        self.entry_user.grid(row=1, column=1, pady=10, padx=10)
        
        ttk.Label(inner, text="Contraseña:").grid(row=2, column=0, sticky="e", pady=10, padx=10)
        self.entry_pass = ttk.Entry(inner, show="*", width=25)
        self.entry_pass.grid(row=2, column=1, pady=10, padx=10)
        
        btn_login = ttk.Button(inner, text="Iniciar sesión", command=self.login)
        btn_login.grid(row=3, column=0, columnspan=2, pady=(20,10), ipadx=20, ipady=5)
        
        btn_exit = ttk.Button(inner, text="Salir", command=self.controller.quit)
        btn_exit.grid(row=4, column=0, columnspan=2, ipadx=20, ipady=5)
        
    def login(self):
        user = self.entry_user.get()
        pasw = self.entry_pass.get()
        # Reemplazo de lógica:
        if self.controller.backend.validar_acceso(user, pasw):
            self.controller.show_frame("MainMenu")
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")


# ---- PANTALLA 2: MENÚ PRINCIPAL ----
class MainMenu(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        lbl_title = ttk.Label(self, text="Menú Principal", font=('Arial', 24, 'bold'))
        lbl_title.pack(pady=50)
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack()
        
        buttons = [
            ("Gestión de Usuarios", "UserManagement"),
            ("Gestión de Materiales", "MaterialManagement"),
            ("Préstamos", "LoanScreen"),
            ("Devoluciones", "ReturnScreen"),
            ("Reportes", "ReportScreen")
        ]
        
        for text, frame_name in buttons:
            def create_cmd(f: str):
                return lambda: self.controller.show_frame(f)

            btn = ttk.Button(btn_frame, text=text, command=create_cmd(frame_name))
            btn.pack(fill="x", pady=10, ipadx=50, ipady=10)
            
        btn_logout = ttk.Button(btn_frame, text="Salir", command=lambda: self.controller.show_frame("LoginScreen"))
        btn_logout.pack(fill="x", pady=30, ipadx=50, ipady=10)


# ---- PANTALLA 3: GESTIÓN DE USUARIOS ----
class UserManagement(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        lbl_title = ttk.Label(self, text="Gestión de Usuarios", font=('Arial', 18, 'bold'))
        lbl_title.pack(pady=20)
        
        content = ttk.Frame(self)
        content.pack(fill="both", expand=True, padx=20, pady=10)
        
        # --- Formulario (Izquierda) ---
        frm_left = ttk.Frame(content)
        frm_left.pack(side="left", fill="y", padx=20)
        
        ttk.Label(frm_left, text="ID Usuario:").grid(row=0, column=0, sticky="e", pady=5)
        self.e_id = ttk.Entry(frm_left, state="disabled") # Automático
        self.e_id.grid(row=0, column=1, pady=5, sticky="w")
        
        ttk.Label(frm_left, text="Nombre completo:").grid(row=1, column=0, sticky="e", pady=5)
        self.e_name = ttk.Entry(frm_left, width=30)
        self.e_name.grid(row=1, column=1, pady=5, sticky="w")
        
        ttk.Label(frm_left, text="Número de identificación:").grid(row=2, column=0, sticky="e", pady=5)
        self.e_ident = ttk.Entry(frm_left, width=30)
        self.e_ident.grid(row=2, column=1, pady=5, sticky="w")
        
        ttk.Label(frm_left, text="Grupo:").grid(row=3, column=0, sticky="e", pady=5)
        self.cmb_group = ttk.Combobox(frm_left, values=["Estudiante", "Docente", "Administrativo", "Mantenimiento"], state="readonly")
        self.cmb_group.grid(row=3, column=1, pady=5, sticky="w")
        
        ttk.Label(frm_left, text="Fecha registro:").grid(row=4, column=0, sticky="e", pady=5)
        self.e_date = ttk.Entry(frm_left, state="normal")
        self.e_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.e_date.configure(state="disabled") # Automática
        self.e_date.grid(row=4, column=1, pady=5, sticky="w")
        
        # Botones de acción
        frm_btns = ttk.Frame(frm_left)
        frm_btns.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(frm_btns, text="Registrar", command=self.registrar_usuario).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(frm_btns, text="Modificar").grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frm_btns, text="Eliminar", command=self.eliminar).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(frm_btns, text="Buscar").grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(frm_btns, text="Limpiar", command=self.limpiar).grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        ttk.Button(frm_left, text="Volver al Menú", command=lambda: self.controller.show_frame("MainMenu")).grid(row=6, column=0, columnspan=2, pady=30)
        
        # --- Tabla (Derecha) ---
        frm_right = ttk.Frame(content)
        frm_right.pack(side="right", fill="both", expand=True)
        
        cols = ("ID", "Nombre", "Identificación", "Grupo")
        self.tree = ttk.Treeview(frm_right, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor="center")
        self.tree.pack(fill="both", expand=True)
        
    def registrar_usuario(self):
        nom = self.e_name.get()
        ide = self.e_ident.get()
        grp = self.cmb_group.get()
        if nom and ide and grp:
            self.controller.backend.registrar_usuario(nom, ide, grp)
            messagebox.showinfo("Éxito", "Usuario guardado en el Back-end")
            self.actualizar_tabla()
        else:
            messagebox.showwarning("Error", "Completa todos los campos")

    def actualizar_tabla(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for u in self.controller.backend.usuarios_db:
            self.tree.insert("", "end", values=(u["id"], u["nombre"], u["ident"], u["grupo"]))
        
    def registrar(self):
        messagebox.showinfo("Registro Exitoso", "El usuario ha sido registrado correctamente.")
        
    def eliminar(self):
        respuesta = messagebox.askyesno("Confirmación", "¿Está seguro de eliminar este usuario?")
        if respuesta:
            messagebox.showinfo("Eliminación Confirmada", "El usuario ha sido eliminado correctamente.")
            
    def limpiar(self):
        self.e_name.delete(0, tk.END)
        self.e_ident.delete(0, tk.END)
        self.cmb_group.set("")


# ---- PANTALLA 4: GESTIÓN DE MATERIALES ----
class MaterialManagement(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        lbl_title = ttk.Label(self, text="Gestión de Materiales", font=('Arial', 18, 'bold'))
        lbl_title.pack(pady=20)
        
        content = ttk.Frame(self)
        content.pack(fill="both", expand=True, padx=20, pady=10)
        
        frm_left = ttk.Frame(content)
        frm_left.pack(side="left", fill="y", padx=20)
        
        ttk.Label(frm_left, text="ID Material:").grid(row=0, column=0, sticky="e", pady=5)
        self.e_id = ttk.Entry(frm_left, state="disabled") # Automático
        self.e_id.grid(row=0, column=1, pady=5, sticky="w")
        
        ttk.Label(frm_left, text="Nombre material:").grid(row=1, column=0, sticky="e", pady=5)
        self.e_name = ttk.Entry(frm_left, width=30)
        self.e_name.grid(row=1, column=1, pady=5, sticky="w")
        
        ttk.Label(frm_left, text="Código material:").grid(row=2, column=0, sticky="e", pady=5)
        self.e_code = ttk.Entry(frm_left, width=30)
        self.e_code.grid(row=2, column=1, pady=5, sticky="w")
        
        ttk.Label(frm_left, text="Cantidad:").grid(row=3, column=0, sticky="e", pady=5)
        # Se requiere Spinbox
        self.spin_qty = tk.Spinbox(frm_left, from_=0, to=1000, width=10, font=('Arial', 11))
        self.spin_qty.grid(row=3, column=1, pady=5, sticky="w")
        
        ttk.Label(frm_left, text="Descripción:").grid(row=4, column=0, sticky="ne", pady=5)
        # Se requiere TextBox (tk.Text)
        self.txt_desc = tk.Text(frm_left, width=30, height=4, font=('Arial', 10))
        self.txt_desc.grid(row=4, column=1, pady=5, sticky="w")
        
        frm_btns = ttk.Frame(frm_left)
        frm_btns.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(frm_btns, text="Registrar", command=self.registrar).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(frm_btns, text="Modificar").grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frm_btns, text="Eliminar", command=self.eliminar).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(frm_btns, text="Buscar").grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(frm_btns, text="Limpiar", command=self.limpiar).grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        ttk.Button(frm_left, text="Volver al Menú", command=lambda: self.controller.show_frame("MainMenu")).grid(row=6, column=0, columnspan=2, pady=20)
        
        frm_right = ttk.Frame(content)
        frm_right.pack(side="right", fill="both", expand=True)
        
        # Tabla y columnas
        cols = ("Código", "Nombre", "Cantidad")
        self.tree = ttk.Treeview(frm_right, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor="center")
        self.tree.pack(fill="both", expand=True)
        
    def registrar_material(self):
        nom = self.e_m_name.get()
        cod = self.e_m_code.get()
        qty = self.spin_qty.get()
        if nom and cod:
            self.controller.backend.registrar_material(nom, cod, qty, "Sin desc")
            messagebox.showinfo("Back-end", "Material registrado")
            self.actualizar_tabla_mat()

    def actualizar_tabla_mat(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for m in self.controller.backend.materiales_db:
            self.tree.insert("", "end", values=(m["codigo"], m["nombre"], m["cant"], m["cant"]))

    def registrar(self):
        messagebox.showinfo("Registro Exitoso", "Material registrado correctamente.")
        
    def eliminar(self):
        if messagebox.askyesno("Confirmación", "¿Está seguro de eliminar este material?"):
            messagebox.showinfo("Eliminación Confirmada", "Material eliminado.")
            
    def limpiar(self):
        self.e_name.delete(0, tk.END)
        self.e_code.delete(0, tk.END)
        self.spin_qty.delete(0, "end")
        self.spin_qty.insert(0, "0")
        self.txt_desc.delete("1.0", tk.END)

# ---- PANTALLA 5: PRÉSTAMOS ----
class LoanScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        lbl_title = ttk.Label(self, text="Registro de Préstamos", font=('Arial', 18, 'bold'))
        lbl_title.pack(pady=30)
        
        frm_form = ttk.Frame(self)
        frm_form.pack(pady=10)
        
        ttk.Label(frm_form, text="Usuario:").grid(row=0, column=0, sticky="e", pady=10, padx=10)
        self.cmb_user = ttk.Combobox(frm_form, values=["Usuario 1 (12345)", "Usuario 2 (67890)"], state="readonly", width=30)
        self.cmb_user.grid(row=0, column=1, pady=10, padx=10)
        
        ttk.Label(frm_form, text="Material:").grid(row=1, column=0, sticky="e", pady=10, padx=10)
        self.cmb_material = ttk.Combobox(frm_form, values=["Calculadora (Disp: 5)", "Proyector (Disp: 0)"], state="readonly", width=30)
        self.cmb_material.grid(row=1, column=1, pady=10, padx=10)
        
        ttk.Label(frm_form, text="Fecha préstamo:").grid(row=2, column=0, sticky="e", pady=10, padx=10)
        self.e_date_loan = ttk.Entry(frm_form, state="normal", width=33)
        self.e_date_loan.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.e_date_loan.configure(state="disabled") # Automática
        self.e_date_loan.grid(row=2, column=1, pady=10, padx=10)
        
        ttk.Label(frm_form, text="Fecha devolución:").grid(row=3, column=0, sticky="e", pady=10, padx=10)
        
        # Uso de tkcalendar si está disponible (Selector de fecha interactivo)
        if DateEntry:
            self.date_return = DateEntry(frm_form, width=30, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
            self.date_return.grid(row=3, column=1, pady=10, padx=10)
        else:
            self.date_return = ttk.Entry(frm_form, width=33)
            self.date_return.insert(0, "YYYY-MM-DD")
            self.date_return.grid(row=3, column=1, pady=10, padx=10)
            
        frm_btns = ttk.Frame(frm_form)
        frm_btns.grid(row=4, column=0, columnspan=2, pady=40)
        
        ttk.Button(frm_btns, text="Registrar Préstamo", command=self.registrar).grid(row=0, column=0, padx=10, ipadx=10, ipady=5)
        ttk.Button(frm_btns, text="Cancelar", command=lambda: self.controller.show_frame("MainMenu")).grid(row=0, column=1, padx=10, ipadx=10, ipady=5)

    def registrar(self):
        material = self.cmb_material.get()
        if not material:
            messagebox.showerror("Error de Datos", "Seleccione un material válido.")
            return
            
        # Validación de disponibilidad
        if "Disp: 0" in material:
            messagebox.showerror("Error de Disponibilidad", "No hay unidades disponibles de este material para el préstamo.")
        else:
            messagebox.showinfo("Préstamo Registrado", "El préstamo se ha registrado de forma exitosa.")


# ---- PANTALLA 6: DEVOLUCIONES ----
class ReturnScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        lbl_title = ttk.Label(self, text="Registro de Devoluciones", font=('Arial', 18, 'bold'))
        lbl_title.pack(pady=40)
        
        frm_form = ttk.Frame(self)
        frm_form.pack(pady=10)
        
        ttk.Label(frm_form, text="ID Préstamo:").grid(row=0, column=0, sticky="e", pady=10, padx=10)
        self.cmb_loan = ttk.Combobox(frm_form, values=["PR-001 (Juan Pérez)", "PR-002 (María Gómez)"], state="readonly", width=30)
        self.cmb_loan.grid(row=0, column=1, pady=10, padx=10)
        
        ttk.Label(frm_form, text="Fecha devolución real:").grid(row=1, column=0, sticky="e", pady=10, padx=10)
        self.e_date_return = ttk.Entry(frm_form, state="normal", width=33)
        self.e_date_return.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.e_date_return.configure(state="disabled") # Automática
        self.e_date_return.grid(row=1, column=1, pady=10, padx=10)
        
        frm_btns = ttk.Frame(frm_form)
        frm_btns.grid(row=2, column=0, columnspan=2, pady=40)
        
        ttk.Button(frm_btns, text="Registrar Devolución", command=self.registrar).grid(row=0, column=0, padx=10, ipadx=10, ipady=5)
        ttk.Button(frm_btns, text="Cancelar", command=lambda: self.controller.show_frame("MainMenu")).grid(row=0, column=1, padx=10, ipadx=10, ipady=5)

    def registrar(self):
        if not self.cmb_loan.get():
            messagebox.showerror("Error en datos", "Seleccione un préstamo para procesar la devolución.")
        else:
            messagebox.showinfo("Devolución Registrada", "La devolución se ha registrado correctamente en el sistema.")


# ---- PANTALLA 7: REPORTES ----
class ReportScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        lbl_title = ttk.Label(self, text="Generación de Reportes", font=('Arial', 18, 'bold'))
        lbl_title.pack(pady=40)
        
        frm_opts = ttk.Frame(self)
        frm_opts.pack(pady=20)
        
        self.report_var = tk.StringVar(value="activos")
        
        ttk.Radiobutton(frm_opts, text="Reporte de préstamos activos", variable=self.report_var, value="activos").grid(row=0, column=0, sticky="w", pady=10)
        ttk.Radiobutton(frm_opts, text="Reporte de historial (Préstamos y devoluciones)", variable=self.report_var, value="historial").grid(row=1, column=0, sticky="w", pady=10)
        ttk.Radiobutton(frm_opts, text="Reporte de materiales disponibles", variable=self.report_var, value="inventario").grid(row=2, column=0, sticky="w", pady=10)
        
        frm_btns = ttk.Frame(self)
        frm_btns.pack(pady=40)
        
        ttk.Button(frm_btns, text="Generar PDF", command=self.generar).grid(row=0, column=0, padx=10, ipadx=10, ipady=5)
        ttk.Button(frm_btns, text="Exportar a Excel/CSV", command=self.exportar).grid(row=0, column=1, padx=10, ipadx=10, ipady=5)
        
        ttk.Button(self, text="Volver al Menú", command=lambda: self.controller.show_frame("MainMenu")).pack(pady=20, ipadx=10, ipady=5)
        
    def generar(self):
        messagebox.showinfo("Reporte Generado", f"El archivo PDF para el reporte '{self.report_var.get()}' ha sido generado.")
        
    def exportar(self):
        messagebox.showinfo("Exportación Exitosa", f"Los datos del reporte '{self.report_var.get()}' han sido exportados correctamente.")


# Inicialización de la App
if __name__ == "__main__":
    app = SGPA_App()
    app.mainloop()
