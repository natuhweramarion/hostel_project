# Deployment Audit — Hostel Information Management System

**Audit date:** 2026-04-08
**Target platform:** Render.com
**Auditor:** Claude (Senior Django DevOps review)

This document records the state of the project's deployment configuration **as found**, the problems identified, and the fixes applied. Read it alongside `RENDER_DEPLOYMENT_GUIDE.md`.

---

## 1. Repository layout — the root cause of most problems

The Django package is `hostel_system/hostel_system/` (contains `settings.py`, `urls.py`, `wsgi.py`, `asgi.py`, `__init__.py`). `manage.py` correctly references `hostel_system.settings`, which Python resolves to that inner package.

**However**, an exact set of duplicates of those same files exists at the project root:

```
hostel_system/                    <-- repo root
├── manage.py
├── settings.py        ← DUPLICATE (orphan, never imported)
├── urls.py            ← DUPLICATE (orphan, never imported)
├── wsgi.py            ← DUPLICATE (orphan, never imported)
├── asgi.py            ← DUPLICATE (orphan, never imported)
├── __init__.py        ← DUPLICATE (turns the repo root into a package, harmful)
└── hostel_system/     ← THE REAL Django package
    ├── settings.py    ← actually loaded by manage.py / wsgi.py
    ├── urls.py
    ├── wsgi.py
    ├── asgi.py
    └── .git/          ← STALE nested git repo (must be deleted)
```

All previous deployment edits (whitenoise middleware, `dj_database_url`, env-driven `SECRET_KEY` / `DEBUG` / `ALLOWED_HOSTS`, security headers) were applied to the **root duplicate** `settings.py` — i.e. the file that is **never imported**. The active inner `settings.py` was therefore still development-only and would have failed in production.

The duplicate files and the nested `.git/` directory must be removed. Their entire useful content has been folded into the active inner files.

---

## 2. Files found, problems, and resolutions

| # | File | Status before | Problems | Resolution |
|---|------|---------------|----------|------------|
| 1 | `settings.py` (root) | Tracked | Orphan duplicate; never loaded; held all the deployment edits | **Delete** (after porting content to inner settings) |
| 2 | `urls.py`, `wsgi.py`, `asgi.py`, `__init__.py` (root) | Tracked | Orphan duplicates; `__init__.py` at repo root accidentally turns the repo into a Python package | **Delete** |
| 3 | `hostel_system/hostel_system/.git/` | Untracked, on disk | Stale nested git repo from an earlier mis-init; confuses tools | **Delete** |
| 4 | `hostel_system/hostel_system/settings.py` (active) | Tracked | Hard-coded sqlite, no whitenoise, no env vars, no CSRF_TRUSTED_ORIGINS, no SECURE_PROXY_SSL_HEADER, missing STATIC_ROOT | **Rewritten** with full production config |
| 5 | `Procfile` | Tracked | Malformed: `web:gunicorn hostel_system.wsgi` (missing space, no `:application`, no log flag) | **Rewritten** to `web: gunicorn hostel_system.wsgi:application --log-file -` |
| 6 | `requirements.txt` | Tracked | Pinned to **non-existent** versions: `gunicorn==25.1.0`, `whitenoise==6.12.0`, `dj-database-url==3.1.2`, `psycopg2-binary==2.9.11`, `pillow==11.3.0`. `pip install` would fail outright. | **Rewritten** with verified released versions |
| 7 | `build.sh` | Tracked | Started with `##!/usr/bin/env bash` (broken shebang); did not upgrade pip | **Rewritten** |
| 8 | `runtime.txt` | Missing | Render needs to know which Python interpreter to use | **Created** (`python-3.12.7`) |
| 9 | `render.yaml` | Missing | No infrastructure-as-code; deployment was manual and undocumented | **Created** with web service + managed Postgres + persistent disk |
| 10 | `.env.example` | Missing | No documentation of required env vars | **Created** with every variable explained |
| 11 | `.gitignore` | Tracked, minimal | Did not exclude `.env`, `staticfiles/`, `media/`, IDE files | **Expanded** |
| 12 | `db.sqlite3` | Tracked (committed) | A live sqlite database is checked into the repo. Not a deployment blocker, but it ships dev data and credentials. | **Flag**: consider `git rm --cached db.sqlite3` after backing up sample data |

---

## 3. Django configuration gaps (active settings file, before fix)

| Gap | Why it matters on Render | Fix |
|-----|--------------------------|-----|
| `SECRET_KEY` hard-coded | Anyone with repo read access can forge sessions / signatures | Read from `DJANGO_SECRET_KEY` env var |
| `DEBUG = True` baked in | Leaks tracebacks, settings, source paths to attackers | Read from `DJANGO_DEBUG` env var, default `True` for dev only |
| `ALLOWED_HOSTS = []` | Django refuses to serve any request when `DEBUG=False` | Read from `DJANGO_ALLOWED_HOSTS`; auto-append `RENDER_EXTERNAL_HOSTNAME` |
| No `CSRF_TRUSTED_ORIGINS` | All POST forms (login, register, payments) would 403 | Read from `DJANGO_CSRF_TRUSTED_ORIGINS`; auto-append Render hostname |
| No `SECURE_PROXY_SSL_HEADER` | Django thinks every request is HTTP because Render terminates TLS at the proxy → infinite redirect loop with `SECURE_SSL_REDIRECT=True` | Set `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` |
| No `STATIC_ROOT` | `collectstatic` has nowhere to write → build fails | `STATIC_ROOT = BASE_DIR / 'staticfiles'` |
| No WhiteNoise middleware | Django won't serve `/static/` files when `DEBUG=False`, so the entire CSS/JS layer 404s | Insert `whitenoise.middleware.WhiteNoiseMiddleware` directly after `SecurityMiddleware`, set the `STORAGES` `staticfiles` backend |
| Hard-coded sqlite | Render's filesystem is ephemeral; data is wiped on every deploy | Use `dj_database_url.config()` reading `DATABASE_URL` |
| `MEDIA_ROOT` hard-coded inside source tree | Wiped on every deploy | Read from `DJANGO_MEDIA_ROOT`; mount a persistent disk in `render.yaml` |

All of the above are now fixed in `hostel_system/hostel_system/settings.py`.

---

## 4. Required environment variables (final list)

Detected by reading the new `settings.py` end-to-end. Nothing else in the project (`grep` for `os.environ`, `getenv`, `EMAIL_*`, `STRIPE_*`, `CLOUDINARY_*`, `OPENAI*`, `SENTRY*`, `TWILIO*`) reads any other variable.

| Variable | Required | Purpose |
|----------|----------|---------|
| `DJANGO_SECRET_KEY` | **Yes** | Django cryptographic signing key |
| `DJANGO_DEBUG` | **Yes** | Must be `False` in production |
| `DJANGO_ALLOWED_HOSTS` | **Yes** | Comma-separated host whitelist |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | **Yes** | Comma-separated `https://host` list for CSRF |
| `DATABASE_URL` | **Yes** (prod) | Postgres connection string from the Render database |
| `DJANGO_SECURE_SSL_REDIRECT` | Optional | Defaults to `True` in production; set `False` only to debug |
| `DJANGO_SECURE_HSTS_SECONDS` | Optional | HSTS max-age, defaults to `0` (disabled) |
| `DJANGO_MEDIA_ROOT` | Optional | Path to persistent disk mount for uploads |
| `RENDER_EXTERNAL_HOSTNAME` | Auto | Injected by Render at runtime; settings.py auto-trusts it |
| `PYTHON_VERSION` | Optional | `runtime.txt` already pins this; `render.yaml` also sets it |

---

## 5. Database requirements

- Production database: **PostgreSQL 15+** (Render's managed Postgres). Provisioned automatically by `render.yaml` (`databases:` section).
- `psycopg2-binary` is in `requirements.txt`.
- `dj-database-url` parses `DATABASE_URL` automatically; no manual host/port/user juggling.
- `conn_max_age=600` enables persistent connections; `ssl_require=True` (in production) is required by Render's managed Postgres.

---

## 6. Static & media handling

**Static files** (`/static/` — CSS, JS, admin assets):
- `collectstatic` runs in `build.sh`, writing into `BASE_DIR/staticfiles`.
- WhiteNoise serves them at runtime via `CompressedManifestStaticFilesStorage` (compressed + cache-busted).
- No CDN/object store needed for the current scale.

**Media files** (`/media/` — uploaded payment receipts, model name `Payment.receipt`):
- Render's standard filesystem is **ephemeral**: every deploy wipes it.
- `render.yaml` attaches a 1 GB persistent disk at `/opt/render/project/src/media` and points `DJANGO_MEDIA_ROOT` at it.
- For higher scale or multi-instance deployments you must move uploads to S3 / Cloudinary / Backblaze B2 — flagged in the deployment guide as a future task.

---

## 7. Items requiring manual attention (not fixable from code)

1. **Delete the duplicate root files** (`settings.py`, `urls.py`, `wsgi.py`, `asgi.py`, `__init__.py`). They are tracked in git, so use `git rm`. See the deployment guide for the exact command.
2. **Delete `hostel_system/hostel_system/.git/`** — stale nested repo on disk; not tracked.
3. **Decide whether to commit `db.sqlite3`.** It currently is. Recommended: `git rm --cached db.sqlite3`, then re-add to `.gitignore` (already done).
4. **Remove the Word lockfile** `~$oject_Proposal_HMS_Natuhwera_Marion.docx` (Office leftover).
5. **Generate a real `DJANGO_SECRET_KEY`** before the first deploy (or let `render.yaml`'s `generateValue: true` do it for you).

---

## 8. What was NOT changed

- No application code (views, models, forms, templates, urls in apps).
- No migrations.
- No business logic.
- No `CLAUDE.md` content.

The audit's scope was strictly deployment configuration.
