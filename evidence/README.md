# Evidence

Redacted outputs and screenshots from test runs. Reference each file by name from the
results record in `tests/`.

## Naming

Use `YYYY-MM-DD-short-description`, for example `2026-10-20-mfa-status-run1.json`.
Put each automated-check run in its own subfolder, such as `run1/`.

## Never commit here

- Raw `snapshot.json` files (they contain the full AWS account ID)
- Access keys, secret keys, session tokens, or passwords
- Unredacted screenshots or output with real account IDs, ARNs, usernames, or emails

## Before committing a file

- [ ] Account IDs, ARNs, and usernames replaced with placeholders (or masked)
- [ ] Console header, account alias, and email addresses blurred in screenshots
- [ ] Only controlled lab data
