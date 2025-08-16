# app.py - Aplicación Taller Automotriz con Streamlit
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from datetime import datetime, date, timedelta
import hashlib
import folium
from streamlit_folium import st_folium
import plotly.express as px
from typing import Dict, List, Optional, Tuple

# Configuración de la página
st.set_page_config(
    page_title="Taller AutoMax",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',  # Cambiar por tu host
    'database': 'taller_db',
    'user': 'postgres',
    'password': 'password',  # Cambiar por tu password
    'port': 5432
}

class DatabaseManager:
    def __init__(self, config: Dict):
        self.config = config
    
    def get_connection(self):
        """Obtiene conexión a la base de datos"""
        try:
            return psycopg2.connect(**self.config)
        except Exception as e:
            st.error(f"Error conectando a la base de datos: {e}")
            return None
    
    def execute_procedure(self, procedure_name: str, params: tuple = None):
        """Ejecuta un procedimiento almacenado"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                if params:
                    cursor.callproc(procedure_name, params)
                else:
                    cursor.callproc(procedure_name)
                
                try:
                    result = cursor.fetchall()
                except:
                    result = None
                
                conn.commit()
                return result
        except Exception as e:
            st.error(f"Error ejecutando procedimiento {procedure_name}: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: tuple = None):
        """Ejecuta una consulta SQL"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                
                try:
                    result = cursor.fetchall()
                except:
                    result = None
                
                conn.commit()
                return result
        except Exception as e:
            st.error(f"Error ejecutando consulta: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

# Inicializar gestor de base de datos
db = DatabaseManager(DB_CONFIG)

def init_database():
    """Inicializa la base de datos con las tablas y procedimientos almacenados"""
    
    # Script SQL para crear tablas
    create_tables_sql = """
    -- Tabla de usuarios/administradores
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        rol VARCHAR(20) DEFAULT 'admin',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Tabla de clientes
    CREATE TABLE IF NOT EXISTS clientes (
        id SERIAL PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        telefono VARCHAR(20),
        email VARCHAR(100),
        direccion TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Tabla de vehículos
    CREATE TABLE IF NOT EXISTS vehiculos (
        id SERIAL PRIMARY KEY,
        cliente_id INTEGER REFERENCES clientes(id),
        marca VARCHAR(50) NOT NULL,
        modelo VARCHAR(50) NOT NULL,
        año INTEGER,
        placa VARCHAR(20) UNIQUE,
        color VARCHAR(30),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Tabla de servicios
    CREATE TABLE IF NOT EXISTS servicios (
        id SERIAL PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        descripcion TEXT,
        precio DECIMAL(10,2) NOT NULL,
        duracion_minutos INTEGER DEFAULT 60,
        activo BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Tabla de citas
    CREATE TABLE IF NOT EXISTS citas (
        id SERIAL PRIMARY KEY,
        cliente_id INTEGER REFERENCES clientes(id),
        vehiculo_id INTEGER REFERENCES vehiculos(id),
        servicio_id INTEGER REFERENCES servicios(id),
        fecha_cita DATE NOT NULL,
        hora_cita TIME NOT NULL,
        estado VARCHAR(20) DEFAULT 'pendiente',
        observaciones TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Tabla de inventario
    CREATE TABLE IF NOT EXISTS inventario (
        id SERIAL PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        descripcion TEXT,
        cantidad_actual INTEGER DEFAULT 0,
        cantidad_minima INTEGER DEFAULT 5,
        precio_unitario DECIMAL(10,2),
        categoria VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Procedimientos almacenados
    procedures_sql = """
    -- Procedimiento para crear cliente
    CREATE OR REPLACE FUNCTION sp_crear_cliente(
        p_nombre VARCHAR(100),
        p_telefono VARCHAR(20),
        p_email VARCHAR(100),
        p_direccion TEXT
    )
    RETURNS INTEGER AS $$
    DECLARE
        cliente_id INTEGER;
    BEGIN
        INSERT INTO clientes (nombre, telefono, email, direccion)
        VALUES (p_nombre, p_telefono, p_email, p_direccion)
        RETURNING id INTO cliente_id;
        RETURN cliente_id;
    END;
    $$ LANGUAGE plpgsql;
    
    -- Procedimiento para crear vehículo
    CREATE OR REPLACE FUNCTION sp_crear_vehiculo(
        p_cliente_id INTEGER,
        p_marca VARCHAR(50),
        p_modelo VARCHAR(50),
        p_año INTEGER,
        p_placa VARCHAR(20),
        p_color VARCHAR(30)
    )
    RETURNS INTEGER AS $$
    DECLARE
        vehiculo_id INTEGER;
    BEGIN
        INSERT INTO vehiculos (cliente_id, marca, modelo, año, placa, color)
        VALUES (p_cliente_id, p_marca, p_modelo, p_año, p_placa, p_color)
        RETURNING id INTO vehiculo_id;
        RETURN vehiculo_id;
    END;
    $$ LANGUAGE plpgsql;
    
    -- Procedimiento para crear cita
    CREATE OR REPLACE FUNCTION sp_crear_cita(
        p_cliente_id INTEGER,
        p_vehiculo_id INTEGER,
        p_servicio_id INTEGER,
        p_fecha_cita DATE,
        p_hora_cita TIME,
        p_observaciones TEXT
    )
    RETURNS INTEGER AS $$
    DECLARE
        cita_id INTEGER;
    BEGIN
        -- Verificar disponibilidad de horario
        IF EXISTS (
            SELECT 1 FROM citas 
            WHERE fecha_cita = p_fecha_cita 
            AND hora_cita = p_hora_cita 
            AND estado != 'cancelada'
        ) THEN
            RAISE EXCEPTION 'El horario ya está ocupado';
        END IF;
        
        INSERT INTO citas (cliente_id, vehiculo_id, servicio_id, fecha_cita, hora_cita, observaciones)
        VALUES (p_cliente_id, p_vehiculo_id, p_servicio_id, p_fecha_cita, p_hora_cita, p_observaciones)
        RETURNING id INTO cita_id;
        RETURN cita_id;
    END;
    $$ LANGUAGE plpgsql;
    
    -- Procedimiento para actualizar estado de cita
    CREATE OR REPLACE FUNCTION sp_actualizar_cita(
        p_cita_id INTEGER,
        p_estado VARCHAR(20)
    )
    RETURNS BOOLEAN AS $$
    BEGIN
        UPDATE citas SET estado = p_estado WHERE id = p_cita_id;
        RETURN FOUND;
    END;
    $$ LANGUAGE plpgsql;
    
    -- Procedimiento para actualizar inventario
    CREATE OR REPLACE FUNCTION sp_actualizar_inventario(
        p_item_id INTEGER,
        p_cantidad INTEGER
    )
    RETURNS BOOLEAN AS $$
    BEGIN
        UPDATE inventario 
        SET cantidad_actual = p_cantidad 
        WHERE id = p_item_id;
        RETURN FOUND;
    END;
    $$ LANGUAGE plpgsql;
    
    -- Vista para citas completas
    CREATE OR REPLACE VIEW vista_citas_completas AS
    SELECT 
        c.id,
        c.fecha_cita,
        c.hora_cita,
        c.estado,
        c.observaciones,
        cl.nombre as cliente_nombre,
        cl.telefono as cliente_telefono,
        v.marca || ' ' || v.modelo || ' (' || v.placa || ')' as vehiculo_info,
        s.nombre as servicio_nombre,
        s.precio as servicio_precio,
        s.duracion_minutos
    FROM citas c
    JOIN clientes cl ON c.cliente_id = cl.id
    JOIN vehiculos v ON c.vehiculo_id = v.id
    JOIN servicios s ON c.servicio_id = s.id;
    """
    
    # Datos iniciales
    initial_data_sql = """
    -- Usuario administrador por defecto (password: admin123)
    INSERT INTO usuarios (username, password_hash) 
    VALUES ('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9')
    ON CONFLICT (username) DO NOTHING;
    
    -- Servicios básicos
    INSERT INTO servicios (nombre, descripcion, precio, duracion_minutos) VALUES
    ('Cambio de Aceite', 'Cambio de aceite y filtro', 45.00, 30),
    ('Revisión General', 'Diagnóstico completo del vehículo', 80.00, 60),
    ('Cambio de Frenos', 'Cambio de pastillas y discos de freno', 120.00, 90),
    ('Alineación y Balanceo', 'Alineación de ruedas y balanceo', 35.00, 45),
    ('Cambio de Batería', 'Instalación de batería nueva', 25.00, 20),
    ('Reparación de Motor', 'Reparación y mantenimiento de motor', 200.00, 240)
    ON CONFLICT DO NOTHING;
    
    -- Items de inventario básicos
    INSERT INTO inventario (nombre, descripcion, cantidad_actual, cantidad_minima, precio_unitario, categoria) VALUES
    ('Aceite 5W-30', 'Aceite para motor sintético', 20, 5, 35.00, 'Lubricantes'),
    ('Filtro de Aceite', 'Filtro de aceite universal', 15, 3, 8.50, 'Filtros'),
    ('Pastillas de Freno', 'Pastillas de freno cerámicas', 8, 2, 45.00, 'Frenos'),
    ('Batería 12V', 'Batería de automóvil 12V', 5, 2, 85.00, 'Eléctrico'),
    ('Llantas 185/65R15', 'Llantas para automóvil', 12, 4, 120.00, 'Llantas')
    ON CONFLICT DO NOTHING;
    """
    
    try:
        conn = db.get_connection()
        if conn:
            cursor = conn.cursor()
            
            # Crear tablas
            cursor.execute(create_tables_sql)
            
            # Crear procedimientos y vistas
            cursor.execute(procedures_sql)
            
            # Insertar datos iniciales
            cursor.execute(initial_data_sql)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
    except Exception as e:
        st.error(f"Error inicializando base de datos: {e}")
        return False

def hash_password(password: str) -> str:
    """Genera hash SHA-256 de la contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username: str, password: str) -> bool:
    """Autentica usuario"""
    password_hash = hash_password(password)
    result = db.execute_query(
        "SELECT id FROM usuarios WHERE username = %s AND password_hash = %s",
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
    
    # Obtener servicios de la base de datos
    servicios = db.execute_query(
        "SELECT nombre, descripcion, precio, duracion_minutos FROM servicios WHERE activo = TRUE ORDER BY precio"
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
            
            # Servicio y fecha/hora
            st.markdown("**Detalles de la Cita**")
            
            # Obtener servicios disponibles
            servicios = db.execute_query("SELECT id, nombre, precio FROM servicios WHERE activo = TRUE ORDER BY nombre")
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
                # Horarios disponibles (8:00 AM a 5:00 PM)
                horarios = [f"{h:02d}:{m:02d}" for h in range(8, 18) for m in [0, 30]]
                hora_cita = st.selectbox("Hora de la Cita*", options=horarios)
            
            observaciones = st.text_area("Observaciones")
            
            submitted = st.form_submit_button("Agendar Cita", type="primary")
            
            if submitted:
                if not all([nombre_cliente, telefono, marca, modelo, placa]) or not servicio_id:
                    st.error("Por favor completa todos los campos obligatorios (*)")
                else:
                    try:
                        # Crear cliente
                        cliente_id = db.execute_procedure(
                            'sp_crear_cliente',
                            (nombre_cliente, telefono, email, direccion)
                        )[0][0]
                        
                        # Crear vehículo
                        vehiculo_id = db.execute_procedure(
                            'sp_crear_vehiculo',
                            (cliente_id, marca, modelo, año, placa, color)
                        )[0][0]
                        
                        # Crear cita
                        cita_id = db.execute_procedure(
                            'sp_crear_cita',
                            (cliente_id, vehiculo_id, servicio_id, fecha_cita, hora_cita, observaciones)
                        )[0][0]
                        
                        st.success(f"¡Cita agendada exitosamente! Número de cita: {cita_id}")
                        
                    except Exception as e:
                        if "ya está ocupado" in str(e):
                            st.error("El horario seleccionado ya está ocupado. Por favor elige otro horario.")
                        elif "duplicate key" in str(e):
                            st.error("La placa del vehículo ya está registrada.")
                        else:
                            st.error(f"Error al agendar la cita: {e}")
    
    with tab2:
        st.subheader("Consultar Citas por Teléfono")
        
        telefono_buscar = st.text_input("Ingresa tu número de teléfono:")
        
        if telefono_buscar:
            citas = db.execute_query("""
                SELECT * FROM vista_citas_completas 
                WHERE cliente_telefono LIKE %s 
                ORDER BY fecha_cita DESC, hora_cita
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
                        
                        # Botones de acción para citas pendientes
                        if cita['estado'] == 'pendiente':
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                if st.button(f"Confirmar #{cita['id']}", type="primary"):
                                    if db.execute_procedure('sp_actualizar_cita', (cita['id'], 'confirmada')):
                                        st.success("Cita confirmada")
                                        st.rerun()
                            
                            with col_btn2:
                                if st.button(f"Cancelar #{cita['id']}", type="secondary"):
                                    if db.execute_procedure('sp_actualizar_cita', (cita['id'], 'cancelada')):
                                        st.success("Cita cancelada")
                                        st.rerun()
            else:
                st.info("No se encontraron citas con ese número de teléfono.")
    
    with tab3:
        st.subheader("Consultar Cita por ID")
        
        cita_id = st.number_input("Número de Cita:", min_value=1, step=1)
        
        if st.button("Buscar Cita"):
            cita = db.execute_query(
                "SELECT * FROM vista_citas_completas WHERE id = %s", 
                (cita_id,)
            )
            
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
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (nombre, descripcion, cantidad_actual, cantidad_minima, precio_unitario, categoria))
                    
                    if result:
                        st.success(f"Item agregado exitosamente con ID: {result[0]['id']}")
                    else:
                        st.error("Error al agregar el item.")
    
    with tab3:
        st.subheader("Items con Stock Bajo")
        
        items_bajo_stock = db.execute_query("""
            SELECT nombre, descripcion, categoria, cantidad_actual, cantidad_minima,
                   (cantidad_minima - cantidad_actual) as deficit
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
                    