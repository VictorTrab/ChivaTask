# ChivaTask UI Design Guide

Esta guia resume las reglas visuales del producto. Usa estas reglas antes de cambiar `presentation/qt`.

## Principios

- Disenar para productividad academica: rapido de escanear, claro y sin decoracion pesada.
- Seguir el ciclo `scan -> diagnose -> fix`: primero capturas, luego problemas concretos, luego cambios puntuales.
- Evitar interfaces genericas: exceso de gris, sombras pesadas, textos largos en botones y cards sin jerarquia.
- Mantener el look utilitario premium: superficies blancas, borde ligero, acentos verdes y estados de color claros.
- Proteger densidad: la app debe funcionar bien en 1366x768 sin scroll horizontal.

## Tokens

- Fondo: `#F5F7FA`.
- Superficie: `#FFFFFF`.
- Texto principal: `#102033`.
- Texto secundario: `#64748B`.
- Marca: `#123F35`.
- Accion: `#16775F`.
- Hover: `#0F5F4A`.
- Vencida: `#D97706`.
- Error: `#DC2626`.
- Info: `#2563EB`.
- Fuente base: Segoe UI con fallback Arial.

## Componentes

- Botones: texto corto, radio 10px, icono Tabler si la accion lo amerita.
- Cards: radio 12-14px, borde `#D8E2EA`, sin sombras fuertes.
- Filtros: usar pills o segmented controls, no combos cuando hay pocas opciones.
- Tareas: lista agrupada por curso, chip de estado, fecha absoluta y relativa.
- Cursos: cards con progreso, estado y acciones alineadas; nunca scroll horizontal.
- Ajustes: filas tipo card con texto a la izquierda y control a la derecha.

## Logo

- El isotipo debe leerse a 16, 24, 32 y 64 px.
- Concepto: birrete + campana + check, simple y reconocible.
- Usar SVG local bajo `src/uph_pendientes/resources/brand/`.
- No usar imagen raster ni CDN para marca.

## Checklist Visual

- Capturar Inicio, Tareas, Cursos y Ajustes en 1366x768 y 1920x1080.
- Confirmar que no hay texto como cuadros, texto cortado ni scroll horizontal.
- Confirmar que los botones caben y tienen nombres cortos.
- Confirmar que los paneles laterales no roban espacio al contenido principal.
- Confirmar que empty states se ven centrados y utiles.
