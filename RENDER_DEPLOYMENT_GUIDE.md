# Render.com Deployment Guide
## Hostel Information Management System

Follow these steps in order. Do not skip any.

---

## 1. Files created or changed in this audit

| File | Status | Why it exists |
|------|--------|---------------|
| `hostel_system/hostel_system/settings.py` | **Rewritten** | The active Django settings file. Now reads every secret/host from environment variables, configures WhiteNoise, dj-database-url, CSRF trusted origins, and the Render TLS proxy header. |
| `requirements.txt` | **Rewritten** | Pinned to versions that actually exist on PyPI. Includes `gunicorn`, `whitenoise`, `psycopg2-binary`, `dj-database-url`, `pillow`. |
| `Procfile` | **Rewritten** | Render reads this as a fallback if `render.yaml` is absent. Format: `web: gunicorn hostel_system.wsgi:application --log-file -`. |
| `build.sh` | **Rewritten** | Runs on every deploy: `pip install`, `collectstatic`, `migrate`. |
| `runtime.txt` | **New** | Pins the Python interpreter to `3.12.7`. |
| `render.yaml` | **New** | Infrastructure-as-Code blueprint. One click provisions the web service, the Postgres database, and a 1 GB persistent media disk. |
| `.env.example` | **New** | Documents every environment variable the project reads. |
| `.gitignore` | **Expanded** | Now excludes `.env`, `staticfiles/`, `media/`, IDE files. |
| `DEPLOYMENT_AUDIT.md` | **New** | Full record of what was wrong and what was fixed. |
| `RENDER_DEPLOYMENT_GUIDE.md` | **New** | This file. |

**Files that must be deleted manually** (tracked in git, so `git rm` is required):

```bash
git rm settings.py urls.py wsgi.py asgi.py __init__.py
rm -rf hostel_system/.git              # stale nested .git inside the package
git commit -m "chore: remove duplicate Django package files at repo root"
```

These were orphan duplicates of the real files inside `hostel_system/hostel_system/`. They were never imported, but they confused every previous attempt at deployment because earlier edits landed on them instead of the active files. See `DEPLOYMENT_AUDIT.md` § 1 for the full explanation.

---

## 2. Environment variables to set in Render

If you use `render.yaml` (recommended), most of these are set automatically. The list below is the source of truth either way.

| Variable | Set automatically by `render.yaml`? | Value |
|----------|-------------------------------------|-------|
| `DJANGO_SECRET_KEY` | Yes — `generateValue: true` | (random) |
| `DJANGO_DEBUG` | Yes | `False` |
| `DJANGO_ALLOWED_HOSTS` | Yes | `.onrender.com` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Yes | `https://*.onrender.com` |
| `DJANGO_SECURE_SSL_REDIRECT` | Yes | `True` |
| `DJANGO_SECURE_HSTS_SECONDS` | Yes | `3600` |
| `DJANGO_MEDIA_ROOT` | Yes | `/opt/render/project/src/media` |
| `DATABASE_URL` | Yes — linked from `hostel-system-db` | (managed) |
| `PYTHON_VERSION` | Yes | `3.12.7` |

If you ever attach a custom domain (e.g. `hostels.example.ac.ug`), update `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` to include it.

---

## 3. Render service type

- **Web Service** (Python runtime). Not a Background Worker, not a Static Site.
- **Database**: Render's managed **PostgreSQL**.
- **Persistent disk**: 1 GB attached to the web service for `/media` uploads.

---

## 4. Create the PostgreSQL database

**Option A — Blueprint (recommended).** Skip to section 7; `render.yaml` provisions everything in one step.

**Option B — Manual.**
1. Render dashboard → **New +** → **PostgreSQL**.
2. Name: `hostel-system-db`. Region: same as your web service. Plan: Free.
3. Click **Create Database**. Wait for status = **Available**.
4. Open the database page → copy the **Internal Database URL** (starts with `postgres://`).
5. You will paste this into the web service as `DATABASE_URL` in section 5.

---

## 5. Build command

```bash
./build.sh
```

This runs `pip install -r requirements.txt`, `collectstatic --noinput`, and `migrate --noinput`.

> Make `build.sh` executable before pushing: `git update-index --chmod=+x build.sh && git commit -m "chore: mark build.sh executable"`

---

## 6. Start command

```bash
gunicorn hostel_system.wsgi:application --log-file -
```

This binds gunicorn to the port Render injects via `$PORT` automatically (gunicorn auto-detects it).

---

## 7. Connect GitHub and deploy

### Path A — Blueprint (one click, recommended)

1. Push the project to GitHub (`main` branch).
2. Render dashboard → **New +** → **Blueprint**.
3. Connect your GitHub account if you haven't already, and select the repo.
4. Render reads `render.yaml`, shows you a preview of "1 web service + 1 database + 1 disk".
5. Click **Apply**. Wait for the build to finish (3–6 minutes).

### Path B — Manual

1. Render dashboard → **New +** → **Web Service** → Connect GitHub repo.
2. Settings:
   - **Environment:** Python 3
   - **Region:** same as your database
   - **Branch:** `main`
   - **Build Command:** `./build.sh`
   - **Start Command:** `gunicorn hostel_system.wsgi:application --log-file -`
3. Add the environment variables from section 2.
4. Click **Advanced** → **Add Disk**: name `hostel-media`, mount path `/opt/render/project/src/media`, size 1 GB.
5. Click **Create Web Service**.

---

## 8. Deploy

Render builds automatically on every push to the configured branch. Your first build kicks off the moment you click **Apply** (Blueprint) or **Create Web Service** (manual).

Watch the build logs in real time. A successful build ends with:

```
==> Build successful
==> Starting service with 'gunicorn hostel_system.wsgi:application --log-file -'
==> Your service is live at https://hostel-system-XXXX.onrender.com
```

---

## 9. Run migrations

Migrations run automatically as part of `build.sh` (`python manage.py migrate --noinput`). You do not need to run them manually unless something fails.

If you ever need to run a one-off migration manually:

1. Render dashboard → web service → **Shell** tab.
2. Run:
   ```bash
   python manage.py migrate
   ```

To create the first superuser:
```bash
python manage.py createsuperuser
```

---

## 10. Collect static files

Also handled automatically by `build.sh` (`python manage.py collectstatic --noinput`). WhiteNoise serves them at runtime — no CDN required.

If you change static files locally and they don't appear after a deploy, hard-refresh (Ctrl+F5) — `CompressedManifestStaticFilesStorage` produces hashed filenames so the browser cache never lies.

---

## 11. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Build fails at `pip install` with `Could not find a version that satisfies the requirement gunicorn==25.1.0` | Old `requirements.txt` with non-existent versions | Pull the new `requirements.txt` from this audit |
| Build succeeds but page returns `DisallowedHost at /` | `DJANGO_ALLOWED_HOSTS` does not include the Render hostname | Add `.onrender.com` (or your custom domain) to the env var |
| Every form POST returns `403 CSRF verification failed` | `DJANGO_CSRF_TRUSTED_ORIGINS` missing or wrong | Set `https://*.onrender.com` (note the `https://` and the `*.`) |
| Browser shows infinite redirect / `ERR_TOO_MANY_REDIRECTS` | `SECURE_SSL_REDIRECT=True` without `SECURE_PROXY_SSL_HEADER` | Already fixed in `settings.py`. If you forked the file, ensure `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` is present |
| CSS / JS not loading, admin looks unstyled | WhiteNoise not installed, or `collectstatic` not run, or `STORAGES['staticfiles']` missing | Confirm `whitenoise` is in `requirements.txt`, the middleware is right after `SecurityMiddleware`, and `build.sh` runs `collectstatic` |
| `psycopg2.OperationalError: SSL connection required` | `dj_database_url` called without `ssl_require=True` | Already fixed in `settings.py` (`ssl_require=not DEBUG`) |
| `OperationalError: FATAL: database does not exist` | `DATABASE_URL` not linked or pointing at the wrong DB | Re-link the database in the env vars panel |
| Uploaded payment receipts disappear after a deploy | No persistent disk attached | Add the disk in `render.yaml` (already configured) **or** in the dashboard under Advanced → Disks |
| `OSError: [Errno 30] Read-only file system: '/opt/render/...'` when uploading | `DJANGO_MEDIA_ROOT` not set, so Django wrote into the read-only build dir | Set `DJANGO_MEDIA_ROOT=/opt/render/project/src/media` |
| Build hangs or times out | Free plan resource limits | Wait, then retry; consider upgrading to Starter |
| `ModuleNotFoundError: No module named 'hostel_system'` | The duplicate root `__init__.py` was pushed, turning the repo root into a package and shadowing the real one | Delete the duplicates as described in section 1 |

### How to read the logs
- **Build logs**: dashboard → web service → **Logs** tab → filter to "Build". Shows everything from `build.sh`.
- **Runtime logs**: same Logs tab, "Service" filter. Tracebacks from gunicorn workers appear here.
- **Database logs**: dashboard → database → **Logs**.

---

## 12. Local production smoke test (optional but recommended)

Before pushing, verify the new settings work with `DEBUG=False` locally:

```bash
# Windows PowerShell
$env:DJANGO_DEBUG="False"
$env:DJANGO_SECRET_KEY="any-long-random-string-for-local-test"
$env:DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1"
$env:DJANGO_CSRF_TRUSTED_ORIGINS="http://localhost:8000"
$env:DJANGO_SECURE_SSL_REDIRECT="False"   # disable for plain-HTTP local test
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py runserver
```

Visit http://localhost:8000 — every page should render with full styling, login should work, and POST forms should not 403.

---

## 13. Things to do after the first successful deploy

- [ ] Create a superuser via the **Shell** tab.
- [ ] Add at least one Hostel → Block → Room via Django admin or the Hostels UI.
- [ ] Test student registration end-to-end on the live URL.
- [ ] Test a payment submission with a file upload, then confirm the receipt survives a redeploy (proves the persistent disk is mounted).
- [ ] If you plan to scale beyond a single web instance, migrate `/media` to S3 or Cloudinary — a single persistent disk only attaches to one instance.
- [ ] Replace Render's `*.onrender.com` URL with a custom domain and update `DJANGO_ALLOWED_HOSTS` + `DJANGO_CSRF_TRUSTED_ORIGINS`.
- [ ] Raise `DJANGO_SECURE_HSTS_SECONDS` from `3600` to `31536000` (1 year) once you're confident HTTPS will stay on.
