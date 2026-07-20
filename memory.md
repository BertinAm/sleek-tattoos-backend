# Memory — context for whoever (human or AI) picks this up next

Read this before touching the backend. It's the "why" behind decisions that
aren't obvious from the code alone. `implementation.md` is the "what" (full
endpoint reference); `deployment.md` is the "how to ship it"; `todo.md` is
"what's left." This file is "what you'd otherwise have to re-derive."

## What this is and why it exists

The Sleek Tattoos site started as a Next.js frontend with a fake backend —
`lib/store.js` faked persistence via `localStorage`, meaning every "admin
edit" only existed in one browser, on one device, and vanished if the user
cleared site data. This Django app is the real backend that replaces it.
**As of 2026-07-20, the frontend is fully switched over.** `lib/store.js`
is now a thin wrapper that calls the real API through `lib/api.js` (JWT
storage, auto-refresh-on-401, visitor-token header) — every public page and
the entire admin panel were verified end-to-end in a browser against the
live backend. Don't assume the old localStorage-mock architecture still
applies; read `lib/store.js` directly if you need current field-name
mappings between the API and the frontend's internal shapes.

## Scope: what's actually in the database

Every content type (News, Artists, Gallery, Services, About, FAQ) is a real
Django model with full REST CRUD — nothing was moved to static frontend
files, despite an earlier mid-build detour that briefly trimmed the `content`
app down to Services-only. That was a misreading of a scope-trim request and
was explicitly reverted by the user ("No all of that data will be store in
the database so restore that file"). The only real requirement was trimming
seed *volume*, not the schema: `seed_content.py` seeds one featured artist
(Mateusz Kocjan) with 5 news posts and 6 gallery pieces, all six gallery
items tied to that one artist. If you're ever asked to "reduce what's in the
database," re-read this paragraph before touching `models.py` — the last
time that phrase came up, the actual ask was about row counts, not schema.

## Why these specific technical choices

- **Django + DRF, not FastAPI/Flask/Node**: the user explicitly asked for
  Django, and specified Namecheap Stellar shared hosting (cPanel + Passenger
  WSGI) as the deploy target — that constrains the framework choice
  regardless of what else might be "simpler." Passenger only speaks WSGI, so
  ASGI-only frameworks were never on the table here.
- **JWT (simplejwt), not session auth, for the admin panel**: the frontend
  and backend are different origins (`sleektattoos.com` /
  `api.sleektattoos.com`) with no shared-cookie trust. Session auth would
  need CSRF token juggling across origins for zero benefit over a bearer
  token. Access tokens are short-lived (1hr default) with refresh rotation —
  tune `JWT_ACCESS_LIFETIME_MINUTES` / `JWT_REFRESH_LIFETIME_DAYS` in `.env`
  if that cadence is annoying in practice.
- **SQLite locally, MySQL in prod, one settings.py**: `DATABASE_URL` env var
  presence/absence branches it (`config/settings.py`). Not Postgres — Stellar's
  included database is MySQL, and paying extra for a managed Postgres
  instance would blow the ~$50/yr budget the user specified. `mysqlclient`
  vs `PyMySQL` is flagged as a real open risk in `deployment.md` — shared
  hosting can choke on `mysqlclient`'s C-extension build. **Verify this on
  the actual server before assuming it works** — it wasn't testable in this
  sandbox (no MySQL server available here).
- **Activity logging via Django signals, not inline in views**: originally
  written inline in each ViewSet's `perform_create`/`perform_update`, then
  deliberately refactored to `signals.py` per app. Reasoning: Django's
  built-in `/admin/` site is a first-class way to manage content here (not
  just a fallback), and inline view-logging would silently miss any edit
  made through `/admin/` instead of the API. Signals fire either way — one
  source of truth. If you add a new model that should show up in Activity
  Logs, add a signal handler, not a `add_log()` call in the view.
- **Google Calendar via service account, not OAuth user consent**: this
  was an explicit, emphatic instruction from the user (quoting their own
  research) — OAuth "Testing" mode refresh tokens expire every 7 days
  without paying for Google Cloud app verification, which would silently
  break booking sync weekly. Service account + calendar-sharing has no
  expiry and no re-auth ever. Don't "simplify" this back to OAuth without
  re-reading why it was avoided.
- **"Save booking first, sync calendar second, never block"**: also an
  explicit user instruction. `bookings/views.py`
  `BookingViewSet.perform_create` saves unconditionally, then calls
  `google_calendar.create_booking_event()` in a way that can never raise
  past that point (the service module itself catches everything and
  returns `(None, error)` on any failure). This was verified: a booking
  created locally with no service account configured still saves
  correctly, with `calendar_sync_error` explaining why sync didn't happen.
  If you touch this flow, preserve that ordering and that guarantee.
- **Image fields are plain strings (Unsplash ID or URL), not
  `ImageField`**: the existing seed content is 100% Unsplash-hotlinked
  photo IDs (`unsplash(id)` on the frontend builds the CDN URL). Making
  the field a real `ImageField` would've broken every seeded record.
  Instead, `/api/uploads/images/` is a separate endpoint that saves a real
  file and returns a URL — which fits into the *same* string field
  alongside legacy Unsplash IDs. `lib/data.js`'s `unsplash()` helper
  already has a branch for full URLs (added earlier in this project, before
  the backend existed) — don't remove that branch, the whole scheme depends
  on it.
- **Support chat has no real user accounts**: it's a low-stakes widget, not
  something worth building auth for. A `visitor_token` (UUID) is
  self-reported by the frontend and trusted at face value — someone could
  theoretically guess another visitor's UUID and read their chat, but the
  content is "do you do cover-ups" level, not something worth an auth
  system over. If that threat model ever changes (e.g. chat starts
  including anything sensitive), revisit this.

## Things that surprised me while building this (worth knowing before you assume otherwise)

- `mysqlclient` is intentionally **not installed** in the local dev venv —
  only `requirements.txt` lists it (for the production server to install).
  Local dev never touches MySQL. Don't add it to local dev setup
  instructions; it's unnecessary friction for zero benefit locally.
- The `content` app's `AboutSummaryView` (`GET /api/about/`) exists
  *alongside* the separate `/about/occasions/` and `/about/booking-options/`
  CRUD endpoints — this isn't redundancy, it's two different consumers: the
  public About page wants one combined call, the admin panel wants normal
  REST CRUD on each sub-resource. Keep both.
- DRF's default pagination (`PageNumberPagination`, `PAGE_SIZE: 50`) is
  active on every list endpoint. The old frontend/localStorage layer never
  paginated anything — it just returned full arrays. Every seeded dataset
  here is well under 50 items so this has never actually been *observed* to
  matter, but it's a real behavior difference the frontend integration work
  needs to account for (DRF returns `{count, next, previous, results}`, not
  a bare array).
- `homeHighlights` (the homepage's rotating image/quote carousel) was
  **deliberately not modeled** — it was never admin-editable in the
  original frontend either (hardcoded in `lib/data.js`), so there was
  nothing to port. Don't add a `HomeHighlight` model unless someone
  actually asks for that to become editable.
- **`django-cors-headers`' default `CORS_ALLOW_HEADERS` doesn't include
  custom headers.** The frontend sends `X-Visitor-Token` on every support-chat
  request (anonymous visitor identity). Without explicitly extending
  `corsheaders.defaults.default_headers` in `settings.py`, the browser's
  preflight silently rejects the request client-side — this manifests as a
  generic `TypeError: Failed to fetch` / `net::ERR_FAILED` with **no clear
  CORS error message**, not an obvious CORS rejection. It broke Home,
  Services, Portfolio, and Contact simultaneously (every page touching
  gallery/FAQ/services/support) the moment a visitor token existed in
  localStorage, i.e. after the very first page load — and easy to miss
  because the failure looks like a network problem, not an auth/CORS one.
  Fixed once in `settings.py`; if you add another custom header anywhere,
  extend that same list or you'll rediscover this.
- **`ImageUploadView` (`core/views.py`) is `AllowAny`, not staff-only** —
  changed mid-build once the booking form (public, no login) needed to let
  customers attach reference images before submitting. It's still an
  unauthenticated public write endpoint with no rate limiting, same caveat
  as `/bookings/` and `/contacts/` in `todo.md`.

## Bugs found during frontend verification (2026-07-20)

Two real bugs surfaced only once the frontend was wired to the live API and
clicked through page by page — neither was caught by `manage.py check`,
migrations, or the earlier curl smoke tests, because both are about how a
DRF list response's *shape* gets consumed, not whether the endpoint responds.

- **`support/views.py`'s `ConversationListView.get_queryset` evaluated
  `self.queryset` directly** (`sorted(self.queryset, ...)`) instead of
  `self.queryset.all()`. DRF caches and reuses the class-level `.queryset`
  attribute across requests, so evaluating it directly raises
  `RuntimeError: Do not evaluate the .queryset attribute directly` on every
  call to `GET /api/support/conversations/list/` — a hard 500, not a data
  bug. Fixed by calling `.all()` first. **Lesson**: any DRF generic view
  that overrides `get_queryset()` to do something to `self.queryset` (sort,
  filter) must clone it first — never iterate the class attribute as-is.
- **`lib/store.js`'s `getConversations()` called `data.map(...)` on the
  admin conversation-list response**, but that endpoint is paginated like
  everything else (`{count, next, previous, results}`), not a bare array.
  `data.map` isn't a function on a plain object, so the call threw, was
  swallowed by the admin Support page's `.catch(() => setConversations([]))`,
  and the inbox silently rendered "No conversations yet." with zero
  indication anything was wrong — no console error, no failed network
  request (the request succeeded; only the client-side parsing broke).
  Fixed by changing it to `data.results.map(...)`, matching every other
  getter in the file. **Lesson**: this is the exact class of bug
  `todo.md`'s "pagination default needs a frontend-side check" item warned
  about — it's worth grep'ing `lib/store.js` for any other bare `.map(`/
  `.forEach(` on an `api.get()` result that isn't already unwrapping
  `.results`, since this one hid behind a silent catch for a while.

## Security hardening pass (2026-07-20)

A full pass was done across every public-facing endpoint and the frontend
alongside it. Worth knowing if you're auditing this again later:

- **`Booking.travel_fee` was a mass-assignment hole.** It was in
  `BookingSerializer.fields` but not `read_only_fields`, so the public,
  unauthenticated `POST /bookings/` accepted a client-supplied travel fee
  outright — verified by POSTing `travel_fee: 999999` and getting it echoed
  back. Fixed by making it read-only and computing it server-side in
  `BookingViewSet.perform_create` from a case-insensitive `Location.name`
  lookup (falls back to 0 for free-text "Other" locations, matching the
  booking form's "final pricing confirmed after consultation" copy). If you
  add another field to `Booking` that should never be client-controlled,
  check `read_only_fields` the same way — this class of bug won't show up
  in `manage.py check`, only in an actual request against the endpoint.
- **Unbounded `TextField`/`CharField` inputs on public write endpoints.**
  `Booking.notes`, `ContactSubmission.message`, and `Message.text` (support
  chat) are all DB `TextField`s with no `max_length`, and none of their
  serializers overrode that — meaning an anonymous caller could submit an
  arbitrarily large payload to any of them. Added explicit `max_length`
  overrides on the serializer fields (2000/5000/2000 respectively) even
  though the model fields themselves stay unbounded — DRF still enforces a
  serializer-level `CharField(max_length=...)` regardless of what the
  underlying model column allows.
- **`Booking.reference_images` (JSONField) had no shape validation** — a
  malicious client could submit a huge or deeply-nested JSON blob instead
  of a list of URL strings. Added `validate_reference_images` capping it to
  10 items, each a non-empty string under 500 chars.
- **`ImageUploadSerializer` had no explicit size cap.** `ImageField()`
  already verifies (via Pillow) that the upload is a genuine, openable
  image — the main protection against disguised executables — but nothing
  stopped a legitimately-image-shaped multi-hundred-MB file. Added a 5MB
  `validate_file` check, and set `DATA_UPLOAD_MAX_MEMORY_SIZE` /
  `FILE_UPLOAD_MAX_MEMORY_SIZE` to 8MB in `settings.py` as a body-size
  backstop above that.
- **No throttling anywhere.** Added `AnonRateThrottle`/`UserRateThrottle`
  as the global DRF default (`1000/hour` anon, `3000/hour` user — sized
  well above normal browsing/admin-panel traffic, not meant to be the real
  limiter), plus two `ScopedRateThrottle` scopes: `login` (5/min/IP, on
  `LoginView` only) and `public_write` (20/min, per-user for staff /
  per-IP for anon) applied to every unauthenticated write path:
  `POST /bookings/`, `POST /contacts/`, `POST /uploads/images/`, and both
  support-chat POST endpoints. `BookingViewSet`/`ContactSubmissionViewSet`
  override `get_throttles()` to apply the scope only to `create` — staff
  list/destroy/status actions stay on the general `user` rate so admin
  panel use is never throttled by the public-facing limit.
- **Production security settings were entirely absent.** Added a
  `if not DEBUG:` block in `settings.py`: `SECURE_SSL_REDIRECT`,
  `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`
  (+ subdomains/preload), `SECURE_CONTENT_TYPE_NOSNIFF`,
  `X_FRAME_OPTIONS = 'DENY'`, `SECURE_REFERRER_POLICY`, and
  `CSRF_TRUSTED_ORIGINS` (Django's own `/admin/` site uses session+CSRF
  cookies, unlike the JWT API — that's the one thing here that actually
  needs it). All gated on `DEBUG` so local HTTP dev is untouched. New
  `.env.example` vars: `DJANGO_CSRF_TRUSTED_ORIGINS`,
  `DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_HSTS_SECONDS`.
- **`SECRET_KEY` had a silent insecure fallback.** `settings.py` now raises
  `ImproperlyConfigured` at boot if `DEBUG=False` and the key is still the
  dev default — turns a "forgot to set an env var" mistake into an
  immediate crash instead of a production deploy quietly running on a
  guessable key.
- **This whole API origin now serves a deny-all `robots.txt`**
  (`GET /robots.txt` → `RobotsView`, mounted at the domain root in
  `config/urls.py`, not under `/api/`) — nothing on `api.sleektattoos.com`
  is ever meant to be indexed.
- **Frontend**: added a cookie-consent banner (`components/CookieConsent.jsx`,
  Accept/Reject/Customize, stores choice in `localStorage['sk_cookie_consent']`,
  exposes `hasAnalyticsConsent()` for gating any analytics script added
  later — there isn't one yet), a `/privacy` page describing actual data
  practices, `app/robots.js` (Next.js metadata route, disallows `/admin`,
  resolves to a static file under `output: 'export'`), and a
  `<meta name="robots" content="noindex, nofollow">` rendered directly
  inside `app/admin/layout.jsx`. That layout is a Client Component so it
  can't export Next's `metadata` API (server-components only) — but
  Next.js still hoists `<meta>`/`<title>` tags into `<head>` wherever
  they're rendered in the tree, which is what makes this work without
  middleware (middleware doesn't run under the static export this site
  deploys as — see `deployment.md` §0).
- **Not done, flagged for later**: no CAPTCHA/honeypot on public forms
  (throttling covers volume, not a single determined submitter), no
  `django-axes` on Django's built-in `/admin/` login, no dependency
  vulnerability scan of `requirements.txt`/`package.json` pins.

## How to verify the backend still works after changes

This is exactly the sequence used to build confidence in the original
build — repeat it after any non-trivial change:

```bash
cd backend
./venv/Scripts/python.exe manage.py check
./venv/Scripts/python.exe manage.py makemigrations --check   # fails if you forgot a migration
./venv/Scripts/python.exe manage.py migrate
./venv/Scripts/python.exe manage.py runserver 8000
```

Then, in another shell, the smoke-test sequence that was actually run and
passed during this build (adjust the password if you re-seed with a
different superuser):

```bash
curl -s http://127.0.0.1:8000/api/health/
curl -s http://127.0.0.1:8000/api/news/
curl -s -X POST http://127.0.0.1:8000/api/auth/login/ -H "Content-Type: application/json" -d '{"username":"admin","password":"admin12345"}'
# use the returned access token for Authorization: Bearer <token> on write calls
```

Full transcript of everything tested (login, CRUD, booking creation with
calendar disabled, contact form, support chat bot matching, image upload,
permission enforcement on staff-only routes) is in this session's history —
`implementation.md`'s "Endpoint reference" section is the durable summary
of what was confirmed working.

## Local admin credentials (dev only — do not reuse in production)

Created during this build for testing:
- username: `admin`
- password: `admin12345`

This exists only in the local SQLite `db.sqlite3` (gitignored, never
shipped). Production needs its own `createsuperuser` run with a real
password — see `deployment.md`'s post-deploy checklist.
