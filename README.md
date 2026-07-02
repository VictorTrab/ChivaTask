# ChivaTask

Aplicación de escritorio para Windows que consulta Moodle mediante su API oficial, identifica actividades académicas pendientes y muestra recordatorios locales.

![Marca de ChivaTask](src/resources/brand/chivatask-lockup.svg)

> El repositorio no incluye capturas de pantalla de la interfaz. Se muestra la imagen de marca existente para mantener el README sin archivos externos.

## Problema que resuelve

Revisar manualmente Moodle puede hacer que un estudiante pase por alto tareas, fechas de entrega o cambios en sus cursos. ChivaTask centraliza las actividades pendientes en una app local, conserva una caché mínima y ayuda a recordar tareas importantes sin guardar credenciales en archivos del proyecto.

## Funcionalidades principales

- Consulta de cursos y tareas mediante Moodle Web Services.
- Detección de actividades pendientes, vencidas y sin fecha.
- Sincronización en segundo plano para no bloquear la interfaz.
- Notificaciones locales y bandeja del sistema en Windows.
- Caché local en SQLite para consultar información reciente.
- Gestión de credenciales con Windows Credential Manager mediante `keyring`.
- Pruebas automatizadas para dominio, aplicación, infraestructura y presentación.

## Tecnologías

- Python 3.11+
- PySide6 / Qt Widgets
- SQLite
- Moodle Web Services
- Windows Credential Manager
- Git y GitHub

## Arquitectura resumida

El proyecto está organizado por capas:

- `domain/`: modelos, reglas de priorización y políticas de tareas.
- `application/`: casos de uso y puertos para coordinar sincronización, consultas y ajustes.
- `infrastructure/`: adaptadores concretos para Moodle, SQLite, credenciales, notificaciones y funciones de escritorio.
- `presentation/`: interfaz Qt, componentes visuales, bandeja del sistema y trabajadores de sincronización.
- `app/`: composición de dependencias y arranque de la aplicación.

## Seguridad y privacidad

- Las contraseñas y tokens no se guardan en archivos del repositorio.
- Las credenciales se almacenan con `keyring`; en Windows se integran con Windows Credential Manager.
- SQLite se usa como caché local y no debe contener contraseñas ni tokens.
- No se deben publicar bases reales, tokens, credenciales, datos de estudiantes ni respuestas completas de Moodle.
- La aplicación usa la API oficial de Moodle; no depende de scraping.

## Instalación de desarrollo

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

## Ejecución

```powershell
.\.venv\Scripts\Activate.ps1
python src\main.py
```

En la primera ejecución se solicitan credenciales del campus. La aplicación las almacena mediante el administrador de credenciales del sistema, no dentro del repositorio.

## Pruebas

```powershell
python -m unittest discover -s tests -t .
```

## Estado actual

MVP funcional para escritorio Windows. Incluye sincronización con Moodle, caché local, manejo seguro de credenciales, interfaz Qt, notificaciones locales y pruebas automatizadas.

## Limitaciones conocidas

- No hay instalador ni ejecutable empaquetado en el repositorio.
- El funcionamiento completo depende de credenciales válidas y disponibilidad de Moodle.
- Las notificaciones de escritorio están orientadas a Windows.
- El repositorio no incluye capturas de pantalla de la interfaz.

## Empaque

No hay build configurado por ahora. No generar `.exe` salvo solicitud explícita.
