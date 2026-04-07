# Render.com Deployment Guide — Hostel Information Management System

**Platform:** Render.com (free tier)
**Framework:** Django 5.2 / Python 3.12
**Database:** PostgreSQL (Render managed)
**Static files:** WhiteNoise
**Last updated:** 2026-04-07

Follow every step in order. Do not skip any step.

---

## Table of Contents

1. [Files created or changed](#1-files-created-or-changed)
2. [Prerequisites](#2-prerequisites)
3. [Service type to use on Render](#3-service-type-to-use-on-render)
4. [Connect GitHub to Render](#4-connect-github-to-render)
5. [Deploy using the Blueprint (render.yaml)](#5-deploy-using-the-blueprint-renderyaml)
6. [Set required environment variables](#6-set-required-environment-variables)
7. [Trigger first deploy and verify build](#7-trigger-first-deploy-and-verify-build)
8. [Migrations (automatic)](#8-migrations-automatic)
9. [Static files (automatic)](#9-static-files-automatic)
10. [Create the admin account](#10-create-the-admin-account)
11. [Media files and payment receipts](#11-media-files-and-payment-receipts)
12. [Custom domain (optional)](#12-custom-domain-optional)
13. [Subsequent deploys](#13-subsequent-deploys)
14. [Troubleshooting common failures](#14-troubleshooting-common-failures)

---

## 1. Files Created or Changed

The following deployment files were audited and updated. No application code
(models, views, templates, migrations) was modified.

| File | Change | Why |
|------|--------|-----|
| `settings.py` (root level) | **Deleted** | Stale duplicate; the real settings is `hostel_system/hostel_system/settings.py`. The root file was never loaded by Django (`DJANGO_SETTINGS_MODULE` resolves to the inner package) but caused confusion. |
| `Procfile` | **Fixed** | Removed the `release:` line — it is a Heroku-only convention silently ignored by Render. Updated gunicorn flags to `--workers 2 --threads 2`. |
| `render.yaml` | **Fixed** | Changed `DJANGO_CSRF_TRUSTED_ORIGINS` from a hardcoded, wrong URL to the wildcard `https://*.onrender.com`. Updated gunicorn flags to match. |
| `.env.example` | **Updated** | Added the three missing `DJANGO_SUPERUSER_*` variables that `build.sh` needs to create the admin account. Fixed `DJANGO_DEBUG` default for local dev. |
| `DEPLOYMENT_AUDIT.md` | **Rewritten** | Replaced the outdated audit with an accurate one. |
| `RENDER_DEPLOYMENT_GUIDE.md` | **Created** | This file. |

**Already correct — no changes:**
- `hostel_system/hostel_system/settings.py` — complete production config
- `requirements.txt` — all packages at correct versions
- `build.sh` — correct build sequence
- `runtime.txt` — pins Python 3.12.7
- `users/management/commands/ensure_superuser.py` — idempotent superuser creation

---

## 2. Prerequisites

Before you start:

- [ ] A free [Render.com](https://render.com) account
- [ ] A [GitHub](https://github.com) account
- [ ] This project pushed to a GitHub repository (public or private)

If you have not pushed yet:
```bash
git add .
git commit -m "Clean up deployment configuration"
git push origin main
```

---

## 3. Service Type to Use on Render

Use a **Web Service** (Python runtime) + **PostgreSQL database**.

Do NOT use:
- Static Site — wrong, Django is server-side rendered
- Background Worker — wrong, this is the main web process
- Docker — not needed, Render supports Python natively

`render.yaml` provisions both services automatically as a **Blueprint**.
You do not need to create anything in the dashboard manually.

---

## 4. Connect GitHub to Render

1. Log in to [render.com](https://render.com).
2. Click your avatar (top right) → **Account Settings** → **Git Providers** → **Connect** next to GitHub.
3. Authorize Render to access your repository.
4. Done. Render can now read your code and auto-deploy on push.

---

## 5. Deploy Using the Blueprint (render.yaml)

`render.yaml` is a **Render Blueprint** — a single file that defines the
PostgreSQL database and the web service together.

Steps:

1. In the Render dashboard click **New +** → **Blueprint**.
2. Select your GitHub repository from the list.
3. Render reads `render.yaml` and shows a preview:
   - 1 PostgreSQL database: `hostel-system-db` (free)
   - 1 Web Service: `hostel-system` (free, Python)
4. Click **Apply**.
5. Render starts provisioning. Do not wait — go to Step 6 immediately to set
   environment variables **before** the first build finishes.

> **Why use Blueprint instead of "New Web Service"?**
> Blueprint creates the database and links `DATABASE_URL` automatically.
> Manual creation requires you to copy-paste the connection string yourself.

---

## 6. Set Required Environment Variables

Go to: **Render Dashboard → hostel-system (web service) → Environment**

### Variables set automatically by render.yaml

You do not need to touch these — they are already in `render.yaml`:

| Variable | Value |
|----------|-------|
| `DJANGO_SECRET_KEY` | Auto-generated (random, unique per service) |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | `.onrender.com` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://*.onrender.com` |
| `DJANGO_SECURE_SSL_REDIRECT` | `True` |
| `DJANGO_SECURE_HSTS_SECONDS` | `3600` |
| `DATABASE_URL` | Auto-linked from `hostel-system-db` |
| `PYTHON_VERSION` | `3.12.7` |

### Variables you must set manually

These have `sync: false` in `render.yaml` — Render will not set them for you:

| Variable | What to put |
|----------|-------------|
| `DJANGO_SUPERUSER_USERNAME` | The login username for your Django admin account |
| `DJANGO_SUPERUSER_EMAIL` | Your email address |
| `DJANGO_SUPERUSER_PASSWORD` | A strong password (12+ characters, mix of types) |

To add them:
1. In the Render dashboard: **hostel-system → Environment → Add Environment Variable**
2. Add each of the three variables above.
3. Click **Save Changes**.

---

## 7. Trigger First Deploy and Verify Build

After saving environment variables:

1. Go to **hostel-system → Manual Deploy → Deploy latest commit**.
2. Click **View Logs** and watch the build output.

Expected output (in this order):

```
==> Running build command './build.sh'

Collecting pip ...
Successfully installed pip-...

Collecting Django==5.2.6
...
Successfully installed Django-5.2.6 gunicorn-23.0.0 whitenoise-6.8.2 psycopg2-binary-2.9.10 dj-database-url-2.3.0 pillow-11.1.0

128 static files copied to '/opt/render/project/src/staticfiles', ...

Operations to perform:
  Apply all migrations: admin, allocations, auth, contenttypes, hostels, payments, reports, sessions, users
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying users.0001_initial... OK
  ...

ensure_superuser: created superuser "your-username".

==> Build successful 🎉
==> Deploying...
==> Your service is live 🚀
```

3. Click the URL shown at the top of the service page.
4. You should see the hostel system home page with the Bootstrap UI.

---

## 8. Migrations (Automatic)

Migrations run automatically on every deploy via `build.sh`:

```bash
python manage.py migrate --noinput
```

- Django only applies migrations that have not been applied yet — safe to run repeatedly.
- If a migration fails, the build fails and Render keeps the previous live version.
- You never need to run `migrate` manually on Render.

---

## 9. Static Files (Automatic)

Static files are collected automatically on every deploy via `build.sh`:

```bash
python manage.py collectstatic --noinput
```

- Files are written to `staticfiles/` at build time.
- WhiteNoise serves them at `/static/` using compressed, cache-busted filenames.
- The `staticfiles/` directory is in `.gitignore` — it is regenerated each build.
- No separate static file server, CDN, or Nginx is required.

---

## 10. Create the Admin Account

If you set `DJANGO_SUPERUSER_*` variables in Step 6 before the build ran,
your admin account was created automatically.

To verify:
1. Go to `https://your-service.onrender.com/admin/`
2. Log in with the username and password you set.
3. You should see the Django admin interface.

**If you skipped Step 6:**
1. Go to the Render dashboard → **hostel-system → Environment** → add the three variables.
2. Click **Manual Deploy → Deploy latest commit**.
3. The next build will create the account.

`ensure_superuser` is idempotent — it never creates duplicates or overwrites
an existing password. Re-running it on every deploy is safe.

---

## 11. Media Files and Payment Receipts

**The problem:** Render's free web service uses an ephemeral filesystem.
Every deploy wipes all files written to disk.
Payment receipt uploads live in `MEDIA_ROOT/payment_receipts/`.
They will be deleted after every deployment.

### Option A — Render Persistent Disk (recommended, ~$0.25/GB/month)

1. In the Render dashboard: **hostel-system → Disks → Add Disk**
2. Settings:
   - Name: `media`
   - Mount Path: `/opt/render/project/src/media`
   - Size: 1 GB
3. Go to **Environment → Add Environment Variable**:
   ```
   DJANGO_MEDIA_ROOT = /opt/render/project/src/media
   ```
4. Trigger a new deploy. Uploaded files now survive deploys.

### Option B — Cloud Object Storage (best for production)

Move uploads to Cloudinary, AWS S3, or Backblaze B2 using `django-storages`.
This requires modifying `settings.py` and `requirements.txt` — outside the scope
of this guide. Cloudinary has a free tier suitable for small systems.

### Current status

For demos and development, the ephemeral filesystem is acceptable — receipts can
be re-uploaded. For a live student system, use Option A or B before going live.

---

## 12. Custom Domain (Optional)

To use `hostels.youruniversity.ac.ug` instead of `hostel-system-xxxx.onrender.com`:

1. Render dashboard → **hostel-system → Settings → Custom Domains → Add Custom Domain**.
2. Enter your domain. Render shows the DNS records to add.
3. Add those records in your domain registrar's DNS panel.
4. Wait for DNS propagation (minutes to hours).
5. Update environment variables in Render:
   ```
   DJANGO_ALLOWED_HOSTS=.onrender.com,hostels.youruniversity.ac.ug
   DJANGO_CSRF_TRUSTED_ORIGINS=https://*.onrender.com,https://hostels.youruniversity.ac.ug
   ```
6. Trigger a new deploy.

---

## 13. Subsequent Deploys

Every push to the `main` branch on GitHub triggers an automatic redeploy.
The sequence on each deploy:

1. `build.sh` runs: pip install, collectstatic, migrate, ensure_superuser
2. New gunicorn workers start
3. Traffic switches to new workers (zero-downtime if workers start cleanly)

To deploy manually: **hostel-system → Manual Deploy → Deploy latest commit**.

---

## 14. Troubleshooting Common Failures

### `./build.sh: Permission denied`
```bash
chmod +x build.sh
git add build.sh && git commit -m "Fix build.sh executable" && git push
```

### `ModuleNotFoundError` during build
A package is missing from `requirements.txt`. Check the build log for the exact
module name and add the corresponding package.

### `403 Forbidden` on every page
CSRF misconfiguration. Check:
- `DJANGO_CSRF_TRUSTED_ORIGINS` includes `https://*.onrender.com`
- You are accessing the site over `https://`, not `http://`

### `DisallowedHost at /`
`DJANGO_ALLOWED_HOSTS` does not cover your URL. Set it to `.onrender.com`
(leading dot = wildcard for all subdomains). `settings.py` also auto-appends
`RENDER_EXTERNAL_HOSTNAME` which Render injects at runtime.

### Infinite redirect loop (`ERR_TOO_MANY_REDIRECTS`)
`SECURE_PROXY_SSL_HEADER` is required because Render terminates TLS at its load
balancer and passes `X-Forwarded-Proto: https` to Django. Without it, Django
sees every request as HTTP and keeps redirecting to HTTPS.
This is already set in `settings.py`:
```python
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```
If you still see this error, check that `DJANGO_DEBUG` is `False` and that
`DJANGO_SECURE_SSL_REDIRECT` is `True`.

### Broken CSS / JS (static files 404)
1. Confirm `collectstatic` ran in the build log without errors.
2. Confirm `whitenoise.middleware.WhiteNoiseMiddleware` is in `MIDDLEWARE`.
3. Confirm `STATIC_ROOT = BASE_DIR / 'staticfiles'` is in settings.
4. Confirm `staticfiles/` is in `.gitignore` — if it is committed, old hashed
   filenames can conflict with the freshly collected ones.

### Uploaded payment receipts disappear after deploy
See [Section 11](#11-media-files-and-payment-receipts) — attach a persistent disk.

### No admin account / login fails at `/admin/`
The `DJANGO_SUPERUSER_*` env vars were not set before the build.
Add them in Render → Environment, then trigger a new deploy.

### `SSL connection has been closed unexpectedly` (intermittent)
The database idled and the connection went stale. This is transient on the free
tier — the next request will succeed. `conn_max_age=600` in the database config
minimises frequency. Not fixable without a paid plan.

### Free PostgreSQL database stopped working
Render's free Postgres expires after ~90 days. Create a new database in Render,
link it to the web service, and run `migrate` against it. Back up your data first.

---

## Summary Checklist

Use this as a final check before going live:

- [ ] Code pushed to `main` branch on GitHub
- [ ] Render Blueprint applied (`render.yaml`)
- [ ] `DJANGO_SUPERUSER_USERNAME` set in Render dashboard
- [ ] `DJANGO_SUPERUSER_EMAIL` set in Render dashboard
- [ ] `DJANGO_SUPERUSER_PASSWORD` set in Render dashboard
- [ ] First deploy completed successfully (check build logs)
- [ ] Home page loads at the Render URL
- [ ] HTTPS padlock shows in browser (no HTTP)
- [ ] Admin login works at `/admin/`
- [ ] Student registration and login works
- [ ] Test allocation can be created
- [ ] Test payment can be submitted
- [ ] Decision made on persistent disk for media uploads
- [ ] Calendar reminder set for free Postgres expiry (~90 days)
