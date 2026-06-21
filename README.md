# ChivaTask

App local para Windows que consulta el Moodle de UPH por API oficial, detecta asignaciones sin entrega registrada y muestra pendientes con notificaciones locales.

## Estado

MVP implementado con:

- Python 3.11+
- PySide6 / Qt Widgets
- Moodle Web Services (`moodle_mobile_app`)
- Windows Credential Manager via `keyring`
- SQLite local sin secretos
- Bandeja del sistema y sincronizacion en segundo plano
- Identidad visual ChivaTask con SVG locales y Tabler Icons

## Instalacion de desarrollo

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

## Ejecutar

```powershell
.\.venv\Scripts\Activate.ps1
python src\main.py
```

Tambien puedes abrir [src/main.py](C:/Users/User/Documents/PROYECTOS/ChivaTask/src/main.py) y ejecutarlo como archivo Python desde VS Code.

La primera ejecucion pide usuario y contrasena del campus. No se guardan en archivos: se almacenan con `keyring`, que en Windows usa Credential Manager.

## Pruebas

```powershell
python -m unittest discover -s tests -t .
```

## Empaque

No hay build configurado por ahora. No generar `.exe` salvo solicitud explicita.

## Seguridad

- No hardcodear credenciales.
- No subir bases SQLite reales.
- No registrar tokens, passwords ni HTML completo.
- Si compartiste tu contrasena durante pruebas, cambiala en el campus.
