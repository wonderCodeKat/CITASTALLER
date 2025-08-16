-- Script para configurar la base de datos del Taller Automotriz
-- Ejecutar como usuario postgres

-- Crear base de datos
CREATE DATABASE taller_db;

-- Conectar a la base de datos taller_db
\c taller_db;

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_estado CHECK (estado IN ('pendiente', 'confirmada', 'completada', 'cancelada'))
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

-- Índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_citas_fecha ON citas(fecha_cita);
CREATE INDEX IF NOT EXISTS idx_citas_estado ON citas(estado);
CREATE INDEX IF NOT EXISTS idx_clientes_telefono ON clientes(telefono);
CREATE INDEX IF NOT EXISTS idx_vehiculos_placa ON vehiculos(placa);
CREATE INDEX IF NOT EXISTS idx_inventario_categoria ON inventario(categoria);

-- Procedimientos almacenados

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
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Error al crear cliente: %', SQLERRM;
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
EXCEPTION
    WHEN unique_violation THEN
        RAISE EXCEPTION 'La placa % ya está registrada', p_placa;
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Error al crear vehículo: %', SQLERRM;
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
    horario_ocupado BOOLEAN;
BEGIN
    -- Verificar disponibilidad de horario
    SELECT EXISTS (
        SELECT 1 FROM citas 
        WHERE fecha_cita = p_fecha_cita 
        AND hora_cita = p_hora_cita 
        AND estado != 'cancelada'
    ) INTO horario_ocupado;
    
    IF horario_ocupado THEN
        RAISE EXCEPTION 'El horario ya está ocupado';
    END IF;
    
    -- Verificar que la fecha no sea en el pasado
    IF p_fecha_cita < CURRENT_DATE THEN
        RAISE EXCEPTION 'No se pueden agendar citas en fechas pasadas';
    END IF;
    
    INSERT INTO citas (cliente_id, vehiculo_id, servicio_id, fecha_cita, hora_cita, observaciones)
    VALUES (p_cliente_id, p_vehiculo_id, p_servicio_id, p_fecha_cita, p_hora_cita, p_observaciones)
    RETURNING id INTO cita_id;
    
    RETURN cita_id;
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Error al crear cita: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- Procedimiento para actualizar estado de cita
CREATE OR REPLACE FUNCTION sp_actualizar_cita(
    p_cita_id INTEGER,
    p_estado VARCHAR(20)
)
RETURNS BOOLEAN AS $$
BEGIN
    -- Validar estado
    IF p_estado NOT IN ('pendiente', 'confirmada', 'completada', 'cancelada') THEN
        RAISE EXCEPTION 'Estado inválido: %', p_estado;
    END IF;
    
    UPDATE citas SET estado = p_estado WHERE id = p_cita_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'No se encontró la cita con ID: %', p_cita_id;
    END IF;
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Error al actualizar cita: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- Procedimiento para actualizar inventario
CREATE OR REPLACE FUNCTION sp_actualizar_inventario(
    p_item_id INTEGER,
    p_cantidad INTEGER
)
RETURNS BOOLEAN AS $$
BEGIN
    IF p_cantidad < 0 THEN
        RAISE EXCEPTION 'La cantidad no puede ser negativa';
    END IF;
    
    UPDATE inventario 
    SET cantidad_actual = p_cantidad 
    WHERE id = p_item_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'No se encontró el item con ID: %', p_item_id;
    END IF;
    
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Error al actualizar inventario: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- Función para obtener horarios disponibles
CREATE OR REPLACE FUNCTION fn_horarios_disponibles(
    p_fecha DATE
)
RETURNS TABLE(hora TIME) AS $$
BEGIN
    RETURN QUERY
    WITH horarios_base AS (
        SELECT (TIME '08:00:00' + (interval '30 minutes' * generate_series(0, 19))) AS hora_disponible
    ),
    horarios_ocupados AS (
        SELECT hora_cita 
        FROM citas 
        WHERE fecha_cita = p_fecha 
        AND estado != 'cancelada'
    )
    SELECT hb.hora_disponible
    FROM horarios_base hb
    LEFT JOIN horarios_ocupados ho ON hb.hora_disponible = ho.hora_cita
    WHERE ho.hora_cita IS NULL
    AND hb.hora_disponible <= TIME '17:00:00'
    ORDER BY hb.hora_disponible;
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
    c.created_at,
    cl.nombre as cliente_nombre,
    cl.telefono as cliente_telefono,
    cl.email as cliente_email,
    v.marca || ' ' || v.modelo || ' (' || v.placa || ')' as vehiculo_info,
    v.marca as vehiculo_marca,
    v.modelo as vehiculo_modelo,
    v.placa as vehiculo_placa,
    v.año as vehiculo_año,
    v.color as vehiculo_color,
    s.nombre as servicio_nombre,
    s.descripcion as servicio_descripcion,
    s.precio as servicio_precio,
    s.duracion_minutos
FROM citas c
JOIN clientes cl ON c.cliente_id = cl.id
JOIN vehiculos v ON c.vehiculo_id = v.id
JOIN servicios s ON c.servicio_id = s.id;

-- Vista para items con stock bajo
CREATE OR REPLACE VIEW vista_stock_bajo AS
SELECT 
    id,
    nombre,
    descripcion,
    categoria,
    cantidad_actual,
    cantidad_minima,
    (cantidad_minima - cantidad_actual) as deficit,
    precio_unitario
FROM inventario 
WHERE cantidad_actual <= cantidad_minima
ORDER BY (cantidad_minima - cantidad_actual) DESC;

-- Insertar datos iniciales

-- Usuario administrador por defecto (password: admin123)
INSERT INTO usuarios (username, password_hash) 
VALUES ('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9')
ON CONFLICT (username) DO NOTHING;

-- Servicios básicos
INSERT INTO servicios (nombre, descripcion, precio, duracion_minutos) VALUES
('Cambio de Aceite', 'Cambio de aceite y filtro de motor', 45.00, 30),
('Revisión General', 'Diagnóstico completo del vehículo', 80.00, 60),
('Cambio de Frenos', 'Cambio de pastillas y discos de freno', 120.00, 90),
('Alineación y Balanceo', 'Alineación de ruedas y balanceo de llantas', 35.00, 45),
('Cambio de Batería', 'Instalación de batería nueva y prueba del sistema eléctrico', 25.00, 20),
('Reparación de Motor', 'Reparación y mantenimiento general de motor', 200.00, 240),
('Cambio de Llantas', 'Montaje y balanceo de llantas nuevas', 40.00, 60),
('Limpieza de Inyectores', 'Limpieza del sistema de inyección de combustible', 60.00, 90),
('Revisión de Aire Acondicionado', 'Diagnóstico y reparación de sistema A/C', 70.00, 75),
('Cambio de Amortiguadores', 'Instalación de amortiguadores nuevos', 150.00, 120)
ON CONFLICT DO NOTHING;

-- Items de inventario básicos
INSERT INTO inventario (nombre, descripcion, cantidad_actual, cantidad_minima, precio_unitario, categoria) VALUES
('Aceite 5W-30', 'Aceite para motor sintético 5W-30', 25, 5, 35.00, 'Lubricantes'),
('Aceite 10W-40', 'Aceite para motor semi-sintético 10W-40', 20, 5, 30.00, 'Lubricantes'),
('Filtro de Aceite Universal', 'Filtro de aceite para vehículos estándar', 15, 3, 8.50, 'Filtros'),
('Filtro de Aire', 'Filtro de aire del motor', 12, 4, 15.00, 'Filtros'),
('Pastillas de Freno Delanteras', 'Pastillas de freno cerámicas delanteras', 8, 2, 45.00, 'Frenos'),
('Pastillas de Freno Traseras', 'Pastillas de freno cerámicas traseras', 6, 2, 40.00, 'Frenos'),
('Discos de Freno', 'Discos de freno ventilados', 4, 2, 80.00, 'Frenos'),
('Batería 12V 60Ah', 'Batería de automóvil 12V 60Ah', 5, 2, 85.00, 'Eléctrico'),
('Batería 12V 75Ah', 'Batería de automóvil 12V 75Ah', 3, 1, 110.00, 'Eléctrico'),
('Llantas 185/65R15', 'Llantas radiales 185/65R15', 12, 4, 120.00, 'Llantas'),
('Llantas 195/60R15', 'Llantas radiales 195/60R15', 8, 4, 135.00, 'Llantas'),
('Amortiguadores Delanteros', 'Par de amortiguadores delanteros', 6, 2, 180.00, 'Suspensión'),
('Amortiguadores Traseros', 'Par de amortiguadores traseros', 4, 2, 160.00, 'Suspensión'),
('Bujías', 'Juego de bujías de encendido', 20, 5, 25.00, 'Encendido'),
('Cables de Bujías', 'Juego de cables de alta tensión', 8, 2, 35.00, 'Encendido'),
('Refrigerante', 'Líquido refrigerante concentrado 1L', 15, 3, 18.00, 'Lubricantes'),
('Líquido de Frenos', 'Líquido de frenos DOT 3', 10, 3, 12.00, 'Frenos'),
('Grasa Multiuso', 'Grasa lubricante multiuso 500g', 8, 2, 15.00, 'Lubricantes')
ON CONFLICT DO NOTHING;

-- Insertar algunos clientes y vehículos de ejemplo (opcional)
INSERT INTO clientes (nombre, telefono, email, direccion) VALUES
('Juan Pérez', '987654321', 'juan.perez@email.com', 'Av. Arequipa 123, Lima'),
('María García', '987654322', 'maria.garcia@email.com', 'Jr. Cusco 456, San Isidro'),
('Carlos López', '987654323', 'carlos.lopez@email.com', 'Av. Javier Prado 789, Miraflores')
ON CONFLICT DO NOTHING;

-- Insertar vehículos de ejemplo
INSERT INTO vehiculos (cliente_id, marca, modelo, año, placa, color) VALUES
(1, 'Toyota', 'Corolla', 2018, 'ABC-123', 'Blanco'),
(2, 'Honda', 'Civic', 2020, 'DEF-456', 'Negro'),
(3, 'Nissan', 'Sentra', 2019, 'GHI-789', 'Gris')
ON CONFLICT DO NOTHING;

-- Triggers para auditoría y validaciones

-- Trigger para validar horarios de trabajo
CREATE OR REPLACE FUNCTION fn_validar_horario_cita()
RETURNS TRIGGER AS $
BEGIN
    -- Validar que la cita esté en horario de trabajo (8:00 AM - 5:30 PM)
    IF NEW.hora_cita < TIME '08:00:00' OR NEW.hora_cita > TIME '17:30:00' THEN
        RAISE EXCEPTION 'Las citas solo se pueden agendar entre 8:00 AM y 5:30 PM';
    END IF;
    
    -- Validar que no sea domingo (asumiendo que domingo = 0)
    IF EXTRACT(DOW FROM NEW.fecha_cita) = 0 THEN
        RAISE EXCEPTION 'No se pueden agendar citas los domingos';
    END IF;
    
    -- Validar que no sea sábado después de las 2:00 PM
    IF EXTRACT(DOW FROM NEW.fecha_cita) = 6 AND NEW.hora_cita > TIME '14:00:00' THEN
        RAISE EXCEPTION 'Los sábados solo se atiende hasta las 2:00 PM';
    END IF;
    
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

CREATE TRIGGER tr_validar_horario_cita
    BEFORE INSERT OR UPDATE ON citas
    FOR EACH ROW
    EXECUTE FUNCTION fn_validar_horario_cita();

-- Función para generar reportes de productividad
CREATE OR REPLACE FUNCTION fn_reporte_productividad(
    p_fecha_inicio DATE,
    p_fecha_fin DATE
)
RETURNS TABLE(
    fecha DATE,
    total_citas BIGINT,
    citas_completadas BIGINT,
    ingresos_totales NUMERIC,
    servicios_mas_solicitados TEXT
) AS $
BEGIN
    RETURN QUERY
    WITH citas_por_dia AS (
        SELECT 
            c.fecha_cita,
            COUNT(*) as total_citas,
            COUNT(CASE WHEN c.estado = 'completada' THEN 1 END) as citas_completadas,
            COALESCE(SUM(CASE WHEN c.estado = 'completada' THEN s.precio ELSE 0 END), 0) as ingresos_totales
        FROM citas c
        JOIN servicios s ON c.servicio_id = s.id
        WHERE c.fecha_cita BETWEEN p_fecha_inicio AND p_fecha_fin
        GROUP BY c.fecha_cita
    ),
    servicios_populares AS (
        SELECT 
            c.fecha_cita,
            STRING_AGG(s.nombre, ', ' ORDER BY COUNT(*) DESC) as servicios_mas_solicitados
        FROM citas c
        JOIN servicios s ON c.servicio_id = s.id
        WHERE c.fecha_cita BETWEEN p_fecha_inicio AND p_fecha_fin
        AND c.estado != 'cancelada'
        GROUP BY c.fecha_cita
    )
    SELECT 
        cpd.fecha_cita,
        cpd.total_citas,
        cpd.citas_completadas,
        cpd.ingresos_totales,
        COALESCE(sp.servicios_mas_solicitados, 'N/A')
    FROM citas_por_dia cpd
    LEFT JOIN servicios_populares sp ON cpd.fecha_cita = sp.fecha_cita
    ORDER BY cpd.fecha_cita;
END;
$ LANGUAGE plpgsql;

-- Función para notificar stock bajo
CREATE OR REPLACE FUNCTION fn_notificar_stock_bajo()
RETURNS TABLE(
    item_id INTEGER,
    nombre VARCHAR(100),
    cantidad_actual INTEGER,
    cantidad_minima INTEGER,
    deficit INTEGER
) AS $
BEGIN
    RETURN QUERY
    SELECT 
        i.id,
        i.nombre,
        i.cantidad_actual,
        i.cantidad_minima,
        (i.cantidad_minima - i.cantidad_actual) as deficit
    FROM inventario i
    WHERE i.cantidad_actual <= i.cantidad_minima
    ORDER BY (i.cantidad_minima - i.cantidad_actual) DESC;
END;
$ LANGUAGE plpgsql;

-- Crear índices adicionales para optimización
CREATE INDEX IF NOT EXISTS idx_citas_cliente_fecha ON citas(cliente_id, fecha_cita);
CREATE INDEX IF NOT EXISTS idx_citas_servicio_estado ON citas(servicio_id, estado);
CREATE INDEX IF NOT EXISTS idx_vehiculos_cliente ON vehiculos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_inventario_stock_bajo ON inventario(cantidad_actual, cantidad_minima);

-- Comentarios en las tablas
COMMENT ON TABLE usuarios IS 'Tabla de usuarios del sistema (administradores)';
COMMENT ON TABLE clientes IS 'Tabla de clientes del taller';
COMMENT ON TABLE vehiculos IS 'Tabla de vehículos asociados a clientes';
COMMENT ON TABLE servicios IS 'Tabla de servicios ofrecidos por el taller';
COMMENT ON TABLE citas IS 'Tabla de citas agendadas';
COMMENT ON TABLE inventario IS 'Tabla de inventario de repuestos y materiales';

-- Mensaje de confirmación
DO $
BEGIN
    RAISE NOTICE 'Base de datos del Taller Automotriz configurada exitosamente!';
    RAISE NOTICE 'Usuario administrador: admin';
    RAISE NOTICE 'Contraseña: admin123';
    RAISE NOTICE 'Servicios iniciales: % registrados', (SELECT COUNT(*) FROM servicios);
    RAISE NOTICE 'Items de inventario: % registrados', (SELECT COUNT(*) FROM inventario);
END $;