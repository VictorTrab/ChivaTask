# Skill: ChivaTask Quality Gate

## Objetivo

Actuar como revisión final obligatoria antes de dar por terminada una tarea.

## Aplicar cuando

- Se complete una funcionalidad.
- Se corrija un bug.
- Se modifique más de un módulo.
- Se prepare un commit, PR o release.
- Se realice una refactorización.

## Checklist obligatorio

1. Ejecutar pruebas automatizadas.
2. Revisar lint, formato, imports y tipado.
3. Buscar llamadas HTTP, SQLite, disco o procesamiento pesado en el hilo principal.
4. Buscar secretos, tokens, contraseñas y datos académicos en código, logs y fixtures.
5. Buscar patrones N+1 en Moodle y SQLite.
6. Verificar estados `loading`, `success`, `empty`, `filtered-empty`, `offline-cache` y `error`.
7. Revisar navegación por teclado, foco visible, contraste y escalado DPI.
8. Confirmar que `presentation` no contiene SQL ni interpretación de respuestas Moodle.
9. Confirmar que cada bug corregido tenga prueba de regresión.
10. Comparar comportamiento anterior y nuevo para detectar regresiones.

## Salida obligatoria

Entregar:

- Cambios realizados.
- Pruebas ejecutadas y resultado.
- Riesgos encontrados.
- Riesgos corregidos.
- Riesgos residuales.
- Recomendación de aprobación o rechazo.

Una tarea no se aprueba solo porque funcione. Debe ser segura, fluida, comprensible, comprobable y coherente con la arquitectura.

## Criterios absorbidos de cierre

- Ejecutar `unittest discover -s tests -t .`, `compileall -q src tests` y `git diff --check`.
- Si `pytest`, Bandit o `pip-audit` no estan instalados, declararlo como riesgo residual; no marcarlo aprobado.
- Verificar que no hay `webbrowser`/`os.startfile` directos en presentation para URLs externas.
- Verificar que domain/application no importan PySide6, requests, sqlite3, keyring, infrastructure ni presentation.
- Verificar que `prompts/`, `build/`, `dist/`, `*.egg-info` y caches generadas no queden como dependencia del flujo normal.
