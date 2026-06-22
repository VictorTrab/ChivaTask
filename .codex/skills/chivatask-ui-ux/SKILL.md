# Skill: ChivaTask UI/UX

## Objetivo

Mantener una interfaz PySide6 consistente, adaptable, accesible y adecuada para estudiantes.

## Skills especializadas

Para redisenos amplios, usar esta skill como base y derivar asi:

- `chivatask-modern-ui-audit`: antes de planear o cambiar varias pantallas.
- `chivatask-design-system`: al definir tokens, QSS, iconografia, claro/oscuro o identidad visual.
- `chivatask-qt-ui-implementation`: al implementar componentes PySide6, layouts y accesibilidad.
- `chivatask-visual-quality-gate`: antes de cerrar cualquier cambio UI/UX.

## Reglas visuales

- Reutilizar componentes antes de crear variantes nuevas.
- Centralizar colores, espaciado, tipografía, radios y estados visuales.
- No usar estilos inline dispersos.
- No depender solo del color para comunicar estado.
- Mantener textos en español correcto y con tildes.
- No mostrar códigos técnicos como mensaje principal.
- Explicar qué ocurrió y qué puede hacer el usuario.

## Layout

- Evitar anchos y alturas fijas salvo justificación técnica.
- Diseñar para 1366×768 y 1920×1080.
- Probar escalado de Windows al 125 % y 150 %.
- Implementar sidebar colapsable cuando el ancho sea limitado.
- Convertir paneles laterales rígidos en paneles adaptables, drawers o modales cuando corresponda.
- Actualizar layouts responsivos durante `resizeEvent`.

## Estados obligatorios

Cada vista dependiente de datos debe contemplar:

- loading
- success
- empty
- filtered-empty
- offline-cache
- recoverable-error
- blocking-error

## Accesibilidad

- Foco visible.
- Orden de tabulación lógico.
- Navegación completa por teclado.
- `accessibleName` en controles relevantes.
- Tooltips para iconos ambiguos.
- Áreas clicables adecuadas.
- Contraste suficiente.
- No comunicar urgencia únicamente mediante color.

## Rendimiento visual

- Aplicar debounce a búsquedas.
- No destruir y reconstruir listas completas por cada tecla.
- Preferir model/view para listas medianas o grandes.
- Actualizar solo elementos modificados.

## Criterio de aceptación

Toda mejora visual debe incluir evidencia de coherencia, accesibilidad, adaptación y ausencia de regresiones funcionales.

## Reglas absorbidas de diseno

- Disenar para productividad academica: rapido de escanear, claro, denso y sin decoracion pesada.
- Mantener superficies blancas, borde ligero, acentos verdes y estados de color claros.
- Tokens base: fondo `#F5F7FA`, superficie `#FFFFFF`, texto `#102033`, texto secundario `#64748B`, marca `#123F35`, accion `#16775F`, hover `#0F5F4A`, vencida `#D97706`, error `#DC2626`, info `#2563EB`.
- Fuente base: Segoe UI con fallback Arial.
- Botones: texto corto, radio 10px, icono Tabler si aporta claridad.
- Cards: radio 12-14px, borde `#D8E2EA`, sin sombras fuertes.
- Filtros: pills o segmented controls cuando hay pocas opciones.
- Tareas: lista agrupada por curso, chip de estado, fecha absoluta y relativa.
- Cursos: cards con progreso, estado y acciones alineadas; nunca scroll horizontal.
- Ajustes: filas tipo card con texto a la izquierda y control a la derecha.
- Brand SVG local bajo `src/resources/brand/`; no usar raster ni CDN para marca.
