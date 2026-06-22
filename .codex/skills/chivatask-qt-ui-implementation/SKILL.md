---
name: chivatask-qt-ui-implementation
description: Guia de implementacion UI para ChivaTask en PySide6/Qt Widgets. Usar al modificar ventana principal, login, componentes, QSS, layouts responsive, QPainter, tarjetas, filtros, listas, detail panels, settings rows, accesibilidad o pruebas Qt.
---

# ChivaTask Qt UI Implementation

## Objetivo

Implementar mejoras UI sin deuda tecnica: componentes reutilizables, QSS centralizado, layouts adaptables y pruebas de regresion. No convertir `ventana_principal.py` en un monolito mayor.

## Orden de trabajo

1. Auditar pantalla y estado antes de editar.
2. Revisar si el cambio pertenece a componente existente.
3. Extraer componente si reduce duplicacion real o mejora testabilidad.
4. Mantener `presentation` libre de SQL, Moodle internals y reglas de token.
5. Verificar claro/oscuro, foco, tab order y responsive.

## Patrones Qt

- Usar `QFrame` para superficies, cards y filas.
- Usar `QPainter` para controles custom simples como toggle o progress ring.
- Usar `QSizePolicy`, stretch factors y `resizeEvent` para adaptacion.
- Usar `accessibleName`, tooltip y cursor en controles interactivos.
- Evitar `setStyleSheet()` inline salvo caso dinamico justificado.
- Evitar destruir/recrear listas por cada tecla; usar debounce minimo 200-300 ms.

## Login

El login es ventana previa de acceso, no modal superpuesto sobre la ventana principal. Si se cancela en arranque, la app termina; si se cancela tras logout, no se deja el sistema abierto sin sesion.

## Referencia

Leer `references/qt-patterns.md` para componentes esperados y antipatrones.
