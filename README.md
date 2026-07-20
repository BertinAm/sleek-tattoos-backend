# Sleek Tattoos — API

Django 5.2 + Django REST Framework backend for the [Sleek Tattoos](https://sleektattoos.com) site. Serves all content (news, artists, gallery, services, about, FAQ), booking requests with Google Calendar sync, contact form submissions, and a support-chat widget — all real database-backed CRUD behind a JWT-authenticated admin panel. Pairs with the [sleek-tattoos-frontend](https://github.com/BertinAm/sleek-tattoos-frontend) Next.js app.

## Stack

- **Django 5.2** + **Django REST Framework**
- **Auth**: `djangorestframework-simplejwt` (JWT access/refresh, blacklist-on-logout) for the admin panel; the public site needs no auth at all
- **Database**: SQLite locally, MySQL in production (Namecheap Stellar), same codebase — branches on whether `DATABASE_URL` is set
- **Calendar**: Google Calendar API via a service account (no OAuth, no expiring tokens)
- **Config**: `django-environ`, fully environment-driven

## Run it locally

```bash
python -m venv venv
venv\Scripts\activate          # Windows — use `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
copy .env.example .env         # `cp .env.example .env` on macOS/Linux — defaults are fine for local dev
python manage.py migrate
python manage.py seed_content
python manage.py seed_locations
python manage.py createsuperuser
python manage.py runserver 8000
```

API is served at `http://localhost:8000/api/`, Django admin at `http://localhost:8000/admin/`, health check at `/api/health/`.

## Structure

| App | Owns |
|---|---|
| `core` | Auth endpoints, activity log, image upload, health check, shared permission classes |
| `content` | News, Artists, Gallery, Services, About (occasions + booking options), FAQ |
| `bookings` | Booking requests, Locations (travel-fee list), Google Calendar sync |
| `contacts` | Contact form submissions |
| `support` | Visitor chat conversations/messages, keyword-matching FAQ bot |

Every app that mutates data has a `signals.py` that writes an `ActivityLog` row on save/delete — fires whether the change came through the API or Django's own `/admin/` site, so the Activity Logs page is always complete.

## More detailed docs

Deeper architecture notes, deployment steps, and internal planning docs are kept locally (`implementation.md`, `deployment.md`, `todo.md`, `memory.md`) rather than published in this public repo. Ask a maintainer if you need access.
