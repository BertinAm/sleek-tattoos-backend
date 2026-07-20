"""ASGI config for the Sleek Tattoos API. Not used on Stellar (Passenger is WSGI-only) — kept for local/dev parity and future portability."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
