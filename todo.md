# Todo

Everything below is real remaining work — the backend itself (models,
endpoints, auth, calendar sync, admin logging) is built and verified, and
**the frontend integration is complete and verified end-to-end** (2026-07-20).
This list is what's left before it's actually live for real users.

## Frontend integration — done

`lib/store.js` is now a thin wrapper around the real API (`lib/api.js`
handles JWT storage/refresh and the visitor-token header). Every item that
used to be listed here is done and was verified in a browser:

- [x] Every `getX()`/`upsertX()`/`deleteX()` in `lib/store.js` calls the
  real `/api/...` endpoints.
- [x] Admin login (`app/admin/layout.jsx`) calls `POST /api/auth/login/`,
  stores the JWT in localStorage, attaches `Authorization: Bearer` to admin
  fetches.
- [x] `ImageUpload.jsx` POSTs to `/api/uploads/images/` and stores the
  returned URL (no more ephemeral `blob:` URLs).
- [x] Support chat persists the real `visitor_token` from
  `POST /api/support/conversations/` and sends `X-Visitor-Token` on every
  call. Note: required extending `CORS_ALLOW_HEADERS` — see `memory.md`.
- [x] `NEXT_PUBLIC_API_URL` set via `.env.local` locally
  (`http://localhost:8000/api`); needs the production value set as a
  Cloudflare Pages env var at deploy time (see `deployment.md` §"Cloudflare
  Pages" step 3).
- [ ] Static export (`next.config.js` → `output: 'export'`) still needs to
  actually be turned on — it was never *set*, just confirmed to be the
  right fit now that the frontend is fetch-based (`deployment.md` §0).

## Before going live

- [ ] Real MySQL credentials on Stellar, `DATABASE_URL` set, migrations run
  against it (not just SQLite locally).
- [ ] Real Google Cloud project + service account created, calendar shared,
  a real test booking verified end-to-end on the live server (see
  `deployment.md` §4 for the checklist).
- [ ] `DJANGO_SECRET_KEY` regenerated for production — never reuse the
  local dev key. As of 2026-07-20, `settings.py` will actually refuse to
  boot with `DJANGO_DEBUG=False` and the default dev key still set, so this
  is no longer a silent-failure risk — but it still needs a real value in
  the production `.env`.
- [ ] `DJANGO_DEBUG=False` and `DJANGO_ALLOWED_HOSTS` set correctly in
  production — right now local `.env` has `DEBUG=True`, which must not
  ship as-is. Flipping `DEBUG=False` also activates a block of production
  security settings (HSTS, secure cookies, `X_FRAME_OPTIONS`, etc — see
  `settings.py`'s "Production security hardening" section and
  `DJANGO_CSRF_TRUSTED_ORIGINS` / `DJANGO_SECURE_SSL_REDIRECT` /
  `DJANGO_HSTS_SECONDS` in `.env.example`) — set those env vars before or
  at the same time as flipping `DEBUG`, not after.
- [ ] `CORS_ALLOWED_ORIGINS` updated to the real frontend domain(s) once
  DNS is live.
- [ ] `.cpanel.yml` placeholders (`<CPANEL_USERNAME>`, `<APP_PATH>`,
  `<PYTHON_VERSION>`) filled in with real values from the Stellar account.
- [ ] `mysqlclient` install verified on the actual Stellar server (flagged
  as a real risk in the original architecture notes — shared hosting can
  choke on its C-extension build; `PyMySQL` is the documented fallback).

## Gaps worth closing before or shortly after launch

- [x] **Rate limiting on public write endpoints and login — done 2026-07-20.**
  `POST /auth/login/` is throttled at 5/min/IP (`login` scope).
  `POST /bookings/`, `POST /contacts/`, `POST /uploads/images/`, and the
  support chat's start/message endpoints are throttled at 20/min
  (`public_write` scope, per-user for staff / per-IP for anonymous callers).
  See `settings.py`'s `DEFAULT_THROTTLE_RATES` and `memory.md`'s security
  section for the full list and reasoning. Residual gap: Django's own
  built-in `/admin/` login (session-based, not DRF) is **not** covered by
  this — it has no throttling of its own. Low priority (requires a valid
  staff username to even attempt), but if it needs hardening later,
  `django-axes` is the standard tool; wasn't added since nothing in this
  build actually surfaces that login page to end users (the custom
  DRF-backed admin panel is what's linked from the site).
- [ ] **No spam/bot protection** on those same public forms — no CAPTCHA,
  no honeypot field. Low priority for a small studio site, but worth a
  glance at submission volume after launch.
- [ ] **No automated tests.** Everything was verified manually via curl
  during this build (documented in `implementation.md`), which is fine for
  a first pass but won't catch regressions later. At minimum, a smoke-test
  suite covering: booking creation (with calendar mocked out), the support
  bot's FAQ matching, and permission enforcement (staff-only endpoints
  actually reject anonymous requests) would be worth the time.
- [x] **Pagination shape (`{count, next, previous, results}`) — checked.**
  Every getter in `lib/store.js` now unwraps `.results`; one instance
  (`getConversations()`) was found calling `.map()` on the raw paginated
  object directly, causing the admin Support inbox to silently show "No
  conversations yet." with no console error. Fixed 2026-07-20 — see
  `memory.md`'s "Bugs found during frontend verification". Still true that
  every seeded dataset is well under `PAGE_SIZE: 50`, so if list volume
  grows past that, the Portfolio page's client-side category filtering
  (which assumes it has the whole gallery list) will need to switch to
  server-side filtering or a bumped page size.
- [ ] **Media storage is local disk** (`MEDIA_ROOT` on the Stellar
  filesystem). Fine at this scale, but there's no CDN and no automatic
  backup beyond whatever Stellar's own backup policy covers — worth
  checking what that actually is before treating uploaded images as durable.
- [ ] **`HomeHighlights`** (the rotating carousel on the homepage) is still
  hardcoded in the frontend's `lib/data.js`, not a database model — it
  was never admin-editable even in the original prototype, so this wasn't
  in scope for the backend build. Flag for later if the client wants to
  edit those from the admin panel.
- [ ] **No dashboard aggregate endpoint.** The admin dashboard's recharts
  (bookings-by-day, gallery-category breakdown, 7-day traffic) currently
  compute client-side from raw list endpoints (`/bookings/`, `/gallery/`,
  etc.), matching the old frontend's approach exactly. Fine at small data
  volume; if the booking/contact/support tables grow large, a dedicated
  `GET /api/dashboard/summary/` that does the aggregation in SQL would be
  cheaper than shipping every row to the browser.
- [ ] **Booking calendar event duration is hardcoded to 2 hours**
  (`bookings/services/google_calendar.py`). Fine as a default; revisit if
  the studio wants duration to vary by service size/hourly booking length.
- [ ] Consider whether `AboutOccasion`/`AboutBookingOption` really need to
  be separate list endpoints from `GET /about/` in the admin panel, or
  whether the combined view is enough — right now both exist (the
  combined view for the public About page, the separate CRUD endpoints
  for the admin panel), which is intentional but worth double-checking
  against the actual admin UI once it's wired up.

## Explicitly out of scope for this build

- Payment processing (the site has never accepted payment — bookings are
  requests only, confirmed via consultation, matching the original
  frontend's copy: "No payment required on this website").
- Multi-tenant / multi-studio support — this is a single-studio backend by
  design (one Google Calendar, one owner).
