# 📚 Plataforma de Capacitación

Plataforma web para gestionar capacitaciones empresariales con registro de usuarios, cronometraje de sesiones y gestión de contenido por áreas.

## ✨ Características

- ✅ **Registro de usuarios** sin login (nombres, apellidos, cédula, correo, área)
- ⏱️ **Cronómetro automático** que registra tiempo en plataforma
- 📹 **Videos organizados por área** (enlaces a SharePoint u otra plataforma)
- 📢 **Sistema de anuncios** para capacitaciones programadas
- 🔐 **Panel administrativo** con exportación de datos
- 📊 **Estadísticas y reportes** de capacitación
- 💾 **Almacenamiento persistente** de datos en archivos JSON

## 🚀 Instalación Local

### Requisitos previos
- Python 3.8 o superior
- pip

### Pasos de instalación

1. **Clonar el repositorio**
```bash
git clone https://github.com/tu-usuario/plataforma-capacitacion.git
cd plataforma-capacitacion
```

2. **Crear entorno virtual (opcional pero recomendado)**
```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En Mac/Linux
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Ejecutar la aplicación**
```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

## 🌐 Despliegue en Streamlit Cloud

### Opción 1: Desde GitHub (Recomendado)

1. **Sube tu código a GitHub**
   - Crea un nuevo repositorio en GitHub
   - Sube todos los archivos del proyecto

2. **Conecta con Streamlit Cloud**
   - Ve a [share.streamlit.io](https://share.streamlit.io)
   - Inicia sesión con tu cuenta de GitHub
   - Click en "New app"
   - Selecciona tu repositorio y la rama `main`
   - El archivo principal debe ser `app.py`
   - Click en "Deploy"

3. **¡Listo!** Tu app estará disponible en una URL pública

### Opción 2: Deployment manual

Si prefieres otro servicio de hosting, puedes usar:
- **Heroku**: [Tutorial de despliegue](https://devcenter.heroku.com/articles/getting-started-with-python)
- **Railway**: [Tutorial de despliegue](https://docs.railway.app/deploy/deployments)
- **Google Cloud Run**: [Tutorial de despliegue](https://cloud.google.com/run/docs/quickstarts/deploy-container)

## 📁 Estructura del Proyecto

```
plataforma-capacitacion/
│
├── app.py                          # Aplicación principal
├── requirements.txt                # Dependencias de Python
├── README.md                       # Este archivo
├── .gitignore                      # Archivos ignorados por Git
│
└── data/                           # Carpeta de datos (se crea automáticamente)
    ├── usuarios_registrados.json   # Registro de usuarios
    ├── sesiones.json               # Sesiones de capacitación
    └── anuncios.json               # Anuncios publicados
```

## 🔧 Configuración

### Personalizar áreas y videos

Edita el diccionario `TRAINING_AREAS` en `app.py` (línea ~30):

```python
TRAINING_AREAS = {
    "Tu Área": [
        {
            "titulo": "Nombre del video",
            "url": "https://tu-sharepoint.com/video1",
            "duracion": "15 min"
        },
        # Agrega más videos...
    ],
    # Agrega más áreas...
}
```

### Cambiar el logo

Reemplaza la URL del logo en `app.py` (línea ~115):

```python
st.image("TU_URL_DE_LOGO", use_container_width=True)
```

## 👥 Uso

### Para Usuarios

1. Ingresa a la plataforma
2. Completa el formulario de registro
3. Serás redirigido a los videos de tu área
4. El cronómetro comenzará automáticamente
5. Accede a los videos haciendo click en "Ver Video"
6. Finaliza la sesión cuando termines

### Para Administradores

1. Click en "🔐 Modo Admin" en la barra lateral
2. Accede a tres paneles:
   - **📊 Registros**: Ver y descargar usuarios y sesiones
   - **📢 Anuncios**: Crear y gestionar anuncios
   - **📈 Estadísticas**: Ver métricas de capacitación

## 📊 Exportación de Datos

Los datos se exportan en formato CSV con la siguiente información:

**Usuarios:**
- Nombres, Apellidos, Cédula, Correo, Área, Fecha de registro

**Sesiones:**
- Cédula, Nombres, Apellidos, Área, Tiempo (segundos), Fecha

## 🔒 Seguridad y Privacidad

- Los datos se almacenan localmente en archivos JSON
- No hay autenticación por defecto (puedes agregarla con `streamlit-authenticator`)
- Recomendado: Agregar autenticación para el modo administrador en producción

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 💡 Soporte

¿Preguntas o problemas? Abre un [Issue](https://github.com/tu-usuario/plataforma-capacitacion/issues) en GitHub.

## 🚀 Próximas Mejoras

- [ ] Autenticación con contraseña para administradores
- [ ] Certificados de finalización automáticos
- [ ] Integración con base de datos (PostgreSQL/MySQL)
- [ ] Notificaciones por correo electrónico
- [ ] Dashboard con gráficos interactivos
- [ ] Sistema de evaluaciones/quizzes
- [ ] Integración directa con API de SharePoint

---

Desarrollado con ❤️ usando [Streamlit](https://streamlit.io)
