# Skill: ChivaTask Architecture

## Objetivo

Proteger la arquitectura por capas y evitar que la interfaz se convierta en un módulo monolítico.

## Dependencias permitidas

### domain
- Reglas puras.
- Sin PySide6, requests, SQLite ni Windows.

### application
- Casos de uso y puertos.
- Depende de domain.
- No importa adaptadores concretos.

### infrastructure
- Implementa puertos.
- Contiene Moodle, SQLite, Windows y Credential Manager.

### presentation
- Consume casos de uso, controladores o puertos.
- No ejecuta SQL.
- No interpreta respuestas Moodle.
- No gestiona secretos directamente.

### app
- Composition root.
- Construye implementaciones y dependencias.

## Reglas

- Una vista no instancia gateways.
- Un repositorio no muestra mensajes.
- Un componente UI no ejecuta consultas.
- Las reglas de clasificación permanecen en domain.
- Cada integración externa requiere puerto.
- Dividir archivos mayores de 400–500 líneas cuando mezclen responsabilidades.
- Separar shell, views, controllers y components.
- Evitar dependencias circulares.
- Mantener interfaces pequeñas y específicas.

## Criterio de aceptación

Cada cambio debe indicar en qué capa vive y por qué.
