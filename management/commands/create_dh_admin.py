from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a DocuHealth Admin account'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True, help='Admin email')
        parser.add_argument('--password', type=str, required=True, help='Admin password')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.ERROR(f'User with email {email} already exists.'))
            return

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    role=User.Role.DHADMIN,  # Your specific role string
                    is_staff=True,    # Usually required for Django Admin access
                    is_active=True
                )
                self.stdout.write(self.style.SUCCESS(f'Successfully created DH Admin: {email}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating admin: {str(e)}'))