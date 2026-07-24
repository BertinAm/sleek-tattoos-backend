"""
Creates (or, if it already exists, updates the password of) a Django staff
superuser account. `manage.py createsuperuser` is interactive by default,
which doesn't work through cPanel's "Execute python script" field — this is
the non-interactive equivalent, safe to re-run (idempotent on username).

Run via cPanel's "Setup Python App" -> "Execute python script" field:
    manage.py create_admin_user <username> <password> [--email EMAIL]

Example:
    manage.py create_admin_user sleektattoos00@gmail.com <password> --email sleektattoos00@gmail.com
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Creates or updates a Django staff superuser account non-interactively.'

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('password')
        parser.add_argument('--email', default='')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options['email'] or (username if '@' in username else '')

        user, created = User.objects.get_or_create(username=username, defaults={'email': email})
        if email:
            user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created new staff superuser: {username}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated existing user to staff superuser with new password: {username}'))
