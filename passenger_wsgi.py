"""
cPanel's Passenger looks for this exact file (passenger_wsgi.py) in the
Python App's root and imports `application` from it. This just re-exports
Django's real WSGI app from config/wsgi.py — see deployment.md.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from config.wsgi import application  # noqa: E402,F401
