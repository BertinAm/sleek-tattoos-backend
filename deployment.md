# Deployment

Target architecture (~$35–39/year, under the $50 budget):

| Piece | Where | Cost |
|---|---|---|
| Domain `sleektattoos.com` | Namecheap | ~$11 first year, ~$15–19/yr renewal |
| Frontend (Next.js) | Cloudflare Pages, free tier | $0 |
| Backend (this Django app) | Namecheap Stellar shared hosting | ~$24–28/yr |
| Database | MySQL, included with Stellar | $0 |

Renewal creeps to ~$39–47/yr from year two (domain renewal is pricier than
the first-year promo rate) — worth a calendar reminder now.

---

## 0. Decide the Next.js rendering mode FIRST

This determines the Cloudflare Pages build config, and guessing wrong is
annoying to discover mid-build. Two options:

- **Static export** (`next.config.js` → `output: 'export'`, build command
  `next build`, output dir `out`) — if the frontend is mostly static content
  plus client-side `fetch()` calls to this API. **This is the fit for the
  current frontend**: every page in `app/` is a client component
  (`"use client"`) that fetches data in `useEffect`, not via Next's
  server-side data fetching. `lib/store.js` now makes real `fetch()` calls
  to the Django API instead of localStorage (see `memory.md`), so static
  export should work as-is with zero further frontend architecture changes.
- **True SSR** (per-request dynamic rendering) — only needed if a page must
  render differently per-request on the server (e.g. server-side
  personalization, auth-gated SSR pages). Requires the
  `@opennextjs/cloudflare` adapter and deploying via Workers-with-Static-Assets
  instead of classic Pages, since that's where Cloudflare's roadmap is headed.

**Recommendation for this project: static export.** Nothing in the current
page set needs per-request server rendering — the admin panel is
client-side-gated (JWT in the browser), and the public site is the same for
every visitor until client-side JS fetches personalized data (booking
status, chat history), which is exactly what client-side `fetch()` handles.
Revisit this only if a real SSR requirement shows up later.

---

## 1. Domain & DNS (Namecheap + Cloudflare)

1. Register `sleektattoos.com` at Namecheap.
2. In Cloudflare Pages, add `sleektattoos.com` as a custom domain for the
   frontend project — Cloudflare's dashboard walks through either (a)
   pointing the domain's nameservers at Cloudflare, or (b) adding a CNAME,
   depending on whether Cloudflare is also your DNS host. Follow whichever
   the Pages custom-domain screen shows for your setup.
3. Create an `api` subdomain (`api.sleektattoos.com`) pointed at the Stellar
   hosting account — this is an A record (or CNAME, per Stellar's docs) set
   up from Namecheap's DNS (or Cloudflare's, if Cloudflare is the DNS host
   for the whole domain — either works, just be consistent).

---

## 2. Backend: Namecheap Stellar (cPanel)

### 2.1 Before anything else: confirm SSH is enabled

This is the one dependency that can quietly block the whole deploy pipeline
— cPanel Git Version Control and the Python App's `pip`/`manage.py` steps
generally don't need SSH, but you'll want it for one-off debugging
(tailing logs, running a stray migration, checking why Passenger won't
restart). Check cPanel → SSH Access before building the rest around it. If
it's off, most Stellar plans let you enable it from the same page or via a
support ticket.

### 2.2 Set up the Python App

1. cPanel → **Setup Python App**.
2. Create a new app:
   - **Python version**: pick the newest available 3.x.
   - **Application root**: e.g. `api.sleektattoos.com` (this becomes
     `<APP_PATH>` in `.cpanel.yml`).
   - **Application URL**: the `api` subdomain from step 1.
   - **Application startup file**: `passenger_wsgi.py` (already in this repo).
   - **Application Entry point**: `application`.
3. cPanel shows you the exact virtualenv path and an `pip install` command
   box on this screen — note the virtualenv path, you need it for
   `.cpanel.yml`.

### 2.3 Set up MySQL (not Postgres — Stellar's included DB is MySQL)

1. cPanel → **MySQL Databases** → create a database and a database user,
   grant the user ALL PRIVILEGES on that database.
2. Note the three values cPanel gives you: database name, username,
   password (these are usually prefixed with your cPanel username, e.g.
   `cpuser_sleektattoos`).
3. Set `DATABASE_URL` in the app's `.env` (see 2.5):
   ```
   DATABASE_URL=mysql://DB_USER:DB_PASSWORD@localhost:3306/DB_NAME
   ```

**Verify `mysqlclient` installs cleanly before building anything else on top
of it.** It needs a C compiler and MySQL client headers; shared hosting
occasionally chokes on heavier dependency trees. From the app's virtualenv:
```bash
source /home/<CPANEL_USERNAME>/virtualenv/<APP_PATH>/<PYTHON_VERSION>/bin/activate
pip install mysqlclient
```
If that fails, swap to `PyMySQL` instead (pure Python, no compiler needed):
```bash
pip install PyMySQL
```
and add this to the top of `config/settings.py`:
```python
import pymysql
pymysql.install_as_MySQLdb()
```
Test this on the actual server **before** wiring the rest of the deploy
pipeline around whichever driver you land on.

### 2.4 Push-to-deploy via cPanel Git Version Control

1. cPanel → **Git™ Version Control** → create a repository, pointing at
   this `backend/` directory (either push directly from your local machine
   to the cPanel-hosted repo, or connect it to your GitHub remote —
   whichever cPanel's version supports on your Stellar plan).
2. `.cpanel.yml` (already in this repo) runs automatically on every deploy
   cPanel triggers. **Fill in the placeholders first** —
   `<CPANEL_USERNAME>`, `<APP_PATH>`, `<PYTHON_VERSION>` — using the exact
   values from the "Setup Python App" screen (2.2).
3. What it does, in order: copies files to the live app directory, installs
   `requirements.txt` into the cPanel-managed virtualenv, runs `migrate`,
   runs `collectstatic`, then **touches `tmp/restart.txt`**. That last step
   is the one people forget — Passenger only reloads the app when that
   file's mtime changes. Skip it and the deploy "succeeds" but the old code
   keeps serving every request. `.cpanel.yml` already includes it; just
   don't remove it if you customize the file.

### 2.5 Environment variables

Stellar's Python App interface has an "Environment variables" section on
the same "Setup Python App" screen — set them there rather than committing
a `.env` file to the server (never commit `.env`; it's gitignored). At
minimum, in production:

```
DJANGO_SECRET_KEY=<generate a new one — do NOT reuse the local dev key>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=api.sleektattoos.com
DATABASE_URL=mysql://DB_USER:DB_PASSWORD@localhost:3306/DB_NAME
CORS_ALLOWED_ORIGINS=https://sleektattoos.com,https://www.sleektattoos.com
GOOGLE_SERVICE_ACCOUNT_FILE=/home/<CPANEL_USERNAME>/credentials/sleektattoos-calendar.json
GOOGLE_CALENDAR_OWNER_EMAIL=<owner's Gmail address>
```

Generate a fresh secret key (don't reuse the one in your local `.env`):
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2.6 Where the Google service account key lives

**This is the one secret in this whole stack worth being paranoid about** —
it has calendar-write access. Upload the JSON key file via cPanel File
Manager (or `scp` over the SSH you confirmed in 2.1) to somewhere **outside
`public_html` and outside the git repo** — e.g.
`/home/<CPANEL_USERNAME>/credentials/sleektattoos-calendar.json`. Point
`GOOGLE_SERVICE_ACCOUNT_FILE` at that path. Never commit it, never put it
anywhere web-accessible.

### 2.7 CORS / frontend trust

`sleektattoos.com` and `api.sleektattoos.com` are different origins as far
as browsers are concerned — there's no shared-cookie trust between them.
`CORS_ALLOWED_ORIGINS` (already wired in `config/settings.py` via
`django-cors-headers`) is the only thing that lets the browser's fetch calls
through. Keep it to the exact production origins plus `localhost:3000` for
local frontend dev against the deployed API if you ever need that.

The current design is fully decoupled by request-time coupling: Django
serves an admin/booking backend, the JWT lives in the browser's memory (or
wherever the frontend chooses to persist it), and every cross-origin call is
authenticated per-request via the `Authorization` header — no cookies, no
CSRF dance needed for the API itself (Django's CSRF protection is still
active for the `/admin/` site, which is same-origin with itself).

---

## 3. Frontend: Cloudflare Pages

1. Connect the GitHub repo in the Cloudflare Pages dashboard. Builds trigger
   automatically on every push — no separate CI pipeline needed.
2. Build settings (assuming static export, see §0):
   - **Build command**: `next build`
   - **Build output directory**: `out`
   - **Root directory**: wherever `package.json` lives (repo root, based on
     the current project layout).
3. Set the frontend's API base URL as a Cloudflare Pages environment
   variable: `NEXT_PUBLIC_API_URL=https://api.sleektattoos.com/api`
   (`lib/api.js` reads this; locally it falls back to
   `http://localhost:8000/api` via `.env.local`).
4. Add the custom domain per §1.2.

---

## 4. Google Calendar service account (one-time, ~20 min)

No OAuth consent screen, no expiring refresh tokens, no owner re-login —
ever. Skip anything that says "OAuth2 user consent" for this; in "Testing"
mode (i.e. without paying for Google Cloud app verification) those refresh
tokens expire every 7 days and quietly break booking sync.

1. Create a Google Cloud project, enable the **Google Calendar API**.
2. Create a **Service Account** under that project → download its JSON key
   file.
3. Note the service account's own email address (looks like
   `booking-bot@sleektattoos-xxxx.iam.gserviceaccount.com`).
4. Studio owner: Google Calendar → Settings → the calendar to sync to →
   **Share with specific people** → add that service-account email with
   **"Make changes to events"** permission.
5. Upload the JSON key to the server per §2.6, set the two env vars
   (`GOOGLE_SERVICE_ACCOUNT_FILE`, `GOOGLE_CALENDAR_OWNER_EMAIL`).
6. Verify: create a test booking through the live API and check
   `calendar_sync_error` is empty and the event actually appears on the
   owner's calendar.

Note on scale: Stellar has no background job runner (no Celery/Redis
realistically available), so the Calendar API call happens synchronously
inside the booking request (`bookings/views.py` → `perform_create`) — the
customer's "Book Now" click takes an extra beat while it talks to Google.
Fine at a single studio's booking volume; not worth engineering around.

---

## 5. Post-deploy checklist

- [ ] `mysqlclient` (or `PyMySQL` fallback) confirmed installing cleanly on Stellar
- [ ] `DJANGO_DEBUG=False` in production env vars
- [ ] Fresh `DJANGO_SECRET_KEY` (not the local dev one)
- [ ] `python manage.py migrate` ran against the real MySQL database
- [ ] `python manage.py createsuperuser` run once, real admin credentials set
- [ ] `python manage.py seed_content` + `seed_locations` run once against production
- [ ] Google service account JSON key uploaded outside `public_html`, path confirmed correct
- [ ] Test booking created via the live API — `calendar_sync_error` empty, event visible on the owner's calendar
- [ ] `CORS_ALLOWED_ORIGINS` matches the real frontend domain(s) exactly (no trailing slash, correct scheme)
- [ ] `.cpanel.yml` placeholders filled in with real cPanel username/app path/Python version
- [ ] A push to the Git repo actually triggers a redeploy and the site reflects the change (test with a trivial commit first)
