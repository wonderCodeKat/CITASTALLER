# 🔧 Taller Automotriz - Aplicación Web

## Descripción

Aplicación web completa para la gestión de un taller automotriz, desarrollada con **Streamlit** y **PostgreSQL**. Incluye gestión de citas, clientes, vehículos, inventario y panel administrativo.

## 🚀 Características Principales

### Para Clientes:
- **Página de inicio** con información del taller, horarios y ubicación en Google Maps
- **Agendar citas** de forma sencilla e intuitiva
- **Consultar citas** por teléfono o número de cita
- **Ver servicios** disponibles con precios y duraciones
- **Confirmar o cancelar** citas existentes

### Para Administradores:
- **Dashboard** con métricas clave del negocio
- **Calendario de citas** con vista diaria
- **Gestión completa de citas** (cambiar estados, ver detalles)
- **Control de inventario** (agregar items, actualizar stock, alertas de stock bajo)
- **Reportes** de ingresos y servicios más solicitados
- **Login seguro** con autenticación

### Características Técnicas:
- **Base de datos PostgreSQL** con procedimientos almacenados
- **Interfaz responsive** y moderna con Streamlit
- **Validaciones** de horarios de trabajo y disponibilidad
- **Mapas interactivos** con Folium
- **Gráficos** interactivos con Plotly
- **Triggers** y funciones de base de datos para integridad de datos

## 📋 Requisitos

- Python 3.8 o superior
- PostgreSQL 12 o superior
- Docker y Docker Compose (opcional)

## 🛠️ Instalación

### Opción 1: Instalación Local

1. **Clonar el repositorio o crear los archivos:**
```bash
mkdir taller-automotriz
cd taller-automotriz
```

2. **Crear entorno virtual:**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

4. **Configurar PostgreSQL:**
   - Instalar PostgreSQL
   - Crear base de datos ejecutando el script `setup_database.sql`:
```bash
psql -U postgres -f setup_database.sql
```

5. **Configurar conexión a la base de datos:**
   Editar las variables de conexión en `app.py`:
```python
DB_CONFIG = {
    'host': 'localhost',
    'database': 'taller_db',
    'user': 'postgres',
    'password': 'tu_password',
    'port': 5432
}
```

6. **Ejecutar la aplicación:**
```bash
streamlit run app.py
```

### Opción 2: Con Docker (Recomendado)

1. **Crear los archivos del proyecto:**
   - `app.py` (código principal)
   - `requirements.txt` (dependencias)
   - `setup_database.sql` (script de base de datos)
   - `docker-compose.yml` (configuración Docker)
   - `Dockerfile` (imagen de la aplicación)

2. **Ejecutar con Docker Compose:**
```bash
docker-compose up -d
```

3. **Acceder a la aplicación:**
   - Aplicación Streamlit: http://localhost:8501
   - pgAdmin (opcional): http://localhost:8080

## 🔐 Credenciales por Defecto

- **Usuario administrador:** `admin`
- **Contraseña:** `admin123`

## 📱 Uso de la Aplicación

### Para Clientes:

1. **Agendar Cita:**
   - Ir a "Citas" → "Agendar Cita"
   - Llenar datos del cliente y vehículo
   - Seleccionar servicio, fecha y hora
   - Confirmar la cita

2. **Consultar Citas:**
   - Usar el número de teléfono o ID de cita
   - Ver estado actual de las citas
   - Confirmar o cancelar según sea necesario

### Para Administradores:

1. **Acceso al Panel:**
   - Hacer clic en "Acceso Administrativo"
   - Iniciar sesión con credenciales

2. **Gestionar Citas:**
   - Ver calendario diario
   - Cambiar estados de citas
   - Ver reportes de productividad

3. **Controlar Inventario:**
   - Agregar nuevos items
   - Actualizar cantidades
   - Recibir alertas de stock bajo

## 📊 Estructura de la Base de Datos

### Tablas Principales:
- **usuarios:** Administradores del sistema
- **clientes:** Información de clientes
- **vehiculos:** Vehículos asociados a clientes
- **servicios:** Servicios ofrecidos por el taller
- **citas:** Citas agendadas
- **inventario:** Stock de repuestos y materiales

### Procedimientos Almacenados:
- `sp_crear_cliente()`: Registrar nuevo cliente
- `sp_crear_vehiculo()`: Registrar vehículo
- `sp_crear_cita()`: Agendar nueva cita
- `sp_actualizar_cita()`: Cambiar estado de cita
- `sp_actualizar_inventario()`: Actualizar stock

### Vistas:
- `vista_citas_completas`: Información completa de citas
- `vista_stock_bajo`: Items que necesitan reposición

## 🔧 Configuración Avanzada

### Personalizar Horarios:
Modificar en la función `fn_validar_horario_cita()` del script SQL:
```sql
-- Cambiar horarios de atención
IF NEW.hora_cita < TIME '08:00:00' OR NEW.hora_cita > TIME '17:30:00' THEN
```

### Agregar Nuevos Servicios:
```sql
INSERT INTO servicios (nombre, descripcion, precio, duracion_minutos) 
VALUES ('Nuevo Servicio', 'Descripción', 100.00, 60);
```

### Configurar Ubicación del Taller:
En `app.py`, modificar las coordenadas:
```python
# Coordenadas del taller
lat, lon = -12.0931, -77.0465  # San Isidro, Lima
```

## 🚨 Solución de Problemas

### Error de conexión a la base de datos:
1. Verificar que PostgreSQL esté ejecutándose
2. Comprobar credenciales en `DB_CONFIG`
3. Verificar que la base de datos `taller_db` exista

### Puerto ocupado:
```bash
# Cambiar puerto de Streamlit
streamlit run app.py --server.port 8502
```

### Problemas con Docker:
```bash
# Reiniciar contenedores
docker-compose down
docker-compose up --build
```

## 📈 Funcionalidades Futuras

- [ ] Notificaciones por email/SMS
- [ ] Sistema de facturación
- [ ] API REST para integración móvil
- [ ] Reportes avanzados en PDF
- [ ] Sistema de recordatorios automáticos
- [ ] Gestión de proveedores
- [ ] Historial de mantenimiento por vehículo

## 🤝 Contribuciones

Para contribuir al proyecto:
1. Fork del repositorio
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para detalles.

## 📞 Soporte

Para soporte técnico o consultas:
- Email: soporte@tallerautomax.com
- Teléfono: (01) 234-5678

---

Desarrollado con ❤️ para talleres automotrices modernos