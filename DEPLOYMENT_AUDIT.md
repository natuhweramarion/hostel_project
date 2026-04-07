# Deployment Audit — Hostel Information Management System

**Audit date:** 2026-04-07
**Target platform:** Render.com (free tier)
**Auditor:** Claude (Senior Django DevOps review)
**Session:** Full from-scratch inspection of all deployment-related files

This document records every deployment-related file found, the problems in each,
and the exact fixes applied. Read it alongside `RENDER_DEPLOYMENT_GUIDE.md`.

---

## 1. Project Structure (as found)

```
hostel_system/                    ← repo root / Django project root
├── hostel_system/                ← Django config package (the "inner" package)
│   ├── settings.py               ← ACTIVE settings file (loaded by manage.py)
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── settings.py                   ← ROOT-LEVEL DUPLICATE — never loaded, deleted
├── users/
│   └── management/commands/
│       └── ensure_superuser.py   ← custom management command (good)
├── allocations/
├── payments/
├── hostels/
├── reports/
├── templates/
├── static/
├── manage.py
├── Procfile
├── render.yaml
├── requirements.txt
├── runtime.txt
├── build.sh
└── .env.example
```

`manage.py` uses `DJANGO_SETTINGS_MODULE = 'hostel_system.settings'`, which Python
resolves to `hostel_system/hostel_system/settings.py` (the inner package). The
root-level `settings.py` is therefore **never imported by Django**.

---

## 2. Files Found — Status, Problems, and Resolutions

### 2.1 `settings.py` (root level) — DELETED

| | |
|---|---|
| **Status before** | Tracked in git |
| **Problem** | Orphan duplicate of `hostel_system/hostel_system/settings.py`. Never loaded by Django (`DJANGO_SETTINGS_MODULE` points to the inner package). Contained older, incomplete configuration — no `RENDER_EXTERNAL_HOSTNAME` handling, missing `conn_max_age` / `ssl_require`, used deprecated `STATICFILES_STORAGE` instead of Django 5.x `STORAGES` dict, missing `SECURE_PROXY_SSL_HEADER`. Had confusing production-only security settings with no `SECURE_SSL_REDIRECT` or `SECURE_HSTS_*`. |
| **Risk** | A developer could accidentally edit this file thinking they were changing settings, then see no effect in production. A future Django upgrade or CI step might pick it up and error. |
| **Fix applied** | **Deleted** the file. |

---

### 2.2 `hostel_system/hostel_system/settings.py` — CORRECT (no changes)

| | |
|---|---|
| **Status before** | Complete and production-ready |
| **Verified correct** | `SECRET_KEY` from env with insecure fallback for dev only; `DEBUG` from env defaulting `True`; `ALLOWED_HOSTS` from env with `RENDER_EXTERNAL_HOSTNAME` auto-appended; `CSRF_TRUSTED_ORIGINS` from env with `RENDER_EXTERNAL_HOSTNAME` auto-appended; `DATABASES` via `dj_database_url.config()` falling back to sqlite; `conn_max_age=600`, `ssl_require=not DEBUG`; WhiteNoise in middleware and `STORAGES`; `STATIC_ROOT`; `MEDIA_ROOT` from env; `SECURE_PROXY_SSL_HEADER` for Render's reverse proxy; full production security block inside `if not DEBUG:`. |
| **Fix applied** | None. |

---

### 2.3 `Procfile` — FIXED

| | |
|---|---|
| **Status before** | Two lines: `web:` and `release:` |
| **Problem** | The `release:` key is a **Heroku convention** that Render completely ignores. It ran `python manage.py migrate --noinput`, creating the false impression that migrations run on every Render deploy. On Render, migrations run in `build.sh`. Having the `release:` line causes confusion and could mislead a developer into thinking Render handles migrations that way. |
| **Fix applied** | Removed the `release:` line. Also upgraded the gunicorn flags to `--workers 2 --threads 2` to match the new `render.yaml` start command (consistent across both files). |

**Before:**
```
web: gunicorn hostel_system.wsgi:application --log-file -
release: python manage.py migrate --noinput
```

**After:**
```
web: gunicorn hostel_system.wsgi:application --workers 2 --threads 2 --log-file -
```

---

### 2.4 `render.yaml` — FIXED (2 changes)

| | |
|---|---|
| **Status before** | Structurally complete, minor issues |

**Problem 1 — Hardcoded `DJANGO_CSRF_TRUSTED_ORIGINS`:**
The value was `"https://hostel-system.onrender.com"`. Render assigns the actual
URL only after the first deploy; before that it may be
`hostel-system-abc1.onrender.com` or similar. A wrong `CSRF_TRUSTED_ORIGINS`
means every form POST (login, registration, payment submission) returns HTTP 403.

Fix: changed value to `"https://*.onrender.com"` (Django wildcard — supported
since Django 4.0). The `settings.py` also auto-appends `https://<RENDER_EXTERNAL_HOSTNAME>`
at runtime for belt-and-suspenders coverage.

**Problem 2 — gunicorn `startCommand` had no worker/thread flags:**
A single-worker gunicorn process on a free-tier instance can only handle one
concurrent request. Under even light load (admin + student simultaneously) this
causes visible slowdowns.

Fix: added `--workers 2 --threads 2`.

---

### 2.5 `requirements.txt` — CORRECT (no changes)

| Package | Version | Purpose |
|---------|---------|---------|
| Django | 5.2.6 | Web framework |
| gunicorn | 23.0.0 | WSGI production server |
| whitenoise | 6.8.2 | Static files in production |
| psycopg2-binary | 2.9.10 | PostgreSQL adapter |
| dj-database-url | 2.3.0 | `DATABASE_URL` parser |
| pillow | 11.1.0 | Image processing (payment receipt uploads) |

All versions exist on PyPI. No conflicts detected.

---

### 2.6 `build.sh` — CORRECT (no changes)

```bash
#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py ensure_superuser
```

Correct. Runs on the Render build container. `set -o errexit` ensures the build
fails fast if any command exits non-zero. `ensure_superuser` is idempotent (safe
to run on every deploy).

---

### 2.7 `runtime.txt` — CORRECT (no changes)

```
python-3.12.7
```

Matches `PYTHON_VERSION: 3.12.7` in `render.yaml`. Correct.

---

### 2.8 `.env.example` — UPDATED

| | |
|---|---|
| **Status before** | Existed but incomplete |
| **Problem** | Was missing the three `DJANGO_SUPERUSER_*` variables that `build.sh` needs to create the admin account. Without these documented, a developer would have no superuser and no way to log in after first deploy. Also defaulted `DJANGO_DEBUG=False` which is wrong for a local dev template — local dev needs `True`. |
| **Fix applied** | Added `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD` with clear comments. Changed `DJANGO_DEBUG` default to `True` for local dev. Improved all comments. |

---

### 2.9 `users/management/commands/ensure_superuser.py` — CORRECT (no changes)

Idempotent superuser creation from environment variables. Skips gracefully if
the env vars are not set or if the username already exists. Correct.

---

### 2.10 `manage.py` / `wsgi.py` / `asgi.py` — CORRECT (no changes)

All reference `DJANGO_SETTINGS_MODULE = 'hostel_system.settings'`, correctly
resolving to the inner package.

---

## 3. Required Environment Variables (complete list)

Determined by reading `settings.py` and grepping all apps for `os.environ`,
`os.getenv`, `settings.*`, and common third-party integration patterns
(no email gateway, no Stripe, no Cloudinary, no OpenAI, no Sentry).

| Variable | Required? | Set by | Purpose |
|----------|-----------|--------|---------|
| `DJANGO_SECRET_KEY` | **Yes** | `render.yaml` `generateValue: true` | Django signing key — must be unique per environment |
| `DJANGO_DEBUG` | **Yes** | `render.yaml` → `"False"` | Must be `False` in production |
| `DJANGO_ALLOWED_HOSTS` | **Yes** | `render.yaml` → `".onrender.com"` | Accepted hostnames |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | **Yes** | `render.yaml` → `"https://*.onrender.com"` | Trusted origins for CSRF form posts |
| `DATABASE_URL` | **Yes** | `render.yaml` `fromDatabase` | PostgreSQL connection string |
| `RENDER_EXTERNAL_HOSTNAME` | Auto | Injected by Render at runtime | Auto-added to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` in `settings.py` |
| `DJANGO_SUPERUSER_USERNAME` | Optional | Dashboard, manually | Admin account username |
| `DJANGO_SUPERUSER_EMAIL` | Optional | Dashboard, manually | Admin account email |
| `DJANGO_SUPERUSER_PASSWORD` | Optional | Dashboard, manually | Admin account password |
| `DJANGO_SECURE_SSL_REDIRECT` | Optional | `render.yaml` → `"True"` | Force HTTPS (default `True` in prod) |
| `DJANGO_SECURE_HSTS_SECONDS` | Optional | `render.yaml` → `"3600"` | HSTS max-age (default `0`) |
| `DJANGO_MEDIA_ROOT` | Optional | Not in `render.yaml` | Path for media uploads; defaults to `<project>/media` |
| `PYTHON_VERSION` | Optional | `render.yaml` + `runtime.txt` | Python interpreter version |

No email, payment gateway, object storage, or API keys are used in the codebase.

---

## 4. Static Files

- **Tool:** WhiteNoise (`whitenoise.middleware.WhiteNoiseMiddleware`)
- **Build step:** `python manage.py collectstatic --noinput` (in `build.sh`)
- **Output directory:** `BASE_DIR/staticfiles` (excluded from git via `.gitignore`)
- **Storage class:** `whitenoise.storage.CompressedManifestStaticFilesStorage` (gzip + cache-busting)
- **Serving:** WhiteNoise handles all `/static/` requests directly, no separate static server needed

**Status: Complete. No changes required.**

---

## 5. Media Files (payment receipt uploads)

- **Current setup:** Files written to `MEDIA_ROOT` (defaults to `<project>/media`)
- **Problem:** Render's free-tier and starter-tier web services use an **ephemeral filesystem**. Every new deploy wipes the filesystem. Payment receipts uploaded by students will be permanently deleted after each deployment.
- **Available solutions:**
  1. **Render Persistent Disk** (paid feature, ~$0.25/GB/month) — attach a disk, set `DJANGO_MEDIA_ROOT` to its mount path
  2. **Cloudinary / AWS S3 / Backblaze B2** — move uploads to object storage using `django-storages`
- **Current status:** Acceptable for demo/development. Not acceptable for a live system with real student payments.
- **Action required:** See `RENDER_DEPLOYMENT_GUIDE.md` Section 11 for details.

---

## 6. Database

| | |
|---|---|
| **Development** | SQLite (`db.sqlite3`), auto-fallback in `dj_database_url.config()` |
| **Production** | PostgreSQL 15 (Render managed, provisioned by `render.yaml`) |
| **Adapter** | `psycopg2-binary` (in `requirements.txt`) |
| **Connection pooling** | `conn_max_age=600` (persistent connections, 10-minute timeout) |
| **SSL** | `ssl_require=not DEBUG` — required by Render's managed Postgres |
| **Migrations** | Run in `build.sh` on every deploy (`migrate --noinput`) |

**Status: Complete. No changes required.**

---

## 7. Items Requiring Manual Attention

These cannot be fixed from code alone:

| # | Action | Why |
|---|--------|-----|
| 1 | Set `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD` in the Render dashboard before first deploy | Without these, `ensure_superuser` skips and there is no admin account |
| 2 | After deploy, update `DJANGO_CSRF_TRUSTED_ORIGINS` with your actual Render URL if needed | The wildcard `https://*.onrender.com` covers it, but you may want to restrict to your exact domain |
| 3 | Evaluate persistent disk or S3 for media uploads | Free-tier filesystem is ephemeral; uploaded payment receipts will be lost on every deploy |
| 4 | Raise `DJANGO_SECURE_HSTS_SECONDS` to `31536000` once the site is stable | Starting at `3600` (1 hour) is safe; raise after confirming HTTPS works correctly |
| 5 | Rotate the auto-generated `DJANGO_SECRET_KEY` if it is ever exposed | `render.yaml` generates it on first apply; it is stored only in the Render dashboard |

---

## 8. What Was NOT Changed

- All Django application code (views, models, forms, migrations, templates, URLs)
- `requirements.txt`
- `build.sh`
- `runtime.txt`
- `hostel_system/hostel_system/settings.py` (the active settings file)
- `users/management/commands/ensure_superuser.py`

The audit's scope was strictly deployment configuration files.
