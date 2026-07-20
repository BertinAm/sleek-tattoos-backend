# Sleek Tattoos API — Implementation

Django + Django REST Framework backend for the Sleek Tattoos site. Replaces
the frontend prototype's `lib/store.js` (a localStorage-backed mock data
layer) with a real database and a real API, so content persists per-visitor
correctly, the admin panel edits real data, and bookings actually reach the
studio owner's calendar.

Built and verified locally against SQLite on 2026-07-19/20. Every endpoint
below was smoke-tested end-to-end (see the curl transcript in this session —
login, CRUD writes, booking creation with calendar-sync-disabled fallback,
contact submission, support chat with live FAQ-matching bot replies, image
upload, and permission enforcement all confirmed working).

**Frontend integration is complete** (as of 2026-07-20) — `lib/store.js`
is a thin wrapper around this API (see `memory.md`), and every public page
plus the entire admin panel was verified end-to-end in a browser against the
live backend, including the full booking flow, the shared support-chat
widget, and every admin CRUD screen. Two real bugs were caught and fixed
during that pass — see `memory.md`'s "Bugs found during frontend
verification" section before assuming either area still works as originally
written.

All content types (News, Artists, Gallery, Services, About, FAQ) are fully
database-backed with normal REST CRUD — nothing was moved to static frontend
files. The only scope trim applied was seed *volume*: one featured artist
(Mateusz Kocjan) with 5 news posts and 6 gallery pieces, not a reduction in
what's modeled. See `memory.md` for why.

## Stack

- **Django 5.2** + **Django REST Framework 3.17**
- **Auth**: `djangorestframework-simplejwt` (JWT access/refresh tokens, with
  token blacklisting on logout). No session cookies needed — the frontend is
  a separate origin (`sleektattoos.com` vs `api.sleektattoos.com`), so this
  is a fully decoupled, token-based relationship, not a shared-cookie one.
- **CORS**: `django-cors-headers`, explicit origin allow-list via
  `CORS_ALLOWED_ORIGINS` in `.env`.
- **Database**: SQLite locally (zero setup), MySQL in production via
  `DATABASE_URL` (see deployment.md) — same codebase, no branching logic
  beyond `settings.py` reading the env var.
- **Calendar**: `google-api-python-client` + `google-auth`, service-account
  flow (no OAuth user consent, no expiring tokens — see
  `bookings/services/google_calendar.py`).
- **Config**: `django-environ`, everything environment-driven (`.env.example`
  documents every variable).

## App map

| App | Owns |
|---|---|
| `core` | Auth endpoints, `ActivityLog`, image upload, health check, shared permission classes |
| `content` | News, Artists, Gallery, Services, About (occasions + booking options), FAQ |
| `bookings` | Booking requests, Locations (travel-fee list), Google Calendar sync |
| `contacts` | Contact form submissions |
| `support` | Visitor chat conversations, messages, keyword-matching FAQ bot |

Every app that mutates data has a `signals.py` that writes an `ActivityLog`
row on save/delete — this fires whether the change came through the API or
Django's built-in `/admin/` site, so the Activity Logs admin page is always
complete (mirrors the old `addLog()` calls scattered through `lib/store.js`,
but centralized instead of duplicated per call site).

## Auth model

Public site traffic needs **no** auth. The admin panel needs a real login —
`is_staff=True` on a Django `User` is the only thing that gates write access
anywhere in the API (see `core/permissions.py`: `IsStaffOrReadOnly` /
`IsStaffOnly`).

```
POST /api/auth/login/    {username, password} -> {access, refresh}
POST /api/auth/refresh/  {refresh}             -> {access}
POST /api/auth/logout/   {refresh}             -> 205 (blacklists the refresh token)
GET  /api/auth/me/       (Bearer token)        -> current user
```

Frontend integration note: attach `Authorization: Bearer <access>` to every
admin-panel request. Access tokens are short-lived (`JWT_ACCESS_LIFETIME_MINUTES`,
default 60 min) by design — refresh silently in the background rather than
making the studio owner re-login constantly.

Create the first admin user with `python manage.py createsuperuser`.

## Endpoint reference

All routes are under `/api/`. `[staff]` = requires `Authorization: Bearer`
with `is_staff=True`. Everything else is public.

### Content

| Method | Path | Notes |
|---|---|---|
| GET | `/news/` | paginated list |
| POST | `/news/` | `[staff]` |
| GET | `/news/{slug}/` | |
| PUT/PATCH | `/news/{slug}/` | `[staff]` |
| DELETE | `/news/{slug}/` | `[staff]` |
| GET/POST | `/artists/`, `/artists/{slug}/` | same pattern |
| GET/POST | `/gallery/`, `/gallery/{id}/` | `artist_slug` write field, `artist_name` read field |
| GET/POST | `/services/`, `/services/{id}/` | `cart_value` of `0` means "quote only" (matches the old `num: 0` convention) |
| GET | `/about/` | combined `{occasions, services}` shape — one call for the About page |
| GET/POST | `/about/occasions/`, `/about/occasions/{id}/` | `[staff]` for writes |
| GET/POST | `/about/booking-options/`, `.../{id}/` | `icon` is a lucide-react PascalCase name, same as before |
| GET/POST | `/faq/`, `/faq/{id}/` | powers both the public FAQ accordions and the support bot's keyword matcher |

### Bookings

| Method | Path | Notes |
|---|---|---|
| GET | `/locations/` | public — powers the booking form's city dropdown + travel fee |
| POST | `/locations/` | `[staff]` |
| POST | `/bookings/` | **public** — the booking form. Saves to DB first, then best-effort syncs to Google Calendar. Response always reflects the saved booking; check `calendar_sync_error` if you want to surface sync failures in the admin UI. |
| GET | `/bookings/` | `[staff]` |
| GET/PATCH/DELETE | `/bookings/{id}/` | `[staff]` |
| PATCH | `/bookings/{id}/set_status/` | `[staff]` — `{status: "Contacted"}`, the admin table's cycle button |

### Contacts

| Method | Path | Notes |
|---|---|---|
| POST | `/contacts/` | public — the contact form |
| GET | `/contacts/` | `[staff]` |
| GET/DELETE | `/contacts/{id}/` | `[staff]` |

### Support chat

The widget has no user accounts — a visitor is identified by a
`visitor_token` (UUID) the **frontend must persist** (localStorage, matching
the old `sk_support_visitor_id` key) and send back on every call, either as
header `X-Visitor-Token` or query param `?visitor_token=`.

| Method | Path | Notes |
|---|---|---|
| POST | `/support/conversations/` | `{visitor_token?}` — get-or-create. No token / unknown token creates a new conversation (seeded with the greeting) and returns a fresh token. |
| GET | `/support/conversations/list/` | `[staff]` — admin inbox, newest activity first |
| GET | `/support/conversations/{id}/` | visitor (matching token) or staff |
| POST | `/support/conversations/{id}/messages/` | visitor -> posts as `user`, triggers an instant bot reply (FAQ keyword match, same logic as the old `matchAnswer()`); staff (Bearer token) -> posts as `admin` |
| POST | `/support/conversations/{id}/reset/` | visitor or staff — wipes history back to one fresh greeting |
| POST | `/support/conversations/{id}/read/` | `[staff]` — marks the inbox thread read |

### Core

| Method | Path | Notes |
|---|---|---|
| POST | `/uploads/images/` | `[staff]` — multipart `{file}` -> `{url}`. Admin forms call this first, then pass the returned URL as the `image` field on News/Gallery/Artist/Service. |
| GET | `/logs/` | `[staff]` — Activity Logs admin page, newest first |
| GET | `/health/` | public — uptime check |

## Image fields

`image`/`portrait` fields on content models are plain strings, not Django
`ImageField`s — they accept **either**:
1. An Unsplash photo ID (legacy — `unsplash()` on the frontend already knows
   how to build a CDN URL from this), or
2. A full URL, including the ones `/api/uploads/images/` returns.

This keeps every piece of existing seed content (all Unsplash-sourced)
working unchanged while giving the admin panel a real upload path for new
images instead of the old localStorage `blob:` URLs (which never survived a
page reload).

## Google Calendar sync

See `bookings/services/google_calendar.py`. Every public function there
swallows its own exceptions and returns `(None, error_message)` on failure —
**a Google API problem never blocks a booking from saving**. The booking row
always has `google_calendar_event_id` (set on success) or
`calendar_sync_error` (set on failure) so the admin panel can show sync
status without any extra polling.

Locally, with `GOOGLE_SERVICE_ACCOUNT_FILE` unset, every booking saves fine
and `calendar_sync_error` reads `"Google Calendar not configured..."` — this
was verified directly (see the curl transcript). Setup steps for the real
service account: `deployment.md`.

## Local development

```bash
cd backend
python -m venv venv
./venv/Scripts/activate        # Windows; `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
cp .env.example .env           # defaults are fine for local dev — leave DATABASE_URL blank
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_content      # news, artists, gallery, services, about, faq
python manage.py seed_locations    # booking location / travel-fee list
python manage.py runserver 8000
```

Django admin: `http://localhost:8000/admin/`. API root: `http://localhost:8000/api/`.

Both seed commands are idempotent (`update_or_create` throughout) — safe to
re-run any time to reset content back to the original prototype's copy.

## What's deliberately not built yet

See `todo.md` for the full list — the short version is: the Next.js frontend
still reads from `lib/store.js` (localStorage), not this API. Wiring that up
is the next major piece of work, not something this backend build included.
