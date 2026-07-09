# Codespaces First PR

Use this route when you want to run checks without installing Python, Node,
Expo, FastAPI, local speech engines, generated audio, or private data on your
own computer.

Open a ready-to-configure cloud workspace:

`https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=1293331196`

The Codespaces devcontainer installs:

- Python 3.11
- Node.js 20
- backend test dependencies from `apps/api/requirements.txt`
- mobile dependencies with `npm ci` in `apps/mobile`

## Fast Checks

Backend:

```bash
cd apps/api
.venv/bin/python -m pytest
```

Mobile:

```bash
cd apps/mobile
npm run verify
```

Repository hygiene:

```bash
python3 scripts/check_public_tree.py
python3 scripts/verify_outreach_queue.py
```

## Run The App In Mock Mode

Backend mock API on port 8001:

```bash
apps/api/.venv/bin/uvicorn app.main:app --app-dir apps/api --host 0.0.0.0 --port 8001
```

Expo web mock mode:

```bash
cd apps/mobile
npm run web
```

Codespaces will offer forwarded ports for the FastAPI server, Expo web, and
Metro bundler.

## PR Checklist

- Keep one focused issue per PR.
- Link the issue with `Closes #ISSUE_NUMBER`.
- Name the check you ran in the PR body.
- Do not commit generated audio, archives, SQLite files, screenshots, local
  engines, private notes, secrets, or API keys.

If you want a browser-only contribution instead, use the
[five-minute first PR guide](FIVE_MINUTE_FIRST_PR.html) or the
[no-install first PR board](NO_INSTALL_FIRST_PRS.html).
