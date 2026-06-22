# Qt Patterns

## Componentes esperados

- `NavItem`, `SearchField`, `SyncStatusPill`, `ProfileButton`
- `TaskRowCard`, `CourseCard`, `InfoCard`, `SettingsRow`
- `ToggleSwitch`, `ProgressRing`, `BaseModal`, `ConfirmModal`

## Antipatrones

- Texto con espacios para simular badges.
- Estilos inline repetidos en widgets.
- Botones icon-only sin tooltip o accessibleName.
- Anchos fijos que rompen 960x640.
- Bloques de texto concatenado donde deben existir cards o filas.
- Login creado despues de mostrar la ventana principal.

## Pruebas recomendadas

- Smoke build de componentes.
- Screenshot smoke no pixel-perfect.
- Resize 960x640, 1366x768, 1920x1080.
- Cambio claro/oscuro.
- Foco visible y navegacion por teclado.
