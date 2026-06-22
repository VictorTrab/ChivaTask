---
name: chivatask-modern-ui-audit
description: Auditoria profunda de UI/UX moderna para ChivaTask. Usar cuando se revise, planifique o mejore visualmente Inicio, Tareas, Cursos, Ajustes, Login, onboarding, bandeja, menus, estados, accesibilidad, responsive o coherencia visual PySide6/Qt Widgets.
---

# ChivaTask Modern UI Audit

## Objetivo

Auditar la interfaz real antes de proponer o implementar redisenos. La salida debe ser accionable: hallazgos P0/P1/P2 con evidencia, pantalla afectada, riesgo UX y criterio de aceptacion.

## Flujo

1. Leer `AGENTS.md`, `chivatask-ui-ux` y, si el trabajo es amplio, aplicar `interrogar` antes de cerrar plan.
2. Inspeccionar las vistas reales: Inicio, Tareas, Cursos, Ajustes, Login, onboarding, menus, perfil, bandeja/demo y modales.
3. Revisar capturas existentes del usuario y generar capturas nuevas cuando sea viable.
4. Comparar contra la identidad objetivo: app academica productiva, clara, compacta, profesional, verde institucional, sin decoracion gratuita.
5. Clasificar hallazgos:
   - P0: bloquea acceso, lectura, navegacion, seguridad percibida o flujo critico.
   - P1: reduce confianza, claridad, consistencia o eficiencia diaria.
   - P2: pulido visual, microcopy, ritmo, alineacion o detalle no bloqueante.
6. Entregar plan por pantallas con criterios medibles.

## Evidencia obligatoria

- Usar archivos y componentes concretos cuando sea posible.
- Incluir capturas 1366x768 y 1920x1080 si la plataforma lo permite.
- Si `QT_QPA_PLATFORM=offscreen` renderiza fuentes como cuadros, declararlo como limitacion y usar la captura solo como smoke no pixel-perfect.
- No afirmar que una pantalla esta bien sin revisar estados vacio, loading, error, offline-cache y modo oscuro.

## Referencia

Leer `references/screen-checklist.md` para la matriz minima de pantallas, estados y criterios.
