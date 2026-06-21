# ADR 0001: Arquitectura modular local

## Estado

Aceptada.

## Contexto

ChivaTask es una app local para Windows que consulta Moodle API, detecta tareas pendientes y notifica al estudiante. La app maneja credenciales, cache local, UI de escritorio y llamadas de red; mezclar esas responsabilidades hace difícil probar y evolucionar el proyecto.

## Decisión

El proyecto usará arquitectura modular con estas capas:

- `domain`: modelos y reglas puras.
- `application`: casos de uso y ports.
- `infrastructure`: adapters concretos para Moodle, SQLite, Credential Manager y escritorio Windows.
- `presentation`: UI PySide6.
- `app`: composition root.

La fuente v1 será Moodle API oficial. SQLite será cache local mínima. Windows Credential Manager será el único almacén de secretos. La iconografía usará Tabler Icons en SVG local. No se generará ejecutable durante esta fase de arquitectura.

## Consecuencias

- La UI deja de ser el centro de la arquitectura.
- Los casos de uso se pueden probar con fakes sin red, SQLite real ni PySide6.
- Cambiar Moodle, persistencia o notificaciones requiere crear adapters, no reescribir reglas.
- Hay más archivos, pero con mejor localidad y seams más claros.
