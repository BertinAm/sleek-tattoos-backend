"""
WSGI config for the Sleek Tattoos API.

On Namecheap Stellar (cPanel Passenger), this is the entry point Passenger
imports as `application` — see deployment.md for the passenger_wsgi.py
wrapper cPanel expects.
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
