# Skill: ChivaTask Release

## Objetivo

Preparar builds reproducibles, instalables y verificables.

## Checklist

- Entorno limpio.
- Dependencias bloqueadas.
- Pruebas aprobadas.
- Auditoría de seguridad aprobada.
- Sin bases SQLite reales.
- Sin credenciales ni logs sensibles.
- Recursos incluidos.
- Primera ejecución probada.
- Actualización sobre versión anterior probada.
- Desinstalación probada.
- Inicio con Windows probado.
- Cierre a bandeja probado.
- Versión visible coincide con paquete.
- Hash SHA-256 generado.
- Notas de versión preparadas.

## Build

- PyInstaller reproducible.
- Inno Setup configurado.
- Verificar rutas en Windows.
- Evitar archivos temporales en el paquete.
- Firmar ejecutable e instalador cuando sea posible.

## Salida

Entregar artefactos, hash, versión, pruebas realizadas y limitaciones conocidas.

## Comandos de release local absorbidos

- Tests: `.\.venv\Scripts\python.exe -m unittest discover -s tests -t .`.
- Compilacion: `.\.venv\Scripts\python.exe -m compileall -q src tests`.
- Whitespace: `git diff --check`.
- Bandit si esta instalado: `.\.venv\Scripts\python.exe -m bandit -c pyproject.toml -r src`.
- pip-audit si esta instalado: `.\.venv\Scripts\python.exe -m pip_audit`.
- No generar `.exe` ni instalador salvo solicitud explicita.
- Antes de empaquetar, confirmar que no se incluyen bases SQLite reales, credenciales, tokens ni logs sensibles.
