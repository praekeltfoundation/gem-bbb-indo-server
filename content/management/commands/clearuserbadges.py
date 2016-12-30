
from django.core.management.base import BaseCommand
from content.models import UserBadge


class Command(BaseCommand):
    help = """Clears the Badges earned by a user"""

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            help="Target username"
        )

    def handle(self, *args, **kwargs):
        username = kwargs.get('username')
        self.stdout.write('Clearing Badges for %s...' % username)

        UserBadge.objects.filter(user__username=username).delete()
