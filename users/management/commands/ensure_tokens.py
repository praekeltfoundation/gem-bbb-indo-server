
from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token
from users.models import RegUser


class Command(BaseCommand):
    help = """This command helps create tokens for existing users with no tokens."""

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating tokens for existing users...')
        for user in RegUser.objects.all():
            self.stdout.write('  Creating token for %s' % user.username)
            Token.objects.get_or_create(user=user)
