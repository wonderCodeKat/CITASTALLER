# TALLER AUTOMOTRIZ - GOOGLE COLAB VERSION
# Ejecutar cada celda en orden

# ===== CELDA 1: INSTALACIÓN DE DEPENDENCIAS =====
!pip install streamlit pyngrok sqlite3 pandas plotly folium streamlit-folium -q

# ===== CELDA 2: CONFIGURACIÓN DE ARCHIVOS =====
import os
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, date, timedelta
import json

# Crear directorio para la aplicación
os.makedirs('/content/taller_app', exist_ok=True)
os.chdir('/content/taller_app')

# ===== CELDA 3: CÓDIGO PRINCIPAL DE LA APLICACIÓN =====
app_code = '''
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
import hashlib
import folium
from streamlit_folium import st_folium
import plotly.express as px
from typing import Dict, List, Optional, Tuple
import os

# Configuración de la página
st.set_page_config(
    page_title="Taller AutoMax",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

class DatabaseManager:
    def __init__(self, db_path="taller.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Obtiene conexión a la base de datos SQLite"""
        try:
            return sqlite3.connect(self.db_path)
        except Exception as e:
            st.error(f"Error conectando a la base de datos: {e}")
            return None
    
    def execute_query(self, query: str, params: tuple = None):
        """Ejecuta una consulta SQL"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                result = [dict(row) for row in cursor.fetchall()]
            else:
                result = cursor.lastrowid
                conn.commit()
            
            return result
        except Exception as e:
            st.error(f"Error ejecutando consulta: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def init_database(self):
        """Inicializa la base de datos con tablas y datos"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            # Crear tablas
            cursor.executescript("""
            -- Tabla de usuarios/administradores
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                rol TEXT DEFAULT 'admin',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Tabla de clientes
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                telefono TEXT,
                email TEXT,
                direccion TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Tabla de vehículos
            CREATE TABLE IF NOT EXISTS vehiculos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER REFERENCES clientes(id),
                marca TEXT NOT NULL,
                modelo TEXT NOT NULL,
                año INTEGER,
                placa TEXT UNIQUE,
                color TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Tabla de servicios
            CREATE TABLE IF NOT EXISTS servicios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                precio REAL NOT NULL,
                duracion_minutos INTEGER DEFAULT 60,
                activo BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Tabla de citas
            CREATE TABLE IF NOT EXISTS citas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER REFERENCES clientes(id),
                vehiculo_id INTEGER REFERENCES vehiculos(id),
                servicio_id INTEGER REFERENCES servicios(id),
                fecha_cita DATE NOT NULL,
                hora_cita TEXT NOT NULL,
                estado TEXT DEFAULT 'pendiente',
                observaciones TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Tabla de inventario
            CREATE TABLE IF NOT EXISTS inventario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                cantidad_actual INTEGER DEFAULT 0,
                cantidad_minima INTEGER DEFAULT 5,
                precio_unitario REAL,
                categoria TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            
            # Insertar datos iniciales si no existen
            # Usuario admin (password: admin123)
            cursor.execute("""
            INSERT OR IGNORE INTO usuarios (username, password_hash) 
            VALUES ('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9')
            """)
            
            # Servicios iniciales
            servicios_data = [
                ('Cambio de Aceite', 'Cambio de aceite y filtro de motor', 45.00, 30),
                ('Revisión General', 'Diagnóstico completo del vehículo', 80.00, 60),
                ('Cambio de Frenos', 'Cambio de pastillas y discos de freno', 120.00, 90),
                ('Alineación y Balanceo', 'Alineación de ruedas y balanceo', 35.00, 45),
                ('Cambio de Batería', 'Instalación de batería nueva', 25.00, 20),
                ('Reparación de Motor', 'Reparación y mantenimiento de motor', 200.00, 240)
            ]
            
            cursor.executemany("""
            INSERT OR IGNORE INTO servicios (nombre, descripcion, precio, duracion_minutos) 
            VALUES (?, ?, ?, ?)
            """, servicios_data)
            
            # Items de inventario
            inventario_data = [
                ('Aceite 5W-30', 'Aceite para motor sintético', 20, 5, 35.00, 'Lubricantes'),
                ('Filtro de Aceite', 'Filtro de aceite universal', 15, 3, 8.50, 'Filtros'),
                ('Pastillas de Freno', 'Pastillas de freno cerámicas', 8, 2, 45.00, 'Frenos'),
                ('Batería 12V', 'Batería de automóvil 12V', 5, 2, 85.00, 'Eléctrico'),
                ('Llantas 185/65R15', 'Llantas para automóvil', 12, 4, 120.00, 'Llantas')
            ]
            
            cursor.executemany("""
            INSERT OR IGNORE INTO inventario (nombre, descripcion, cantidad_actual, cantidad_minima, precio_unitario, categoria) 
            VALUES (?, ?, ?, ?, ?, ?)
            """, inventario_data)
            
            conn.commit()
            return True
            
        except Exception as e:
            st.error(f"Error inicializando base de datos: {e}")
            return False
        finally:
            conn.close()

# Inicializar gestor de base de datos
@st.cache_resource
def get_database():
    return DatabaseManager()

db = get_database()

def hash_password(password: str) -> str:
    """Genera hash SHA-256 de la contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username: str, password: str) -> bool:
    """Autentica usuario"""
    password_hash = hash_password(password)
    result = db.execute_query(
        "SELECT id FROM usuarios WHERE username = ? AND password_hash = ?",
        (username, password_hash)
    )
    return len(result) > 0 if result else False

def show_home_page():
    """Página de inicio"""
    st.title("🔧 Taller AutoMax")
    st.markdown("### *Tu taller de confianza para el cuidado de tu vehículo*")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## Bienvenido a Taller AutoMax
        
        Somos un taller especializado en el mantenimiento y reparación de vehículos con más de 15 años de experiencia. 
        Nuestro equipo de técnicos certificados está comprometido con brindarte el mejor servicio para mantener tu vehículo 
        en óptimas condiciones.
        
        ### 🌟 Nuestros Servicios
        - Mantenimiento preventivo y correctivo
        - Cambio de aceite y filtros
        - Sistema de frenos
        - Alineación y balanceo
        - Diagnóstico computarizado
        - Reparación de motor
        """)
    
    with col2:
        st.markdown("### 📅 Horarios de Atención")
        st.info("""
        **Lunes a Viernes:**  
        8:00 AM - 6:00 PM
        
        **Sábados:**  
        8:00 AM - 2:00 PM
        
        **Domingos:**  
        Cerrado
        """)
        
        st.markdown("### 📞 Contacto")
        st.info("""
        **Teléfono:**  
        (01) 234-5678
        
        **Email:**  
        info@tallerautomax.com
        """)
    
    # Mapa de ubicación
    st.markdown("### 📍 Nuestra Ubicación")
    
    # Coordenadas de San Isidro, Lima
    lat, lon = -12.0931, -77.0465
    
    m = folium.Map(location=[lat, lon], zoom_start=15)
    folium.Marker(
        [lat, lon],
        popup="Taller AutoMax<br>Av. Principal 123, San Isidro",
        tooltip="Taller AutoMax",
        icon=folium.Icon(color='red', icon='wrench', prefix='fa')
    ).add_to(m)
    
    st_folium(m, width=700, height=300)
    
    # Botón para agendar cita
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("📅 Agendar Cita", type="primary", use_container_width=True):
            st.session_state.current_page = "citas"
            st.rerun()

def show_services_page():
    """Página de servicios"""
    st.title("🛠️ Nuestros Servicios")
    
    servicios = db.execute_query(
        "SELECT nombre, descripcion, precio, duracion_minutos FROM servicios WHERE activo = 1 ORDER BY precio"
    )
    
    if servicios:
        for servicio in servicios:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{servicio['nombre']}**")
                    st.caption(servicio['descripcion'])
                
                with col2:
                    st.metric("Precio", f"S/ {servicio['precio']:.2f}")
                
                with col3:
                    st.metric("Duración", f"{servicio['duracion_minutos']} min")
                
                st.markdown("---")
    else:
        st.warning("No se pudieron cargar los servicios.")

def show_appointments_page():
    """Página de citas"""
    st.title("📅 Gestión de Citas")
    
    tab1, tab2, tab3 = st.tabs(["Agendar Cita", "Mis Citas", "Consultar Cita"])
    
    with tab1:
        st.subheader("Agendar Nueva Cita")
        
        with st.form("nueva_cita"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Datos del Cliente**")
                nombre_cliente = st.text_input("Nombre Completo*")
                telefono = st.text_input("Teléfono*")
                email = st.text_input("Email")
                direccion = st.text_area("Dirección")
            
            with col2:
                st.markdown("**Datos del Vehículo**")
                marca = st.text_input("Marca*")
                modelo = st.text_input("Modelo*")
                año = st.number_input("Año", min_value=1990, max_value=2024, value=2020)
                placa = st.text_input("Placa*")
                color = st.text_input("Color")
            
            st.markdown("**Detalles de la Cita**")
            
            servicios = db.execute_query("SELECT id, nombre, precio FROM servicios WHERE activo = 1 ORDER BY nombre")
            if servicios:
                servicio_options = {f"{s['nombre']} - S/ {s['precio']:.2f}": s['id'] for s in servicios}
                servicio_seleccionado = st.selectbox("Servicio*", options=list(servicio_options.keys()))
                servicio_id = servicio_options[servicio_seleccionado]
            else:
                st.error("No hay servicios disponibles")
                servicio_id = None
            
            col3, col4 = st.columns(2)
            with col3:
                fecha_cita = st.date_input("Fecha de la Cita*", min_value=date.today())
            with col4:
                horarios = [f"{h:02d}:{m:02d}" for h in range(8, 18) for m in [0, 30]]
                hora_cita = st.selectbox("Hora de la Cita*", options=horarios)
            
            observaciones = st.text_area("Observaciones")
            
            submitted = st.form_submit_button("Agendar Cita", type="primary")
            
            if submitted:
                if not all([nombre_cliente, telefono, marca, modelo, placa]) or not servicio_id:
                    st.error("Por favor completa todos los campos obligatorios (*)")
                else:
                    try:
                        # Verificar disponibilidad
                        cita_existente = db.execute_query(
                            "SELECT id FROM citas WHERE fecha_cita = ? AND hora_cita = ? AND estado != 'cancelada'",
                            (str(fecha_cita), hora_cita)
                        )
                        
                        if cita_existente:
                            st.error("El horario seleccionado ya está ocupado.")
                        else:
                            # Crear cliente
                            cliente_id = db.execute_query(
                                "INSERT INTO clientes (nombre, telefono, email, direccion) VALUES (?, ?, ?, ?)",
                                (nombre_cliente, telefono, email, direccion)
                            )
                            
                            # Crear vehículo
                            vehiculo_id = db.execute_query(
                                "INSERT INTO vehiculos (cliente_id, marca, modelo, año, placa, color) VALUES (?, ?, ?, ?, ?, ?)",
                                (cliente_id, marca, modelo, año, placa, color)
                            )
                            
                            # Crear cita
                            cita_id = db.execute_query(
                                "INSERT INTO citas (cliente_id, vehiculo_id, servicio_id, fecha_cita, hora_cita, observaciones) VALUES (?, ?, ?, ?, ?, ?)",
                                (cliente_id, vehiculo_id, servicio_id, str(fecha_cita), hora_cita, observaciones)
                            )
                            
                            st.success(f"¡Cita agendada exitosamente! Número de cita: {cita_id}")
                            
                    except Exception as e:
                        if "UNIQUE constraint failed" in str(e):
                            st.error("La placa del vehículo ya está registrada.")
                        else:
                            st.error(f"Error al agendar la cita: {e}")
    
    with tab2:
        st.subheader("Consultar Citas por Teléfono")
        
        telefono_buscar = st.text_input("Ingresa tu número de teléfono:")
        
        if telefono_buscar:
            citas = db.execute_query("""
                SELECT 
                    c.id, c.fecha_cita, c.hora_cita, c.estado, c.observaciones,
                    cl.nombre as cliente_nombre, cl.telefono as cliente_telefono,
                    v.marca || ' ' || v.modelo || ' (' || v.placa || ')' as vehiculo_info,
                    s.nombre as servicio_nombre, s.precio as servicio_precio, s.duracion_minutos
                FROM citas c
                JOIN clientes cl ON c.cliente_id = cl.id
                JOIN vehiculos v ON c.vehiculo_id = v.id
                JOIN servicios s ON c.servicio_id = s.id
                WHERE cl.telefono LIKE ?
                ORDER BY c.fecha_cita DESC, c.hora_cita
            """, (f"%{telefono_buscar}%",))
            
            if citas:
                for cita in citas:
                    with st.expander(f"Cita #{cita['id']} - {cita['fecha_cita']} {cita['hora_cita']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Cliente:** {cita['cliente_nombre']}")
                            st.write(f"**Vehículo:** {cita['vehiculo_info']}")
                            st.write(f"**Servicio:** {cita['servicio_nombre']}")
                        
                        with col2:
                            st.write(f"**Estado:** {cita['estado'].title()}")
                            st.write(f"**Precio:** S/ {cita['servicio_precio']:.2f}")
                            st.write(f"**Duración:** {cita['duracion_minutos']} min")
                        
                        if cita['observaciones']:
                            st.write(f"**Observaciones:** {cita['observaciones']}")
                        
                        if cita['estado'] == 'pendiente':
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                if st.button(f"Confirmar #{cita['id']}", type="primary"):
                                    db.execute_query("UPDATE citas SET estado = 'confirmada' WHERE id = ?", (cita['id'],))
                                    st.success("Cita confirmada")
                                    st.rerun()
                            
                            with col_btn2:
                                if st.button(f"Cancelar #{cita['id']}", type="secondary"):
                                    db.execute_query("UPDATE citas SET estado = 'cancelada' WHERE id = ?", (cita['id'],))
                                    st.success("Cita cancelada")
                                    st.rerun()
            else:
                st.info("No se encontraron citas con ese número de teléfono.")
    
    with tab3:
        st.subheader("Consultar Cita por ID")
        
        cita_id = st.number_input("Número de Cita:", min_value=1, step=1)
        
        if st.button("Buscar Cita"):
            cita = db.execute_query("""
                SELECT 
                    c.id, c.fecha_cita, c.hora_cita, c.estado, c.observaciones,
                    cl.nombre as cliente_nombre, cl.telefono as cliente_telefono,
                    v.marca || ' ' || v.modelo || ' (' || v.placa || ')' as vehiculo_info,
                    s.nombre as servicio_nombre, s.precio as servicio_precio, s.duracion_minutos
                FROM citas c
                JOIN clientes cl ON c.cliente_id = cl.id
                JOIN vehiculos v ON c.vehiculo_id = v.id
                JOIN servicios s ON c.servicio_id = s.id
                WHERE c.id = ?
            """, (cita_id,))
            
            if cita:
                cita = cita[0]
                
                st.markdown(f"### Cita #{cita['id']}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.info(f"""
                    **Fecha:** {cita['fecha_cita']}  
                    **Hora:** {cita['hora_cita']}  
                    **Estado:** {cita['estado'].title()}
                    """)
                    
                    st.info(f"""
                    **Cliente:** {cita['cliente_nombre']}  
                    **Teléfono:** {cita['cliente_telefono']}
                    """)
                
                with col2:
                    st.info(f"""
                    **Vehículo:** {cita['vehiculo_info']}
                    """)
                    
                    st.info(f"""
                    **Servicio:** {cita['servicio_nombre']}  
                    **Precio:** S/ {cita['servicio_precio']:.2f}  
                    **Duración:** {cita['duracion_minutos']} minutos
                    """)
                
                if cita['observaciones']:
                    st.markdown(f"**Observaciones:** {cita['observaciones']}")
            
            else:
                st.error("No se encontró una cita con ese ID.")

def show_inventory_page():
    """Página de inventario"""
    st.title("📦 Inventario")
    
    tab1, tab2, tab3 = st.tabs(["Ver Inventario", "Agregar Item", "Stock Bajo"])
    
    with tab1:
        st.subheader("Inventario Actual")
        
        items = db.execute_query("""
            SELECT id, nombre, descripcion, cantidad_actual, cantidad_minima, 
                   precio_unitario, categoria
            FROM inventario 
            ORDER BY categoria, nombre
        """)
        
        if items:
            df = pd.DataFrame(items)
            df['Estado'] = df.apply(lambda row: 'Stock Bajo' if row['cantidad_actual'] <= row['cantidad_minima'] else 'OK', axis=1)
            df['Valor Total'] = df['cantidad_actual'] * df['precio_unitario']
            
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                categorias = ['Todos'] + sorted(df['categoria'].unique().tolist())
                categoria_filter = st.selectbox("Filtrar por Categoría:", categorias)
            
            with col2:
                estado_filter = st.selectbox("Filtrar por Estado:", ['Todos', 'OK', 'Stock Bajo'])
            
            # Aplicar filtros
            df_filtered = df.copy()
            if categoria_filter != 'Todos':
                df_filtered = df_filtered[df_filtered['categoria'] == categoria_filter]
            if estado_filter != 'Todos':
                df_filtered = df_filtered[df_filtered['Estado'] == estado_filter]
            
            # Mostrar tabla
            st.dataframe(
                df_filtered[['nombre', 'descripcion', 'categoria', 'cantidad_actual', 'cantidad_minima', 'precio_unitario', 'Valor Total', 'Estado']],
                use_container_width=True
            )
            
            # Métricas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Items", len(df))
            with col2:
                st.metric("Stock Bajo", len(df[df['Estado'] == 'Stock Bajo']))
            with col3:
                st.metric("Valor Total", f"S/ {df['Valor Total'].sum():.2f}")
            with col4:
                st.metric("Categorías", len(df['categoria'].unique()))
        
        else:
            st.info("No hay items en el inventario.")
    
    with tab2:
        st.subheader("Agregar Nuevo Item")
        
        with st.form("nuevo_item"):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre = st.text_input("Nombre del Item*")
                descripcion = st.text_area("Descripción")
                categoria = st.text_input("Categoría*")
            
            with col2:
                cantidad_actual = st.number_input("Cantidad Actual", min_value=0, value=0)
                cantidad_minima = st.number_input("Cantidad Mínima", min_value=1, value=5)
                precio_unitario = st.number_input("Precio Unitario (S/)", min_value=0.0, value=0.0, format="%.2f")
            
            submitted = st.form_submit_button("Agregar Item", type="primary")
            
            if submitted:
                if not all([nombre, categoria]):
                    st.error("Por favor completa todos los campos obligatorios (*)")
                else:
                    result = db.execute_query("""
                        INSERT INTO inventario (nombre, descripcion, cantidad_actual, cantidad_minima, precio_unitario, categoria)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (nombre, descripcion, cantidad_actual, cantidad_minima, precio_unitario, categoria))
                    
                    if result:
                        st.success(f"Item agregado exitosamente con ID: {result}")
                    else:
                        st.error("Error al agregar el item.")
    
    with tab3:
        st.subheader("Items con Stock Bajo")
        
        items_bajo_stock = db.execute_query("""
            SELECT nombre, descripcion, categoria, cantidad_actual, cantidad_minima,
                   (cantidad_minima - cantidad_actual) as deficit, id
            FROM inventario 
            WHERE cantidad_actual <= cantidad_minima
            ORDER BY (cantidad_minima - cantidad_actual) DESC
        """)
        
        if items_bajo_stock:
            st.warning(f"⚠️ {len(items_bajo_stock)} items necesitan reposición")
            
            for item in items_bajo_stock:
                with st.expander(f"{item['nombre']} - Déficit: {item['deficit']} unidades"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Categoría:** {item['categoria']}")
                        st.write(f"**Descripción:** {item['descripcion']}")
                    
                    with col2:
                        st.metric("Stock Actual", item['cantidad_actual'])
                        st.metric("Stock Mínimo", item['cantidad_minima'])
                        
                        nueva_cantidad = st.number_input(
                            f"Nueva cantidad para {item['nombre']}", 
                            min_value=0, 
                            value=item['cantidad_actual'],
                            key=f"stock_{item['id']}"
                        )
                        
                        if st.button(f"Actualizar Stock", key=f"btn_{item['id']}"):
                            if db.execute_query("UPDATE inventario SET cantidad_actual = ? WHERE id = ?", (nueva_cantidad, item['id'])):
                                st.success("Stock actualizado")
                                st.rerun()
        else:
            st.success("✅ Todos los items tienen stock suficiente")

def show_admin_panel():
    """Panel administrativo"""
    st.title("👨‍💼 Panel Administrativo")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Calendario", "Citas", "Reportes"])
    
    with tab1:
        st.subheader("Dashboard")
        
        today = str(date.today())
        
        # Métricas principales
        citas_hoy = db.execute_query("SELECT COUNT(*) as total FROM citas WHERE fecha_cita = ? AND estado != 'cancelada'", (today,))
        citas_pendientes = db.execute_query("SELECT COUNT(*) as total FROM citas WHERE estado = 'pendiente' AND fecha_cita >= ?", (today,))
        
        ingresos_mes = db.execute_query("""
            SELECT COALESCE(SUM(s.precio), 0) as total
            FROM citas c
            JOIN servicios s ON c.servicio_id = s.id
            WHERE strftime('%Y-%m', c.fecha_cita) = strftime('%Y-%m', ?)
            AND c.estado = 'completada'
        """, (today,))
        
        stock_bajo = db.execute_query("SELECT COUNT(*) as total FROM inventario WHERE cantidad_actual <= cantidad_minima")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Citas Hoy", citas_hoy[0]['total'] if citas_hoy else 0)
        with col2:
            st.metric("Citas Pendientes", citas_pendientes[0]['total'] if citas_pendientes else 0)
        with col3:
            st.metric("Ingresos del Mes", f"S/ {ingresos_mes[0]['total']:.2f}" if ingresos_mes else "S/ 0.00")
        with col4:
            st.metric("Stock Bajo", stock_bajo[0]['total'] if stock_bajo else 0, delta_color="inverse")
        
        # Gráfico de citas por estado
        st.subheader("Citas por Estado (Últimos 30 días)")
        
        fecha_limite = str(date.today() - timedelta(days=30))
        citas_estado = db.execute_query("""
            SELECT estado, COUNT(*) as cantidad
            FROM citas 
            WHERE fecha_cita >= ?
            GROUP BY estado
            ORDER BY cantidad DESC
        """, (fecha_limite,))
        
        if citas_estado:
            df_estado = pd.DataFrame(citas_estado)
            fig = px.pie(df_estado, values='cantidad', names='estado', title="Distribución de Citas por Estado")
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Calendario de Citas")
        
        fecha_seleccionada = st.date_input("Seleccionar fecha:", value=date.today())
        
        citas_dia = db.execute_query("""
            SELECT 
                c.id, c.hora_cita, c.estado, c.observaciones,
                cl.nombre as cliente_nombre, cl.telefono as cliente_telefono,
                v.marca || ' ' || v.modelo || ' (' || v.placa || ')' as vehiculo_info,
                s.nombre as servicio_nombre
            FROM citas c
            JOIN clientes cl ON c.cliente_id = cl.id
            JOIN vehiculos v ON c.vehiculo_id = v.id
            JOIN servicios s ON c.servicio_id = s.id
            WHERE c.fecha_cita = ?
            ORDER BY c.hora_cita
        """, (str(fecha_seleccionada),))
        
        if citas_dia:
            st.write(f"**{len(citas_dia)} citas programadas para {fecha_seleccionada}**")
            
            for cita in citas_dia:
                with st.container():
                    col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
                    
                    with col1:
                        st.write(f"**{cita['hora_cita']}**")
                    
                    with col2:
                        st.write(f"**{cita['cliente_nombre']}**")
                        st.caption(f"Tel: {cita['cliente_telefono']}")
                    
                    with col3:
                        st.write(f"{cita['servicio_nombre']}")
                        st.caption(f"{cita['vehiculo_info']}")
                    
                    with col4:
                        color = {
                            'pendiente': '🟡',
                            'confirmada': '🟢', 
                            'completada': '✅',
                            'cancelada': '❌'
                        }.get(cita['estado'], '⚪')
                        st.write(f"{color} {cita['estado'].title()}")
                    
                    st.markdown("---")
        else:
            st.info(f"No hay citas programadas para {fecha_seleccionada}")
    
    with tab3:
        st.subheader("Gestión de Citas")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            estado_filtro = st.selectbox("Estado:", ['Todos', 'pendiente', 'confirmada', 'completada', 'cancelada'])
        
        with col2:
            fecha_desde = st.date_input("Desde:", value=date.today() - timedelta(days=7))
        
        with col3:
            fecha_hasta = st.date_input("Hasta:", value=date.today() + timedelta(days=7))
        
        # Consulta con filtros
        query = """
            SELECT 
                c.id, c.fecha_cita, c.hora_cita, c.estado, c.observaciones,
                cl.nombre as cliente_nombre, cl.telefono as cliente_telefono,
                v.marca || ' ' || v.modelo || ' (' || v.placa || ')' as vehiculo_info,
                s.nombre as servicio_nombre, s.precio as servicio_precio
            FROM citas c
            JOIN clientes cl ON c.cliente_id = cl.id
            JOIN vehiculos v ON c.vehiculo_id = v.id
            JOIN servicios s ON c.servicio_id = s.id
            WHERE c.fecha_cita BETWEEN ? AND ?
        """
        params = [str(fecha_desde), str(fecha_hasta)]
        
        if estado_filtro != 'Todos':
            query += " AND c.estado = ?"
            params.append(estado_filtro)
        
        query += " ORDER BY c.fecha_cita DESC, c.hora_cita"
        
        citas_filtradas = db.execute_query(query, tuple(params))
        
        if citas_filtradas:
            for cita in citas_filtradas:
                with st.expander(f"#{cita['id']} - {cita['cliente_nombre']} - {cita['fecha_cita']} {cita['hora_cita']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Cliente:** {cita['cliente_nombre']}")
                        st.write(f"**Teléfono:** {cita['cliente_telefono']}")
                        st.write(f"**Vehículo:** {cita['vehiculo_info']}")
                    
                    with col2:
                        st.write(f"**Servicio:** {cita['servicio_nombre']}")
                        st.write(f"**Precio:** S/ {cita['servicio_precio']:.2f}")
                        st.write(f"**Estado:** {cita['estado'].title()}")
                    
                    if cita['observaciones']:
                        st.write(f"**Observaciones:** {cita['observaciones']}")
                    
                    # Botones de cambio de estado
                    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
                    
                    if cita['estado'] != 'pendiente':
                        with col_btn1:
                            if st.button("Marcar Pendiente", key=f"pend_{cita['id']}"):
                                if db.execute_query("UPDATE citas SET estado = 'pendiente' WHERE id = ?", (cita['id'],)):
                                    st.success("Estado actualizado")
                                    st.rerun()
                    
                    if cita['estado'] != 'confirmada':
                        with col_btn2:
                            if st.button("Confirmar", key=f"conf_{cita['id']}"):
                                if db.execute_query("UPDATE citas SET estado = 'confirmada' WHERE id = ?", (cita['id'],)):
                                    st.success("Estado actualizado")
                                    st.rerun()
                    
                    if cita['estado'] != 'completada':
                        with col_btn3:
                            if st.button("Completar", key=f"comp_{cita['id']}"):
                                if db.execute_query("UPDATE citas SET estado = 'completada' WHERE id = ?", (cita['id'],)):
                                    st.success("Estado actualizado")
                                    st.rerun()
                    
                    if cita['estado'] != 'cancelada':
                        with col_btn4:
                            if st.button("Cancelar", key=f"canc_{cita['id']}"):
                                if db.execute_query("UPDATE citas SET estado = 'cancelada' WHERE id = ?", (cita['id'],)):
                                    st.success("Estado actualizado")
                                    st.rerun()
        else:
            st.info("No se encontraron citas con los filtros seleccionados.")
    
    with tab4:
        st.subheader("Reportes")
        
        # Reporte de ingresos
        st.markdown("### 💰 Ingresos por Mes")
        
        fecha_limite = str(date.today() - timedelta(days=365))
        ingresos_mensuales = db.execute_query("""
            SELECT 
                strftime('%Y-%m', c.fecha_cita) as mes,
                SUM(s.precio) as total_ingresos,
                COUNT(*) as total_citas
            FROM citas c
            JOIN servicios s ON c.servicio_id = s.id
            WHERE c.estado = 'completada'
            AND c.fecha_cita >= ?
            GROUP BY strftime('%Y-%m', c.fecha_cita)
            ORDER BY mes DESC
        """, (fecha_limite,))
        
        if ingresos_mensuales:
            df_ingresos = pd.DataFrame(ingresos_mensuales)
            
            fig_ingresos = px.bar(
                df_ingresos, 
                x='mes', 
                y='total_ingresos', 
                title="Ingresos Mensuales",
                labels={'total_ingresos': 'Ingresos (S/)', 'mes': 'Mes'}
            )
            st.plotly_chart(fig_ingresos, use_container_width=True)
        
        # Reporte de servicios más solicitados
        st.markdown("### 🔧 Servicios Más Solicitados")
        
        fecha_limite_90 = str(date.today() - timedelta(days=90))
        servicios_populares = db.execute_query("""
            SELECT 
                s.nombre,
                COUNT(*) as cantidad_citas,
                SUM(s.precio) as ingresos_totales
            FROM citas c
            JOIN servicios s ON c.servicio_id = s.id
            WHERE c.fecha_cita >= ?
            AND c.estado != 'cancelada'
            GROUP BY s.id, s.nombre
            ORDER BY cantidad_citas DESC
            LIMIT 10
        """, (fecha_limite_90,))
        
        if servicios_populares:
            df_servicios = pd.DataFrame(servicios_populares)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_servicios = px.bar(
                    df_servicios, 
                    x='cantidad_citas', 
                    y='nombre', 
                    orientation='h',
                    title="Cantidad de Citas por Servicio"
                )
                st.plotly_chart(fig_servicios, use_container_width=True)
            
            with col2:
                st.dataframe(
                    df_servicios[['nombre', 'cantidad_citas', 'ingresos_totales']],
                    column_config={
                        'nombre': 'Servicio',
                        'cantidad_citas': 'Citas',
                        'ingresos_totales': st.column_config.NumberColumn(
                            'Ingresos (S/)',
                            format="S/ %.2f"
                        )
                    },
                    hide_index=True,
                    use_container_width=True
                )

def show_login_page():
    """Página de login"""
    st.title("🔐 Acceso Administrativo")
    
    with st.form("login_form"):
        st.markdown("### Iniciar Sesión")
        
        username = st.text_input("Usuario:")
        password = st.text_input("Contraseña:", type="password")
        
        submitted = st.form_submit_button("Iniciar Sesión", type="primary")
        
        if submitted:
            if authenticate_user(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("¡Bienvenido al panel administrativo!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
    
    st.markdown("---")
    st.info("**Usuario por defecto:** admin  \\n**Contraseña:** admin123")

def main():
    """Función principal de la aplicación"""
    
    # Inicializar estado de sesión
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'
    
    # Sidebar de navegación
    with st.sidebar:
        st.title("🔧 Taller AutoMax")
        st.markdown("---")
        
        # Navegación principal
        page = st.radio(
            "Navegación:",
            options=['home', 'services', 'citas', 'inventory'],
            format_func=lambda x: {
                'home': '🏠 Inicio',
                'services': '🛠️ Servicios', 
                'citas': '📅 Citas',
                'inventory': '📦 Inventario'
            }[x],
            index=['home', 'services', 'citas', 'inventory'].index(st.session_state.current_page)
        )
        
        st.session_state.current_page = page
        
        st.markdown("---")
        
        # Panel administrativo
        if st.session_state.authenticated:
            if st.button("👨‍💼 Panel Administrativo", use_container_width=True):
                st.session_state.current_page = 'admin'
                st.rerun()
            
            if st.button("🚪 Cerrar Sesión", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.current_page = 'home'
                st.rerun()
            
            st.success(f"Sesión activa: {st.session_state.username}")
        else:
            if st.button("🔐 Acceso Administrativo", use_container_width=True):
                st.session_state.current_page = 'login'
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📞 Contacto")
        st.info("""
        **Teléfono:**  
        (01) 234-5678
        
        **Email:**  
        info@tallerautomax.com
        
        **Horario:**  
        Lun-Vie: 8AM-6PM  
        Sáb: 8AM-2PM
        """)
    
    # Contenido principal
    if st.session_state.current_page == 'home':
        show_home_page()
    elif st.session_state.current_page == 'services':
        show_services_page()
    elif st.session_state.current_page == 'citas':
        show_appointments_page()
    elif st.session_state.current_page == 'inventory':
        show_inventory_page()
    elif st.session_state.current_page == 'login':
        show_login_page()
    elif st.session_state.current_page == 'admin':
        if st.session_state.authenticated:
            show_admin_panel()
        else:
            st.warning("Debes iniciar sesión para acceder al panel administrativo.")
            show_login_page()

if __name__ == "__main__":
    main()
'''

# Escribir el código de la aplicación
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)

print("✅ Aplicación creada exitosamente!")
print("📁 Archivos generados:")
print("   - app.py (aplicación principal)")
print("   - taller.db (base de datos SQLite - se creará automáticamente)")

# ===== CELDA 4: INSTALACIÓN DE NGROK Y EJECUCIÓN =====
# Instalar ngrok para túnel público
!pip install pyngrok -q

# Importar librerías necesarias
from pyngrok import ngrok
import subprocess
import threading
import time
import signal
import os

# Configurar token de ngrok (opcional pero recomendado)
# Obtén tu token gratuito en: https://ngrok.com/
# ngrok.set_auth_token("tu_token_aqui")

def run_streamlit():
    """Ejecuta la aplicación Streamlit"""
    os.system("streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true")

# Ejecutar Streamlit en un hilo separado
streamlit_thread = threading.Thread(target=run_streamlit, daemon=True)
streamlit_thread.start()

# Esperar un momento para que Streamlit inicie
time.sleep(5)

# Crear túnel público con ngrok
public_url = ngrok.connect(8501)

print("🚀 ¡Aplicación lista!")
print("="*50)
print(f"🌐 URL pública: {public_url}")
print("="*50)
print("📋 INFORMACIÓN IMPORTANTE:")
print("• Usuario administrador: admin")
print("• Contraseña: admin123")
print("• La aplicación usa SQLite (no requiere configuración adicional)")
print("• Los datos se guardan en el archivo 'taller.db'")
print("="*50)
print("🔄 Para detener la aplicación, interrumpe la ejecución de la celda")
print("📱 Comparte la URL pública para acceder desde cualquier dispositivo")

# Mantener la aplicación corriendo
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\\n🛑 Aplicación detenida")
    ngrok.disconnect(public_url)
    ngrok.kill()