# 🚀 Instalación en Google Colab - Taller Automotriz

## 📋 Pasos para ejecutar la aplicación

### 1. Abrir Google Colab
- Ve a [colab.research.google.com](https://colab.research.google.com)
- Crea un nuevo notebook

### 2. Ejecutar las celdas en orden

**CELDA 1: Instalación de dependencias**
```python
!pip install streamlit pyngrok sqlite3 pandas plotly folium streamlit-folium -q
```

**CELDA 2: Configuración de archivos**
```python
import os
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime, date, timedelta
import json

# Crear directorio para la aplicación
os.makedirs('/content/taller_app', exist_ok=True)
os.chdir('/content/taller_app')
```

**CELDA 3: Copiar todo el código de la aplicación**
- Copia y pega todo el código del archivo `app.py` que está en el artefacto anterior

**CELDA 4: Ejecutar la aplicación**
```python
# Instalar ngrok para túnel público
!pip install pyngrok -q

# Importar librerías necesarias
from pyngrok import ngrok
import subprocess
import threading
import time
import signal
import os

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
print("📋 INFORMACIÓN:")
print("• Usuario admin: admin")
print("• Contraseña: admin123")
print("• Base de datos: SQLite")
print("="*50)

# Mantener corriendo
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\\n🛑 Detenido")
    ngrok.disconnect(public_url)
    ngrok.kill()
```

## 🎯 Versión Rápida - Una sola celda

Si prefieres ejecutar todo de una vez, usa esta celda única:

```python
# INSTALACIÓN COMPLETA EN UNA CELDA
!pip install streamlit pyngrok pandas plotly folium streamlit-folium -q

import os
os.makedirs('/content/taller_app', exist_ok=True)
os.chdir('/content/taller_app')

# [Aquí va todo el código del app.py]
# Copia el código completo del artefacto anterior

# Crear archivo app.py
app_code = '''
# [Todo el código de la aplicación va aquí]
'''

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(app_code)

# Ejecutar aplicación
from pyngrok import ngrok
import threading
import time

def run_streamlit():
    os.system("streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true")

streamlit_thread = threading.Thread(target=run_streamlit, daemon=True)
streamlit_thread.start()
time.sleep(5)

public_url = ngrok.connect(8501)
print(f"🌐 Aplicación disponible en: {public_url}")
print("👤 Usuario: admin | 🔑 Contraseña: admin123")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    ngrok.disconnect(public_url)
    ngrok.kill()
```

## ⚡ Características de la versión Colab

### ✅ Ventajas:
- **Sin configuración**: No necesitas instalar PostgreSQL
- **Base de datos SQLite**: Funciona directamente en Colab
- **Túnel público**: Accesible desde cualquier dispositivo
- **Datos persistentes**: Durante la sesión de Colab
- **Instalación rápida**: 2-3 minutos para estar funcionando

### ⚠️ Limitaciones:
- **Sesión temporal**: Los datos se pierden al cerrar Colab
- **Límite de tiempo**: Colab desconecta después de un tiempo inactivo
- **Rendimiento**: Menor que una instalación local

### 🔧 Diferencias con la versión PostgreSQL:
- **SQLite** en lugar de PostgreSQL
- **Sin procedimientos almacenados** (lógica en Python)
- **Sintaxis SQL** adaptada para SQLite
- **Funcionalidad idéntica** en la interfaz

## 📱 Uso de la aplicación

1. **Ejecuta las celdas** en orden
2. **Copia la URL pública** que aparece en la salida
3. **Abre la URL** en tu navegador
4. **Navega por la aplicación**:
   - Inicio: Información y mapa del taller
   - Servicios: Lista de servicios disponibles
   - Citas: Agendar y gestionar citas
   - Inventario: Control de stock
   - Admin: Panel administrativo (login requerido)

## 🔐 Credenciales

- **Usuario administrador**: `admin`
- **Contraseña**: `admin123`

## 🚨 Consejos importantes

1. **Guarda el notebook**: Para poder volver a ejecutarlo
2. **Comparte la URL**: Funciona en móviles y tablets
3. **Descarga datos**: Si quieres guardar la información
4. **Ngrok gratuito**: Límite de conexiones concurrentes
5. **Tiempo de sesión**: Ejecuta de nuevo si se desconecta

## 🔄 Reiniciar la aplicación

Si necesitas reiniciar:
1. Interrumpe la celda actual (Ctrl+M I)
2. Ejecuta nuevamente la celda 4
3. Obtendrás una nueva URL

## 📊 Funcionalidades incluidas

✅ Página de inicio con mapa  
✅ Sistema completo de citas  
✅ Gestión de clientes y vehículos  
✅ Inventario con alertas  
✅ Panel administrativo  
✅ Dashboard con métricas  
✅ Reportes gráficos  
✅ Autenticación de usuario  
✅ Interfaz responsive  

## 🎉 ¡Listo para usar!

Una vez ejecutado, tendrás una aplicación web completa para taller automotriz corriendo en la nube, accesible desde cualquier dispositivo. Perfecta para demostrar o usar temporalmente.

---

*Nota: Para uso en producción se recomienda la instalación con PostgreSQL y hosting dedicado.*