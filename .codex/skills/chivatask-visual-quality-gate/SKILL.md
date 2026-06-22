---
name: chivatask-visual-quality-gate
description: Quality gate visual final para cambios UI/UX de ChivaTask. Usar antes de cerrar cualquier cambio de pantallas, login, componentes, QSS, modo oscuro, accesibilidad, responsive, capturas o pruebas visuales PySide6.
---

# ChivaTask Visual Quality Gate

## Objetivo

Impedir cierres prematuros de UI. Una mejora visual no esta terminada hasta tener evidencia de funcionamiento, coherencia, accesibilidad y ausencia de regresiones.

## Checklist obligatorio

1. Ejecutar `.\.venv\Scripts\python.exe -m unittest discover -s tests -t .`.
2. Ejecutar `.\.venv\Scripts\python.exe -m compileall -q src tests`.
3. Ejecutar `git diff --check`.
4. Revisar capturas o screenshot smoke de Inicio, Tareas, Cursos, Ajustes y Login.
5. Confirmar que no hay scroll horizontal global en 960x640.
6. Confirmar foco visible, orden de tabulacion y `accessibleName` en controles relevantes.
7. Confirmar textos en espanol correcto y sin mojibake visible.
8. Confirmar modo claro/oscuro en superficies, cards, inputs, menus, chips y modales.
9. Confirmar que no quedan estilos inline, recursos muertos ni componentes temporales.

## Salida

Reportar cambios visuales, pruebas ejecutadas, capturas revisadas, riesgos corregidos, riesgos residuales y recomendacion de aprobacion o rechazo.

## Referencia

Usar `references/visual-scorecard.md` para puntuar el cierre.
