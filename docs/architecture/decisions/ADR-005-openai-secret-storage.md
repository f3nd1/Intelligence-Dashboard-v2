# ADR-005: OpenAI secret storage

## Status
Accepted (2026-07-31)

## Context
The legacy Ask UCC asked each user for an OpenAI key in the browser and kept
it in session storage. A real key was later pasted into the AI Provider
field on UCC Intelligence Settings, in cleartext, on a saved and viewable
form. Both routes put a live credential somewhere it could be read, exported
or backed up.

## Options considered
1. Browser session storage (the legacy approach).
2. A Password field on UCC Intelligence Settings.
3. `site_config.json`, read server-side only.
4. An external secret manager.

## Decision
Option 3. The key lives in `site_config.json` under
`ucc_intelligence_ai_api_key` and is read only by `ai/client.py`.

## Rationale
Option 1 exposes the key to every user and to any script on the page.
Option 2 still puts it in the database, in version history, in backups and
in exports — a Password field obscures it in the UI, not at rest. Option 4
is correct at larger scale but adds infrastructure UCC does not run today.
Option 3 keeps the credential off every surface a user can reach, and Frappe
already treats site_config as the place for secrets.

## Consequences
- Rotating the key is a bench operation, not a form edit. `client.py` reads
  it fresh inside each call, so a rotation takes effect on the next request
  with no restart.
- The Settings DocType refuses to save any field holding a key-shaped value,
  so the mistake that prompted this cannot recur through a new field.
- The browser never receives the key; the model list is fetched server-side.

## Revisit triggers
UCC adopting a secret manager, or needing per-department keys.
