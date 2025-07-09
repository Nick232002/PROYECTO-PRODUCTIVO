import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from sqlite3 import Error
import csv
from fpdf import FPDF
from datetime import datetime

# ----------------------------
# Configuración de la Base de Datos
# ----------------------------
def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('inventario.db')
        return conn
    except Error as e:
        print(e)
    return conn

def create_tables(conn):
    sql_scripts = [
        """CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        );""",
        """CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            stock INTEGER NOT NULL,
            categoria_id INTEGER,
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        );""",
        """CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER,
            tipo TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            fecha TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        );"""
    ]
    
    try:
        c = conn.cursor()
        for script in sql_scripts:
            c.execute(script)
        conn.commit()
    except Error as e:
        print(e)

# ----------------------------
# Clase para el PDF
# ----------------------------
class PDF(FPDF):
    def __init__(self):
        super().__init__(orientation='L')  # 'L' para landscape (horizontal)
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Reporte de Inventario', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

# ----------------------------
# Aplicación Principal
# ----------------------------
class InventarioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SOFTWARE INVENTORY")
        self.root.geometry("1200x700")
        self.root.minsize(1000, 600)
        
        # Configurar tema oscuro
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configurar colores
        self.bg_color = '#333333'
        self.fg_color = '#ffffff'
        self.primary_color = '#2c3e50'
        self.secondary_color = '#3498db'
        self.success_color = '#27ae60'
        self.danger_color = '#e74c3c'
        self.warning_color = '#f39c12'
        
        # Configurar estilos
        self.configure_styles()
        
        self.setup_ui()
        self.init_db()
    
    def configure_styles(self):
        """Configura los estilos para los widgets"""
        # Frame principal
        self.style.configure('Main.TFrame', background=self.bg_color)
        
        # Labels
        self.style.configure('TLabel', 
                           background=self.bg_color, 
                           foreground=self.fg_color,
                           font=('Arial', 10))
        
        # Botones
        self.style.configure('TButton', 
                           font=('Arial', 10, 'bold'),
                           padding=5,
                           relief='flat')
        
        self.style.map('TButton',
                     foreground=[('active', self.fg_color), ('!active', self.fg_color)],
                     background=[('active', self.secondary_color), ('!active', self.primary_color)])
        
        # Botones de éxito (verde)
        self.style.configure('Success.TButton', 
                           background=self.success_color,
                           foreground=self.fg_color)
        
        # Botones de peligro (rojo)
        self.style.configure('Danger.TButton', 
                           background=self.danger_color,
                           foreground=self.fg_color)
        
        # Botones de advertencia (naranja)
        self.style.configure('Warning.TButton', 
                           background=self.warning_color,
                           foreground=self.fg_color)
        
        # Treeview
        self.style.configure('Treeview', 
                           background='#f8f9fa',
                           foreground='#333333',
                           rowheight=25,
                           fieldbackground='#f8f9fa')
        
        self.style.configure('Treeview.Heading', 
                           background=self.primary_color,
                           foreground=self.fg_color,
                           font=('Arial', 10, 'bold'))
        
        self.style.map('Treeview', 
                     background=[('selected', self.secondary_color)],
                     foreground=[('selected', self.fg_color)])
        
        # Entry y Combobox
        self.style.configure('TEntry', 
                           fieldbackground='#ffffff',
                           foreground='#333333')
        
        self.style.configure('TCombobox', 
                           fieldbackground='#ffffff',
                           foreground='#333333')
        
        # Notebook (pestañas)
        self.style.configure('TNotebook', background=self.bg_color)
        self.style.configure('TNotebook.Tab', 
                           background=self.primary_color,
                           foreground=self.fg_color,
                           padding=[10, 5],
                           font=('Arial', 10, 'bold'))
        
        self.style.map('TNotebook.Tab', 
                     background=[('selected', self.secondary_color)],
                     foreground=[('selected', self.fg_color)])
    
    def init_db(self):
        conn = create_connection()
        if conn:
            create_tables(conn)
            conn.close()
    
    def setup_ui(self):
        # Frame principal
        self.main_frame = ttk.Frame(self.root, style='Main.TFrame')
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Barra de menú
        self.setup_menu()
        
        # Configurar notebook (pestañas)
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pestaña de Productos
        self.product_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.product_frame, text="📦 Productos")
        self.setup_product_tab()
        
        # Pestaña de Categorías
        self.category_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.category_frame, text="🗂 Categorías")
        self.setup_category_tab()
        
        # Pestaña de Movimientos
        self.movement_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.movement_frame, text="🔄 Movimientos")
        self.setup_movement_tab()
        
        # Barra de estado
        self.status_bar = ttk.Label(self.main_frame, 
                                   text="SOFTWARE INVENTORY - © 2025", 
                                   relief=tk.SUNKEN,
                                   anchor=tk.W,
                                   style='TLabel')
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, ipady=5)
        
        # Cargar datos iniciales
        self.load_categories()
        self.load_categories_combobox()
        self.load_products()
        self.load_movements()
    
    def setup_menu(self):
        self.menubar = tk.Menu(self.root)
        
        # Menú Archivo
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="Exportar a CSV", command=self.export_to_csv)
        file_menu.add_command(label="Exportar a PDF", command=self.export_to_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)
        self.menubar.add_cascade(label="Archivo", menu=file_menu)
        
        # Menú Ayuda
        help_menu = tk.Menu(self.menubar, tearoff=0)
        help_menu.add_command(label="Acerca de", command=self.show_about)
        self.menubar.add_cascade(label="Ayuda", menu=help_menu)
        
        self.root.config(menu=self.menubar)
    
    def show_about(self):
        about_text = "Sofware Inventory\n\n" \
                    "Versión 0.1\n" \
                    "© 2025 - Todos los derechos reservados\n\n" \
                    "Desarrollado como proyecto productivo sena"
        messagebox.showinfo("Acerca de", about_text)
    
    def setup_product_tab(self):
        # Frame principal con paneles divididos
        main_panel = ttk.PanedWindow(self.product_frame, orient=tk.HORIZONTAL)
        main_panel.pack(fill=tk.BOTH, expand=True)
        
        # Panel izquierdo (formulario)
        left_panel = ttk.Frame(main_panel)
        main_panel.add(left_panel, weight=1)
        
        # Panel derecho (lista de productos)
        right_panel = ttk.Frame(main_panel)
        main_panel.add(right_panel, weight=3)
        
        # Formulario de productos
        form_frame = ttk.LabelFrame(left_panel, text="Formulario de Producto", padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        fields = ["Código", "Nombre", "Precio", "Stock", "Categoría"]
        for i, field in enumerate(fields):
            ttk.Label(form_frame, text=f"{field}:").grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.codigo_entry = ttk.Entry(form_frame)
        self.nombre_entry = ttk.Entry(form_frame)
        self.precio_entry = ttk.Entry(form_frame)
        self.stock_entry = ttk.Entry(form_frame)
        self.categoria_combobox = ttk.Combobox(form_frame)
        
        self.codigo_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.nombre_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        self.precio_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.EW)
        self.stock_entry.grid(row=3, column=1, padx=5, pady=5, sticky=tk.EW)
        self.categoria_combobox.grid(row=4, column=1, padx=5, pady=5, sticky=tk.EW)
        
        # Botones de acción
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Agregar", command=self.add_product, style='Success.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Editar", command=self.edit_product, style='Warning.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Eliminar", command=self.delete_product, style='Danger.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Limpiar", command=self.clear_product_form).pack(side=tk.LEFT, padx=5)
        
        # Treeview de productos
        list_frame = ttk.LabelFrame(right_panel, text="Lista de Productos", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.product_tree = ttk.Treeview(
            list_frame,
            columns=("codigo", "nombre", "precio", "stock", "categoria", "fecha"),
            show="headings"
        )
        
        headers = ["Código", "Nombre", "Precio", "Stock", "Categoría", "Fecha Creación"]
        for i, header in enumerate(headers):
            self.product_tree.heading(f"#{i+1}", text=header)
            self.product_tree.column(f"#{i+1}", width=100, anchor=tk.CENTER)
        
        self.product_tree.column("#1", width=120)  # Código
        self.product_tree.column("#2", width=200)  # Nombre
        self.product_tree.column("#6", width=120)  # Fecha
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.product_tree.yview)
        self.product_tree.configure(yscroll=scrollbar.set)
        
        self.product_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.product_tree.bind("<Double-1>", self.on_product_double_click)
        
        # Barra de búsqueda
        search_frame = ttk.Frame(right_panel)
        search_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Label(search_frame, text="Buscar:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(search_frame, text="Buscar", command=self.search_products).pack(side=tk.LEFT, padx=5)
    
    def setup_category_tab(self):
        # Frame principal con paneles divididos
        main_panel = ttk.PanedWindow(self.category_frame, orient=tk.HORIZONTAL)
        main_panel.pack(fill=tk.BOTH, expand=True)
        
        # Panel izquierdo (formulario)
        left_panel = ttk.Frame(main_panel)
        main_panel.add(left_panel, weight=1)
        
        # Panel derecho (lista de categorías)
        right_panel = ttk.Frame(main_panel)
        main_panel.add(right_panel, weight=3)
        
        # Formulario de categorías
        form_frame = ttk.LabelFrame(left_panel, text="Formulario de Categoría", padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Nombre:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.category_entry = ttk.Entry(form_frame)
        self.category_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        
        # Botones de acción
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Agregar", command=self.add_category, style='Success.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Editar", command=self.edit_category, style='Warning.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Eliminar", command=self.delete_category, style='Danger.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Limpiar", command=self.clear_category_form).pack(side=tk.LEFT, padx=5)
        
        # Treeview de categorías
        list_frame = ttk.LabelFrame(right_panel, text="Lista de Categorías", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.category_tree = ttk.Treeview(
            list_frame,
            columns=("nombre",),
            show="headings"
        )
        
        self.category_tree.heading("#1", text="Nombre")
        self.category_tree.column("#1", width=300)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.category_tree.yview)
        self.category_tree.configure(yscroll=scrollbar.set)
        
        self.category_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.category_tree.bind("<Double-1>", self.on_category_double_click)
    
    def setup_movement_tab(self):
        # Frame principal
        main_frame = ttk.Frame(self.movement_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Filtros
        filter_frame = ttk.LabelFrame(main_frame, text="Filtros", padding=10)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Tipo:").pack(side=tk.LEFT, padx=5)
        
        self.movement_filter = ttk.Combobox(filter_frame, values=["Todos", "Entradas", "Salidas"])
        self.movement_filter.pack(side=tk.LEFT, padx=5)
        self.movement_filter.set("Todos")
        
        ttk.Button(filter_frame, text="Aplicar", command=self.load_movements).pack(side=tk.LEFT, padx=5)
        
        # Treeview de movimientos
        list_frame = ttk.LabelFrame(main_frame, text="Historial de Movimientos", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.movement_tree = ttk.Treeview(
            list_frame,
            columns=("producto", "tipo", "cantidad", "fecha"),
            show="headings"
        )
        
        headers = ["Producto", "Tipo", "Cantidad", "Fecha"]
        for i, header in enumerate(headers):
            self.movement_tree.heading(f"#{i+1}", text=header)
            self.movement_tree.column(f"#{i+1}", width=100, anchor=tk.CENTER)
        
        self.movement_tree.column("#1", width=200)  # Producto
        self.movement_tree.column("#4", width=150)  # Fecha
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.movement_tree.yview)
        self.movement_tree.configure(yscroll=scrollbar.set)
        
        self.movement_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def search_products(self):
        """Busca productos según el texto ingresado"""
        search_term = self.search_entry.get().strip()
        if not search_term:
            self.load_products()
            return
        
        conn = create_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.id, p.codigo, p.nombre, p.precio, p.stock, 
                           c.nombre, p.fecha_creacion
                    FROM productos p
                    LEFT JOIN categorias c ON p.categoria_id = c.id
                    WHERE p.codigo LIKE ? OR p.nombre LIKE ? OR c.nombre LIKE ?
                    ORDER BY p.nombre
                """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
                
                productos = cursor.fetchall()
                self.product_tree.delete(*self.product_tree.get_children())
                
                for producto in productos:
                    self.product_tree.insert("", tk.END, values=producto[1:], iid=producto[0])
                    
            except Error as e:
                messagebox.showerror("Error", f"No se pudo realizar la búsqueda: {e}")
            finally:
                conn.close()
    
    def export_to_csv(self):
        items = self.product_tree.get_children()
        if not items:
            messagebox.showwarning("Advertencia", "No hay datos para exportar")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")],
            title="Guardar como"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                headers = []
                for col in self.product_tree["columns"]:
                    headers.append(self.product_tree.heading(col)["text"])
                writer.writerow(headers)
                
                for item in items:
                    row = self.product_tree.item(item)["values"]
                    writer.writerow(row)
                    
            messagebox.showinfo("Éxito", f"Datos exportados correctamente a:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar el archivo:\n{str(e)}")

    def export_to_pdf(self):
        items = self.product_tree.get_children()
        if not items:
            messagebox.showwarning("Advertencia", "No hay datos para exportar")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")],
            title="Guardar como"
        )
        
        if not file_path:
            return
        
        try:
            pdf = PDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Encabezado con logo (simulado)
            pdf.cell(200, 10, txt="Reporte de Inventario - SENA", ln=1, align='C')
            pdf.ln(10)
            
            # Fecha de generación
            pdf.set_font("Times New", size=10)
            pdf.cell(0, 10, txt=f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=1, align='R')
            pdf.ln(5)
            
            # Tabla de productos
            pdf.set_font("Arial", size=10)
            
            headers = []
            for col in self.product_tree["columns"]:
                headers.append(self.product_tree.heading(col)["text"])
            
            # Ajustar anchos de columna
            col_widths = [30, 60, 20, 20, 30, 30]
            
            # Encabezados de la tabla
            pdf.set_fill_color(44, 62, 80)  # Color primario
            pdf.set_text_color(255, 255, 255)  # Texto blanco
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 10, txt=header, border=1, fill=True)
            pdf.ln()
            
            # Contenido de la tabla
            pdf.set_fill_color(255, 255, 255)  # Fondo blanco
            pdf.set_text_color(0, 0, 0)  # Texto negro
            
            for item in items:
                row = self.product_tree.item(item)["values"]
                for i, value in enumerate(row):
                    pdf.cell(col_widths[i], 10, txt=str(value), border=1)
                pdf.ln()
            
            # Pie de página
            pdf.ln(10)
            pdf.set_font("Arial", 'I', 8)
            pdf.cell(0, 10, txt="Sistema de Inventario SENA - © 2023", ln=1, align='C')
            
            pdf.output(file_path)
            messagebox.showinfo("Éxito", f"Reporte PDF generado correctamente en:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n{str(e)}")

    def add_product(self):
        """Agrega un nuevo producto a la base de datos"""
        codigo = self.codigo_entry.get().strip()
        nombre = self.nombre_entry.get().strip()
        precio = self.precio_entry.get().strip()
        stock = self.stock_entry.get().strip()
        categoria = self.categoria_combobox.get().strip()

        # Validaciones
        if not all([codigo, nombre, precio, stock, categoria]):
            messagebox.showwarning("Advertencia", "Todos los campos son obligatorios")
            return

        try:
            precio = float(precio)
            stock = int(stock)
        except ValueError:
            messagebox.showwarning("Advertencia", "Precio y stock deben ser números válidos")
            return

        conn = create_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Obtener ID de la categoría
                cursor.execute("SELECT id FROM categorias WHERE nombre = ?", (categoria,))
                categoria_id = cursor.fetchone()
                if not categoria_id:
                    messagebox.showwarning("Advertencia", "Categoría no válida")
                    return
                categoria_id = categoria_id[0]

                # Verificar si el código ya existe
                cursor.execute("SELECT * FROM productos WHERE codigo = ?", (codigo,))
                if cursor.fetchone():
                    messagebox.showwarning("Advertencia", "El código de producto ya existe")
                    return

                # Insertar nuevo producto
                cursor.execute(
                    "INSERT INTO productos (codigo, nombre, precio, stock, categoria_id) VALUES (?, ?, ?, ?, ?)",
                    (codigo, nombre, precio, stock, categoria_id)
                )
                
                # Registrar movimiento
                cursor.execute(
                    "INSERT INTO movimientos (producto_id, tipo, cantidad) VALUES (?, ?, ?)",
                    (cursor.lastrowid, 'entrada', stock)
                )
                
                conn.commit()
                messagebox.showinfo("Éxito", "Producto agregado correctamente")
                self.clear_product_form()
                self.load_products()
                
            except Error as e:
                messagebox.showerror("Error", f"No se pudo agregar el producto: {e}")
            finally:
                conn.close()

    def edit_product(self):
        """Edita un producto existente"""
        selected_item = self.product_tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Debe seleccionar un producto")
            return

        # Obtener datos del formulario
        codigo = self.codigo_entry.get().strip()
        nombre = self.nombre_entry.get().strip()
        precio = self.precio_entry.get().strip()
        stock = self.stock_entry.get().strip()
        categoria = self.categoria_combobox.get().strip()

        # Validaciones
        if not all([codigo, nombre, precio, stock, categoria]):
            messagebox.showwarning("Advertencia", "Todos los campos son obligatorios")
            return

        try:
            precio = float(precio)
            stock = int(stock)
        except ValueError:
            messagebox.showwarning("Advertencia", "Precio y stock deben ser números válidos")
            return

        conn = create_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Obtener ID de la categoría
                cursor.execute("SELECT id FROM categorias WHERE nombre = ?", (categoria,))
                categoria_id = cursor.fetchone()
                if not categoria_id:
                    messagebox.showwarning("Advertencia", "Categoría no válida")
                    return
                categoria_id = categoria_id[0]

                # Obtener ID del producto (usando el iid del Treeview)
                producto_id = selected_item[0]
                
                # Obtener datos actuales del producto
                cursor.execute("SELECT stock FROM productos WHERE id = ?", (producto_id,))
                stock_actual = cursor.fetchone()[0]
                diferencia = stock - stock_actual

                # Actualizar producto
                cursor.execute(
                "INSERT INTO movimientos (producto_id, tipo, cantidad) VALUES (?, ?, ?)",
                 (producto_id, tipo, abs(diferencia))
                )
                
                # Registrar movimiento si hay cambio en el stock
                if diferencia != 0:
                    tipo = 'entrada' if diferencia > 0 else 'salida'
                    cursor.execute(
                        "INSERT INTO movimientos (producto_id, tipo, cantidad) VALUES (?, ?, ?)",
                        (producto_id, tipo, abs(diferencia))
                    )
                conn.commit()
                messagebox.showinfo("Éxito", "Producto actualizado correctamente")
                self.load_products()
                
            except Error as e:
                messagebox.showerror("Error", f"No se pudo actualizar el producto: {e}")
            finally:
                conn.close()

    def delete_product(self):
        """Elimina un producto de la base de datos"""
        selected_item = self.product_tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Debe seleccionar un producto")
            return

        if not messagebox.askyesno("Confirmar", "¿Está seguro que desea eliminar este producto?"):
            return

        producto_id = selected_item[0]  # Obtenemos el ID del iid del Treeview

        conn = create_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Primero eliminar movimientos relacionados
                cursor.execute("DELETE FROM movimientos WHERE producto_id = ?", (producto_id,))
                
                # Luego eliminar el producto
                cursor.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
                
                conn.commit()
                messagebox.showinfo("Éxito", "Producto eliminado correctamente")
                self.clear_product_form()
                self.load_products()
                
            except Error as e:
                messagebox.showerror("Error", f"No se pudo eliminar el producto: {e}")
            finally:
                conn.close()

    def clear_product_form(self):
        """Limpia el formulario de productos"""
        self.codigo_entry.delete(0, tk.END)
        self.nombre_entry.delete(0, tk.END)
        self.precio_entry.delete(0, tk.END)
        self.stock_entry.delete(0, tk.END)
        self.categoria_combobox.set('')

    def on_product_double_click(self, event):
        """Carga los datos del producto seleccionado en el formulario"""
        selected_item = self.product_tree.selection()
        if not selected_item:
            return

        item_data = self.product_tree.item(selected_item)['values']
        self.clear_product_form()
        
        self.codigo_entry.insert(0, item_data[0])  # código
        self.nombre_entry.insert(0, item_data[1])  # nombre
        self.precio_entry.insert(0, item_data[2])  # precio
        self.stock_entry.insert(0, item_data[3])   # stock
        self.categoria_combobox.set(item_data[4])  # categoría

    def add_category(self): 
        """Agrega una nueva categoría a la base de datos"""
        nombre = self.category_entry.get().strip()
        if not nombre:
            messagebox.showwarning("Advertencia", "Debe ingresar un nombre para la categoría")
            return
        
        conn = create_connection()
        if conn:
            try:
                cursor = conn.cursor()
                # Verificar si la categoría ya existe
                cursor.execute("SELECT * FROM categorias WHERE nombre = ?", (nombre,))
                if cursor.fetchone():
                    messagebox.showwarning("Advertencia", "Esta categoría ya existe")
                    return
                
                # Insertar nueva categoría
                cursor.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))
                conn.commit()
                
                messagebox.showinfo("Éxito", "Categoría agregada correctamente")
                self.clear_category_form()
                self.load_categories()
                self.load_categories_combobox()
                
            except Error as e:
                messagebox.showerror("Error", f"No se pudo agregar la categoría: {e}")
            finally:
                conn.close()

    def edit_category(self):
        """Edita una categoría existente"""
        selected_item = self.category_tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Debe seleccionar una categoría")
            return

        nuevo_nombre = self.category_entry.get().strip()
        if not nuevo_nombre:
            messagebox.showwarning("Advertencia", "Debe ingresar un nombre para la categoría")
            return

        categoria_id = selected_item[0]  # Obtenemos el ID del iid del Treeview
        nombre_actual = self.category_tree.item(selected_item)['values'][0]

        if nuevo_nombre == nombre_actual:
            return

        conn = create_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Verificar si el nuevo nombre ya existe
                cursor.execute("SELECT * FROM categorias WHERE nombre = ? AND id != ?", (nuevo_nombre, categoria_id))
                if cursor.fetchone():
                    messagebox.showwarning("Advertencia", "Ya existe una categoría con ese nombre")
                    return
                
                # Actualizar categoría
                cursor.execute("UPDATE categorias SET nombre = ? WHERE id = ?", (nuevo_nombre, categoria_id))
                conn.commit()
                
                messagebox.showinfo("Éxito", "Categoría actualizada correctamente")
                self.clear_category_form()
                self.load_categories()
                self.load_categories_combobox()
                
            except Error as e:
                messagebox.showerror("Error", f"No se pudo actualizar la categoría: {e}")
            finally:
                conn.close()

    def delete_category(self):
        """Elimina una categoría de la base de datos"""
        selected_item = self.category_tree.selection()
        if not selected_item:
            messagebox.showwarning("Advertencia", "Debe seleccionar una categoría")
            return

        if not messagebox.askyesno("Confirmar", "¿Está seguro que desea eliminar esta categoría? Los productos asociados quedarán sin categoría."):
            return

        categoria_id = selected_item[0]  # Obtenemos el ID del iid del Treeview

        conn = create_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Primero actualizar productos que usan esta categoría
                cursor.execute("UPDATE productos SET categoria_id = NULL WHERE categoria_id = ?", (categoria_id,))
                
                # Luego eliminar la categoría
                cursor.execute("DELETE FROM categorias WHERE id = ?", (categoria_id,))
                
                conn.commit()
                messagebox.showinfo("Éxito", "Categoría eliminada correctamente")
                self.clear_category_form()
                self.load_categories()
                self.load_categories_combobox()
                self.load_products()  # Actualizar lista de productos
                
            except Error as e:
                messagebox.showerror("Error", f"No se pudo eliminar la categoría: {e}")
            finally:
                conn.close()

    def clear_category_form(self):
        """Limpia el formulario de categorías"""
        self.category_entry.delete(0, tk.END)

    def on_category_double_click(self, event):
        """Carga los datos de la categoría seleccionada en el formulario"""
        selected_item = self.category_tree.selection()
        if not selected_item:
            return

        item_data = self.category_tree.item(selected_item)['values']
        self.clear_category_form()
        self.category_entry.insert(0, item_data[0])  # nombre

    def load_movements(self):
        """Carga los movimientos desde la base de datos al TreeView"""
        self.movement_tree.delete(*self.movement_tree.get_children())
        
        filtro = self.movement_filter.get()
        
        conn = create_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                query = """
                    SELECT m.id, p.nombre, m.tipo, m.cantidad, m.fecha
                    FROM movimientos m
                    JOIN productos p ON m.producto_id = p.id
                """
                
                if filtro != "Todos":
                    query += " WHERE m.tipo = ?"
                    cursor.execute(query, (filtro.lower(),))
                else:
                    cursor.execute(query)
                    
                movimientos = cursor.fetchall()
                
                for mov in movimientos:
                    # Insertamos solo los datos visibles (sin el ID)
                    self.movement_tree.insert("", tk.END, values=mov[1:], iid=mov[0])
                    
            except Error as e:
                messagebox.showerror("Error", f"No se pudieron cargar los movimientos: {e}")
            finally:
                conn.close()

    def load_categories(self):
        """Carga las categorías desde la base de datos al TreeView"""
        self.category_tree.delete(*self.category_tree.get_children())
        
        conn = create_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id, nombre FROM categorias ORDER BY nombre")
                categorias = cursor.fetchall()
                
                for categoria in categorias:
                    # Insertamos solo el nombre pero usamos el ID como iid
                    self.category_tree.insert("", tk.END, values=(categoria[1],), iid=categoria[0])
                    
            except Error as e:
                messagebox.showerror("Error", f"No se pudieron cargar las categorías: {e}")
            finally:
                conn.close()

    def load_products(self):
        """Carga los productos desde la base de datos al TreeView"""
        self.product_tree.delete(*self.product_tree.get_children())
        
        conn = create_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.id, p.codigo, p.nombre, p.precio, p.stock, 
                           c.nombre, p.fecha_creacion
                    FROM productos p
                    LEFT JOIN categorias c ON p.categoria_id = c.id
                    ORDER BY p.nombre
                """)
                productos = cursor.fetchall()
                
                for producto in productos:
                    # Insertamos todos los campos excepto el ID (usamos el ID como iid)
                    self.product_tree.insert("", tk.END, values=producto[1:], iid=producto[0])
                    
            except Error as e:
                messagebox.showerror("Error", f"No se pudieron cargar los productos: {e}")
            finally:
                conn.close()

    def load_categories_combobox(self):
        """Carga las categorías en el combobox de productos"""
        conn = create_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT nombre FROM categorias ORDER BY nombre")
                categorias = [row[0] for row in cursor.fetchall()]
                self.categoria_combobox['values'] = categorias
                
            except Error as e:
                messagebox.showerror("Error", f"No se pudieron cargar las categorías: {e}")
            finally:
                conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = InventarioApp(root)
    root.mainloop()