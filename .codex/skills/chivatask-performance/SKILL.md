# Skill: ChivaTask Performance

## Objetivo

Evitar bloqueos, trabajo duplicado y sincronizaciones innecesariamente costosas.

## Hilo principal

Nunca ejecutar directamente en el hilo de Qt:

- HTTP.
- Consultas SQLite pesadas.
- Lectura o escritura intensiva.
- Procesamiento masivo.
- Generación de reportes.
- Esperas o reintentos.

## Moodle

- Detectar y eliminar patrones N+1.
- Reutilizar `requests.Session`.
- Usar timeout de conexión y lectura separados.
- Reintentar solo fallos transitorios.
- No reintentar credenciales inválidas.
- Implementar progreso visible.
- Permitir cancelación segura.
- Evitar consultar de nuevo datos que no pueden haber cambiado.
- Preferir endpoints masivos o sincronización incremental.

## SQLite

- Activar `PRAGMA journal_mode=WAL`.
- Activar `PRAGMA busy_timeout`.
- Activar `PRAGMA foreign_keys=ON`.
- Usar `PRAGMA synchronous=NORMAL` cuando sea apropiado.
- Agrupar una sincronización en una transacción.
- Evitar un `SELECT` por elemento.
- Usar `executemany`.
- Crear índices solo según consultas reales.
- Marcar o limpiar registros no devueltos tras una sincronización exitosa.

## UI

- Debounce de 200–300 ms para búsquedas.
- Preferir `QAbstractItemModel` y `QSortFilterProxyModel`.
- No recrear cientos de widgets en cada filtro.
- Cargar detalles secundarios bajo demanda.

## Presupuestos recomendados

- Inicio con caché: menor a 1.5 s.
- Respuesta al escribir: menor a 100 ms.
- Aplicación de filtro: menor a 200 ms.
- Navegación entre vistas: menor a 150 ms.
- Toda operación mayor a 300 ms debe mostrar progreso o estado.

## Evidencia

No afirmar mejora sin medición antes y después.

## Evidencia y presupuestos absorbidos

- Medir antes/despues con fixtures; no afirmar mejoras sin datos.
- Fixture recomendado: 3 cursos x 20 tareas compara legacy 60 estados individuales contra actual 1 llamada bulk.
- `notification_state` debe leerse una sola vez para calcular cambios.
- La sincronizacion exitosa agrupa escrituras en transaccion.
- Filtrar 1000 tareas locales debe quedar bajo 200 ms en fixture en memoria.
- Moodle real puede diferir; registrar riesgo si solo hay fixtures.
