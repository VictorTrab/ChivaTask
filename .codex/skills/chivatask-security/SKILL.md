# Skill: ChivaTask Security

## Objetivo

Proteger credenciales, tokens, datos académicos, comunicación con Moodle y distribución.

## Credenciales

- Nunca guardar secretos en SQLite.
- Nunca incluir secretos en logs o excepciones.
- Tratar tokens como contraseñas.
- Preferir guardar token antes que contraseña.
- Pedir consentimiento explícito para recordar contraseña.
- Verificar que cerrar sesión elimine realmente los secretos.
- No usar `except Exception: pass`.

## Red

- HTTPS obligatorio.
- Allowlist de dominios Moodle.
- Validar toda URL antes de abrirla.
- Rechazar esquemas no permitidos.
- Validar redirecciones.
- Validar tipo y tamaño de respuesta.
- Redactar `wstoken`, usuario y contraseña en diagnósticos.
- No guardar payloads de autenticación.

## Datos locales

- Guardar datos en `%LOCALAPPDATA%/ChivaTask`.
- No usar carpetas compartidas.
- No incluir bases reales en Git, builds o reportes.
- Informar qué datos se eliminan al limpiar caché o cerrar sesión.
- Ofrecer eliminación completa de datos locales.
- Evitar mostrar rutas sensibles salvo necesidad.

## Dependencias

- Bloquear versiones.
- Ejecutar `pip-audit`.
- Ejecutar Bandit.
- Activar Dependabot.
- Revisar mantenimiento y licencias.
- No agregar dependencias para resolver tareas triviales.

## Release

- No distribuir bases, credenciales, logs o fixtures reales.
- Generar hash SHA-256.
- Firmar ejecutable e instalador cuando sea viable.

## Reglas absorbidas de privacidad

- SQLite es cache local; nunca guardar passwords ni tokens en SQLite.
- Credenciales y tokens viven en Windows Credential Manager mediante `keyring`.
- `Limpiar cache local` borra cursos, tareas, estado de notificaciones y estado de sincronizacion; conserva credenciales y ajustes.
- `Cerrar sesion local` borra credenciales, token y cache academica local; no borra Moodle.
- Diagnosticos sensibles deben pasar por `redact_secrets` o `SecretRedactionFilter`.
- Redactar `password`, `contrasena`, `contraseña`, `token`, `wstoken`, `username` y `usuario`.
- Moodle debe devolver JSON y no exceder el limite de tamano configurado antes de parsear.
- URLs externas solo por `SafeDesktopNavigator` con HTTPS y allowlist del campus.
