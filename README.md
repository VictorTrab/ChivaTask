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
python -m uph_pendientes
```

La primera ejecucion pide usuario y contrasena del campus. No se guardan en archivos: se almacenan con `keyring`, que en Windows usa Credential Manager.

## VS Code

El proyecto incluye configuracion en `.vscode/` para usar el entorno local `.venv`.

Atajos utiles:

- Debug: selecciona `ChivaTask` en Run and Debug.
- Tarea: `Terminal > Run Task > Run app`.
- Tests: `Terminal > Run Task > Run tests`.
- Build: `Terminal > Run Task > Build exe`.

## Pruebas

```powershell
python -m unittest discover -s tests
```

## Empaque

Build base con PyInstaller:

```powershell
pyinstaller packaging\uph-pendientes.spec
```

Installer recomendado: Inno Setup usando `packaging\installer.iss` despues de generar el build de PyInstaller.

## Seguridad

- No hardcodear credenciales.
- No subir bases SQLite reales.
- No registrar tokens, passwords ni HTML completo.
- Si compartiste tu contrasena durante pruebas, cambiala en el campus.
