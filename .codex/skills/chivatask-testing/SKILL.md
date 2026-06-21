# Skill: ChivaTask Testing

## Objetivo

Prevenir regresiones funcionales, visuales, de sincronización y seguridad.

## Pruebas unitarias

- Clasificación y prioridad de tareas.
- Fechas límite y tareas vencidas.
- Tareas sin fecha.
- Snooze.
- Hash estable.
- Ajustes.
- Validación de URLs.
- Redacción de secretos.

## Pruebas de integración

- SQLite en memoria o archivo temporal.
- Migraciones.
- Upserts.
- Transacciones.
- WAL y concurrencia básica.
- Limpieza de caché.
- Credenciales mediante fake.
- Moodle mediante respuestas simuladas.

## Pruebas UI

- Primera ejecución.
- Login exitoso e inválido.
- Sin conexión con caché.
- Sin tareas.
- Muchas tareas.
- Filtros y búsqueda.
- Cambio de tema.
- Cierre a bandeja.
- Salida completa.
- Escalado DPI.

## Reglas

- Cada bug corregido agrega una prueba de regresión.
- No depender de Moodle real.
- No usar credenciales reales.
- No escribir en Credential Manager real.
- No escribir en la base de producción.
- Las pruebas deben funcionar sin conexión.
- No reducir cobertura del código modificado.

## Salida

Informar pruebas ejecutadas, resultado, cobertura del cambio y escenarios no cubiertos.
