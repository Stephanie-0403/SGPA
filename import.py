import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None


# SECCIÓN: BACKEND CONTROLADOR 

class BackendControlador:
    def __init__(self):
        # Datos iniciales simulados 
        self.usuarios_db = [
            {"id": 1, "nombre": "Administrador Global", "ident": "ADMIN-01", "grupo": "Administrativo"}
        ]
        self.materiales_db = [
            {"codigo": "LPT-001", "nombre": "Laptop Dell", "cantidad": 5, "disponible": 5, "desc": "Equipo de oficina"}
        ]
        # Credenciales de prueba
        self.credenciales = {
            "admin": "1234"
        }

    def validar_acceso(self, usuario, password):
        if usuario in self.credenciales and self.credenciales[usuario] == password:
            return True
        return False

    def registrar_usuario_db(self, nombre, ident, grupo):
        nuevo_id = len(self.usuarios_db) + 1
        self.usuarios_db.append({
            "id": nuevo_id,
            "nombre": nombre,
            "ident": ident,
            "grupo": grupo
        })
        return True

    def registrar_material_db(self, nombre, codigo, cantidad, desc):
        self.materiales_db.append({
            "codigo": codigo,
            "nombre": nombre,
            "cantidad": cantidad,
            "disponible": cantidad,
            "desc": desc
        })
        return True

# SECCIÓN: INTERFAZ GRÁFICA 

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
    style.configure('TCombobox', fieldbackground="white", selectbackground=btn_color)

class SGPA_App(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("SGPA - Sistema de Control de Préstamos")
        self.geometry("1024x768")
        
        # INICIALIZACIÓN DEL BACKEND
        self.backend = BackendControlador()
        
        setup_styles()
        
        self.container = ttk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        for F in (LoginScreen, MainMenu, UserManagement, MaterialManagement, LoanScreen, ReturnScreen, ReportScreen):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        self.show_frame("LoginScreen")
        
    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        # Si la pantalla tiene método de actualizar datos al entrar, se llama aquí
        if hasattr(frame, "actualizar_datos"):
            frame.actualizar_datos()

class LoginScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Contenedor centrado
        login_frame = ttk.Frame(self)
        login_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ttk.Label(login_frame, text="SGPA - Sistema de Control de Préstamos", font=('Arial', 18, 'bold')).grid(row=0, column=0, columnspan=2, pady=20)
        
        ttk.Label(login_frame, text="Usuario:").grid(row=1, column=0, sticky="e", pady=10, padx=5)
        self.entry_user = ttk.Entry(login_frame, width=30)
        self.entry_user.grid(row=1, column=1, pady=10, padx=5)
        
        ttk.Label(login_frame, text="Contraseña:").grid(row=2, column=0, sticky="e", pady=10, padx=5)
        self.entry_pass = ttk.Entry(login_frame, show="*", width=30)
        self.entry_pass.grid(row=2, column=1, pady=10, padx=5)
        
        btn_frame = ttk.Frame(login_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="Iniciar sesión", command=self.login).grid(row=0, column=0, padx=10, ipadx=10, ipady=5)
        ttk.Button(btn_frame, text="Salir", command=self.quit).grid(row=0, column=1, padx=10, ipadx=10, ipady=5)
        
    def login(self):
        user = self.entry_user.get()
        password = self.entry_pass.get()
        
        # LLAMADA AL BACKEND
        if self.controller.backend.validar_acceso(user, password):
            self.controller.show_frame("MainMenu")
            self.entry_user.delete(0, tk.END)
            self.entry_pass.delete(0, tk.END)
        else:
            messagebox.showerror("Error de autenticación", "Usuario o contraseña incorrectos.")

class MainMenu(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        ttk.Label(self, text="Menú Principal", font=('Arial', 24, 'bold')).pack(pady=50)
        
        btn_container = ttk.Frame(self)
        btn_container.pack()
        
        menu_items = [
            ("Gestión de Usuarios", "UserManagement"),
            ("Gestión de Materiales", "MaterialManagement"),
            ("Préstamos", "LoanScreen"),
            ("Devoluciones", "ReturnScreen"),
            ("Reportes", "ReportScreen")
        ]
        
        for text, target in menu_items:
            ttk.Button(btn_container, text=text, command=lambda t=target: self.controller.show_frame(t)).pack(fill="x", pady=10, ipadx=80, ipady=10)
            
        ttk.Button(self, text="Cerrar Sesión", command=lambda: self.controller.show_frame("LoginScreen")).pack(pady=40, ipadx=10, ipady=5)

class UserManagement(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        ttk.Label(self, text="Gestión de Usuarios", font=('Arial', 20, 'bold')).pack(pady=20)
        
        # Formulario
        form_frame = ttk.Frame(self)
        form_frame.pack(pady=10)
        
        ttk.Label(form_frame, text="Nombre completo:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.e_name = ttk.Entry(form_frame, width=40)
        self.e_name.grid(row=0, column=1, pady=5)
        
        ttk.Label(form_frame, text="N° Identificación:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.e_ident = ttk.Entry(form_frame, width=40)
        self.e_ident.grid(row=1, column=1, pady=5)
        
        ttk.Label(form_frame, text="Grupo/Categoría:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.cmb_group = ttk.Combobox(form_frame, values=["Estudiante", "Docente", "Administrativo", "Mantenimiento"], state="readonly", width=37)
        self.cmb_group.grid(row=2, column=1, pady=5)
        
        # Botones de acción
        btn_action_frame = ttk.Frame(self)
        btn_action_frame.pack(pady=20)
        
        ttk.Button(btn_action_frame, text="Registrar", command=self.registrar).grid(row=0, column=0, padx=10, ipadx=10)
        ttk.Button(btn_action_frame, text="Modificar", command=lambda: None).grid(row=0, column=1, padx=10, ipadx=10)
        ttk.Button(btn_action_frame, text="Eliminar", command=lambda: None).grid(row=0, column=2, padx=10, ipadx=10)
        ttk.Button(btn_action_frame, text="Limpiar", command=self.limpiar).grid(row=0, column=3, padx=10, ipadx=10)
        
        # Tabla
        cols = ("ID", "Nombre", "Identificación", "Grupo")
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=8)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.pack(fill="both", expand=True, padx=30, pady=10)
        
        ttk.Button(self, text="Volver al Menú", command=lambda: self.controller.show_frame("MainMenu")).pack(pady=20, ipadx=10, ipady=5)

    def actualizar_datos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for u in self.controller.backend.usuarios_db:
            self.tree.insert("", "end", values=(u["id"], u["nombre"], u["ident"], u["grupo"]))

    def registrar(self):
        nombre = self.e_name.get()
        ident = self.e_ident.get()
        grupo = self.cmb_group.get()
        
        if nombre and ident and grupo:
            self.controller.backend.registrar_usuario_db(nombre, ident, grupo)
            messagebox.showinfo("Éxito", f"Usuario {nombre} registrado correctamente.")
            self.actualizar_datos()
            self.limpiar()
        else:
            messagebox.showwarning("Atención", "Por favor complete todos los campos.")

    def limpiar(self):
        self.e_name.delete(0, tk.END)
        self.e_ident.delete(0, tk.END)
        self.cmb_group.set('')

class MaterialManagement(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        ttk.Label(self, text="Gestión de Materiales", font=('Arial', 20, 'bold')).pack(pady=20)
        
        form_frame = ttk.Frame(self)
        form_frame.pack(pady=10)
        
        ttk.Label(form_frame, text="Nombre del Material:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.e_m_name = ttk.Entry(form_frame, width=40); self.e_m_name.grid(row=0, column=1, pady=5)
        
        ttk.Label(form_frame, text="Código/Serial:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.e_m_code = ttk.Entry(form_frame, width=40); self.e_m_code.grid(row=1, column=1, pady=5)
        
        ttk.Label(form_frame, text="Cantidad Total:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.spin_qty = tk.Spinbox(form_frame, from_=1, to=1000, width=38); self.spin_qty.grid(row=2, column=1, pady=5)
        
        ttk.Label(form_frame, text="Descripción:").grid(row=3, column=0, sticky="nw", padx=10, pady=5)
        self.txt_desc = tk.Text(form_frame, width=30, height=3); self.txt_desc.grid(row=3, column=1, pady=5)
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="Registrar Material", command=self.registrar).grid(row=0, column=0, padx=10, ipadx=10)
        ttk.Button(btn_frame, text="Limpiar", command=self.limpiar).grid(row=0, column=1, padx=10, ipadx=10)
        
        cols = ("Código", "Nombre", "Total", "Disponible")
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=8)
        for col in cols:
            self.tree.heading(col, text=col)
        self.tree.pack(fill="both", expand=True, padx=30, pady=10)
        
        ttk.Button(self, text="Volver al Menú", command=lambda: self.controller.show_frame("MainMenu")).pack(pady=10)

    def actualizar_datos(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for m in self.controller.backend.materiales_db:
            self.tree.insert("", "end", values=(m["codigo"], m["nombre"], m["cantidad"], m["disponible"]))

    def registrar(self):
        nombre = self.e_m_name.get()
        codigo = self.e_m_code.get()
        qty = self.spin_qty.get()
        desc = self.txt_desc.get("1.0", tk.END).strip()
        
        if nombre and codigo:
            self.controller.backend.registrar_material_db(nombre, codigo, int(qty), desc)
            messagebox.showinfo("Éxito", "Material registrado en inventario.")
            self.actualizar_datos()
            self.limpiar()
        else:
            messagebox.showwarning("Faltan datos", "Nombre y Código son obligatorios.")

    def limpiar(self):
        self.e_m_name.delete(0, tk.END)
        self.e_m_code.delete(0, tk.END)
        self.txt_desc.delete("1.0", tk.END)

class LoanScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        ttk.Label(self, text="Préstamos", font=('Arial', 20, 'bold')).pack(pady=20)
        
        loan_frame = ttk.Frame(self)
        loan_frame.pack(pady=20)
        
        ttk.Label(loan_frame, text="Seleccionar Usuario:").grid(row=0, column=0, pady=10, sticky="e")
        self.cmb_u = ttk.Combobox(loan_frame, width=40); self.cmb_u.grid(row=0, column=1, padx=10)
        
        ttk.Label(loan_frame, text="Seleccionar Material:").grid(row=1, column=0, pady=10, sticky="e")
        self.cmb_m = ttk.Combobox(loan_frame, width=40); self.cmb_m.grid(row=1, column=1, padx=10)
        
        ttk.Label(loan_frame, text="Fecha de Devolución:").grid(row=2, column=0, pady=10, sticky="e")
        if DateEntry:
            self.cal = DateEntry(loan_frame, width=37, background='darkblue', foreground='white', borderwidth=2)
            self.cal.grid(row=2, column=1, padx=10)
        else:
            self.e_date = ttk.Entry(loan_frame, width=40); self.e_date.grid(row=2, column=1, padx=10)
            
        ttk.Button(self, text="Registrar Préstamo", command=lambda: messagebox.showinfo("Préstamo", "Registro exitoso.")).pack(pady=30, ipadx=20, ipady=10)
        ttk.Button(self, text="Volver al Menú", command=lambda: self.controller.show_frame("MainMenu")).pack()

    def actualizar_datos(self):
        self.cmb_u['values'] = [u["nombre"] for u in self.controller.backend.usuarios_db]
        self.cmb_m['values'] = [m["nombre"] for m in self.controller.backend.materiales_db]

class ReturnScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        ttk.Label(self, text="Devoluciones", font=('Arial', 20, 'bold')).pack(pady=20)
        
        return_frame = ttk.Frame(self)
        return_frame.pack(pady=30)
        
        ttk.Label(return_frame, text="ID de Préstamo Activo:").grid(row=0, column=0, padx=10)
        self.cmb_p = ttk.Combobox(return_frame, values=["P-001", "P-002", "P-003"], width=45)
        self.cmb_p.grid(row=0, column=1, padx=10)
        
        ttk.Button(self, text="Registrar Devolución", command=lambda: messagebox.showinfo("Devolución", "Material devuelto al inventario.")).pack(pady=40, ipadx=20, ipady=10)
        ttk.Button(self, text="Volver al Menú", command=lambda: self.controller.show_frame("MainMenu")).pack()

class ReportScreen(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        ttk.Label(self, text="Reportes", font=('Arial', 20, 'bold')).pack(pady=20)
        
        frm_opts = ttk.Frame(self)
        frm_opts.pack(pady=20)
        
        self.report_var = tk.StringVar(value="activos")
        
        ttk.Radiobutton(frm_opts, text="Reporte de préstamos activos", variable=self.report_var, value="activos").grid(row=0, column=0, sticky="w", pady=10)
        ttk.Radiobutton(frm_opts, text="Reporte de historial (Préstamos y devoluciones)", variable=self.report_var, value="historial").grid(row=1, column=0, sticky="w", pady=10)
        ttk.Radiobutton(frm_opts, text="Reporte de materiales disponibles", variable=self.report_var, value="inventario").grid(row=2, column=0, sticky="w", pady=10)
        
        frm_btns = ttk.Frame(self)
        frm_btns.pack(pady=40)
        
        ttk.Button(frm_btns, text="Generar PDF", command=lambda: messagebox.showinfo("Reporte", "Generando PDF...")).grid(row=0, column=0, padx=10, ipadx=10, ipady=5)
        ttk.Button(frm_btns, text="Exportar a Excel/CSV", command=lambda: messagebox.showinfo("Exportar", "Archivo guardado.")).grid(row=0, column=1, padx=10, ipadx=10, ipady=5)
        
        ttk.Button(self, text="Volver al Menú", command=lambda: self.controller.show_frame("MainMenu")).pack(pady=20, ipadx=10, ipady=5)

if __name__ == "__main__":
    app = SGPA_App()
    app.mainloop()
