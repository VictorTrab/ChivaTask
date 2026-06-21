# Agent Architecture Rules

This project uses a modular architecture. Preserve it when adding features or fixing bugs.

## Module Layers

- `domain/`: pure business rules and domain models. It must not import PySide6, requests, sqlite, keyring, Windows APIs, or infrastructure modules.
- `application/`: use cases and ports. It may import `domain/`, but it must depend on interfaces from `application/puertos.py`, not concrete adapters.
- `infrastructure/`: concrete adapters for Moodle, SQLite, Windows Credential Manager, desktop notifications, and autostart.
- `presentation/`: Qt UI only. It may render domain results and call application use cases, but it must not know Moodle function names, SQL schema details, token renewal rules, or notification decision rules.
- `app/`: composition root. It wires adapters to ports.

## SOLID Rules

- SRP: one module should have one clear reason to change.
- DIP: application code depends on ports; infrastructure implements them.
- OCP: new integrations should be added as adapters without rewriting use cases.
- ISP: keep ports narrow and task-oriented.
- LSP: fakes in tests must be substitutable for real adapters.

## Project Rules

- Do not store credentials, tokens, or personal academic data in repo files.
- Do not add web scraping in v1 unless explicitly requested.
- Do not generate a `.exe` unless explicitly requested.
- Use Tabler Icons as local SVG files under `src/uph_pendientes/resources/icons/tabler/`.
- Follow `docs/ui/DESIGN.md` before changing Qt UI, branding, layout, or component styling.
- Prefer reusable Qt components over one-off widget styling in `ventana_principal.py`.
- Keep UI text short enough for 1366x768 and avoid horizontal scroll in main views.
- Add third-party attribution when adding external assets.
- Keep tests close to module seams: domain policies, application use cases, infrastructure adapters, and presentation smoke tests.
- Prefer ASCII in source and docs unless the existing file intentionally uses Spanish accents.
