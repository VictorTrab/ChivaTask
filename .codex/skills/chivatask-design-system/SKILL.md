---
name: chivatask-design-system
description: Define y mantiene el sistema visual de ChivaTask para PySide6/Qt Widgets. Usar al crear tokens, QSS, componentes, paleta claro/oscuro, iconografia Tabler, tipografia, spacing, radios, estados, login profesional o coherencia visual entre pantallas.
---

# ChivaTask Design System

## Objetivo

Convertir decisiones visuales en reglas reutilizables para que todas las pantallas parezcan una sola aplicacion. No implementar estilos aislados sin revisar tokens y componentes existentes.

## Identidad

- Producto: gestor academico local para estudiantes.
- Tono: productivo, confiable, rapido de escanear, sin ruido decorativo.
- Visual: verde institucional, superficies limpias, bordes suaves, estados semanticos claros.
- Plataforma: Windows desktop con PySide6/Qt Widgets.

## Reglas

1. Centralizar colores, spacing, radios, tipografia y estados en `estilos.py`.
2. Usar Tabler SVG locales bajo `src/resources/icons/tabler/`.
3. Mantener modo claro/oscuro binario; no reintroducir densidad de informacion ni modo sistema salvo nueva decision explicita.
4. No usar gradientes, blur, sombras pesadas ni ornamentacion si no mejoran orientacion o jerarquia.
5. Evitar controles Qt nativos visualmente crudos: estilizar menus, combos, scrollbars, focus, disabled y selected.
6. Usar componentes reutilizables antes de crecer `ventana_principal.py`.

## Tokens base

Leer `references/design-tokens.md` antes de modificar QSS o crear variantes visuales.

## Salida esperada

Cuando se use esta skill, entregar una especificacion concreta: tokens afectados, componentes afectados, pantallas cubiertas, estados cubiertos y pruebas visuales necesarias.
