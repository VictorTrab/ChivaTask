# Reglas Para Agentes

Este proyecto usa una arquitectura modular. Preservala al agregar funcionalidades, corregir errores o reorganizar codigo.

## Prioridades Permanentes

1. No comprometer credenciales, tokens ni datos academicos.
2. No bloquear el hilo principal de Qt.
3. Preservar la arquitectura por capas.
4. Mantener util el cache offline cuando Moodle no este disponible.
5. Mantener la UI accesible, adaptable y consistente.
6. Agregar pruebas por cada bug corregido o comportamiento nuevo.
7. Medir antes de afirmar una mejora de rendimiento.

## Reglas De Planificacion

- Cargar y aplicar siempre la skill `interrogar` antes de crear planes, planes por fases, auditorias, propuestas de arquitectura o cuando el prompt sea ambiguo.
- Al usar `interrogar`, revisar primero el repositorio para responder lo que pueda descubrirse en codigo, pruebas, configuracion, `AGENTS.md` o skills locales.
- Preguntar antes de cerrar un plan si quedan decisiones abiertas de alcance, riesgo, prioridad, criterios de aceptacion o tradeoffs de implementacion.
- Aplicar las skills de calidad de ChivaTask segun el area cuando se haga trabajo amplio de calidad.

## Capas Del Proyecto

- `domain/`: reglas de negocio y modelos de dominio puros. No debe importar PySide6, requests, sqlite, keyring, APIs de Windows ni modulos de infraestructura.
- `application/`: casos de uso y puertos. Puede importar `domain/`, pero debe depender de interfaces de `application/puertos.py`, no de adaptadores concretos.
- `infrastructure/`: adaptadores concretos para Moodle, SQLite, Windows Credential Manager, notificaciones de escritorio y autoarranque.
- `presentation/`: UI Qt. Puede renderizar resultados de dominio y llamar casos de uso, pero no debe conocer nombres de funciones Moodle, esquema SQL, reglas de renovacion de token ni reglas de notificacion.
- `app/`: raiz de composicion. Conecta adaptadores con puertos.
- `src/main.py`: unico archivo de entrada ejecutable del proyecto.

## Reglas SOLID

- SRP: un modulo debe tener una razon clara para cambiar.
- DIP: el codigo de aplicacion depende de puertos; infraestructura los implementa.
- OCP: las nuevas integraciones se agregan como adaptadores sin reescribir casos de uso.
- ISP: mantener puertos pequenos y orientados a tareas.
- LSP: los fakes en pruebas deben sustituir a los adaptadores reales.

## Reglas Del Proyecto

- No guardar credenciales, tokens ni datos academicos personales en archivos del repo.
- No agregar web scraping en v1 salvo solicitud explicita.
- No generar `.exe` salvo solicitud explicita.
- Usar Tabler Icons como SVG locales bajo `src/resources/icons/tabler/`.
- Seguir las reglas de UI de este archivo y `chivatask-ui-ux` antes de cambiar Qt UI, marca, layout o estilos de componentes.
- Preferir componentes Qt reutilizables sobre estilos puntuales en `ventana_principal.py`.
- Mantener textos de UI lo bastante cortos para 1366x768 y evitar scroll horizontal en vistas principales.
- Agregar atribucion de terceros al incorporar assets externos.
- Mantener las pruebas cerca de las uniones de modulos: politicas de dominio, casos de uso, adaptadores de infraestructura y smoke tests de presentacion.
- Preferir ASCII en codigo y docs salvo que el archivo ya use intencionalmente acentos en espanol.

## Reglas De Producto Y UI

- Disenar para productividad academica: rapido de escanear, claro, denso y sin decoracion pesada.
- Usar el ciclo `scan -> diagnose -> fix`: capturar estado actual, identificar problemas concretos y hacer cambios enfocados.
- Mantener una apariencia utilitaria premium: superficies blancas, bordes suaves, acentos verdes, colores de estado claros y sin sombras pesadas.
- Preservar la paleta salvo cambio intencional del sistema de diseno: fondo `#F5F7FA`, superficie `#FFFFFF`, texto primario `#102033`, texto secundario `#64748B`, marca `#123F35`, accion `#16775F`, hover `#0F5F4A`, vencido `#D97706`, error `#DC2626`, info `#2563EB`.
- Usar Segoe UI con Arial como fallback.
- Los botones necesitan texto corto, radio de 10px e iconos Tabler cuando la accion se beneficie de un icono.
- Las tarjetas usan radio de 12-14px, borde `#D8E2EA` y sin sombras fuertes.
- Preferir pills o controles segmentados para conjuntos pequenos de opciones.
- Las listas de tareas se agrupan por curso y muestran chip de estado mas fecha absoluta o relativa.
- Las tarjetas de cursos muestran progreso, estado y acciones alineadas; nunca introducir scroll horizontal.
- Las filas de ajustes usan texto a la izquierda y control a la derecha.
- Los SVG de marca viven bajo `src/resources/brand/`; no usar raster ni CDN para branding.
- Antes de cerrar cambios de UI, revisar Inicio, Tareas, Cursos y Ajustes en 1366x768 y 1920x1080 cuando sea viable.

## Seguridad Y Datos Locales

- SQLite es solo cache local; no guardar passwords ni tokens alli.
- Credenciales y tokens deben usar Windows Credential Manager mediante `keyring`.
- `Limpiar cache local` elimina cursos, tareas, estado de notificaciones y estado de sync, pero conserva credenciales y ajustes.
- `Cerrar sesion local` elimina credenciales, token y cache academico; no debe insinuar que borra datos en Moodle.
- Los diagnosticos deben usar `redact_secrets` o `SecretRedactionFilter` antes de registrar o compartir valores sensibles.
- Redactar `password`, `contrasena`, `contraseña`, `token`, `wstoken`, `username` y `usuario`.
- Las respuestas de Moodle deben ser JSON y estar dentro del limite de tamano configurado antes de parsearse.
- Las URLs externas deben pasar por `SafeDesktopNavigator`, que exige HTTPS y allowlist del campus.
- Si Bandit o `pip-audit` no estan disponibles localmente, registrarlo como riesgo residual en vez de afirmar que la auditoria paso.

## Rendimiento Y Sincronizacion

- No afirmar mejoras de rendimiento sin evidencia de fixtures o medicion antes/despues.
- La consulta de estado Moodle debe usar rutas bulk o concurrencia limitada cuando sea posible; evitar bucles N+1 a nivel de aplicacion.
- Las consultas de estado de notificacion en SQLite deben ser bulk, no un `SELECT` por tarea.
- Las escrituras de sincronizacion exitosa deben agruparse en una transaccion del repositorio.
- Las conexiones SQLite deben intentar WAL, `busy_timeout`, foreign keys y `synchronous=NORMAL`, con fallback seguro para bases locales existentes.
- Las actualizaciones de busqueda/filtro en UI deben usar debounce de 200-300 ms.
- Filtrar 1000 tareas locales debe mantenerse por debajo de 200 ms en el fixture en memoria.

## Comandos De Calidad Y Release

- Pruebas estandar: `.\.venv\Scripts\python.exe -m unittest discover -s tests -t .`
- Compilacion: `.\.venv\Scripts\python.exe -m compileall -q src tests`
- Espacios en diff: `git diff --check`
- Auditoria de seguridad opcional si esta instalada: `.\.venv\Scripts\python.exe -m bandit -c pyproject.toml -r src`
- Auditoria de dependencias opcional si esta instalada: `.\.venv\Scripts\python.exe -m pip_audit`
- No construir instaladores ni ejecutables salvo solicitud explicita.

## Prohibiciones

- No hardcodear credenciales, tokens, passwords ni datos academicos reales.
- No registrar secretos, payloads de login, respuestas Moodle sensibles completas ni tokens sin redactar.
- No ejecutar llamadas de red, trabajo pesado de disco, consultas SQLite pesadas ni procesos largos en el hilo de UI.
- No usar `except Exception: pass`.
- No abrir URLs externas sin validacion.
- No duplicar componentes visuales sin necesidad clara.
- No agregar dependencias sin justificar necesidad, mantenimiento y seguridad.
- No declarar una tarea completa sin pruebas y revision de calidad.
- No hacer cambios visuales aislados que rompan consistencia, accesibilidad o escalado DPI.

## Reglas De Finalizacion

Antes de terminar cualquier implementacion, bug fix, refactor, commit, PR o preparacion de release:

1. Ejecutar las pruebas automatizadas relevantes.
2. Aplicar la skill de ChivaTask que corresponda al area modificada:
   - `chivatask-architecture` para limites de capas y direccion de dependencias.
   - `chivatask-performance` para sincronizacion, SQLite, Moodle, hilos o filtrado.
   - `chivatask-security` para credenciales, URLs, logging, datos locales, dependencias o artefactos de release.
   - `chivatask-ui-ux` para Qt UI, layout, estados, accesibilidad y consistencia visual.
   - `chivatask-testing` para estrategia de pruebas, fixtures y cobertura de regresion.
   - `chivatask-release` para empaquetado y trabajo de release.
3. Aplicar `chivatask-quality-gate`.
4. Reportar archivos cambiados, pruebas ejecutadas, riesgos encontrados, riesgos corregidos, riesgos residuales y trabajo pendiente.
