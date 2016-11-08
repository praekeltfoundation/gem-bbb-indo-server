
from django.core.management.base import BaseCommand

from bimbingbung.urls import urlpatterns


class Command(BaseCommand):
    help = """This command lists all url patterns."""

    def handle(self, *args, **kwargs):
        base = '{name}  |  {pattern}'

        def make_str(name, pattern):
            nonlocal base
            return base.format(name=name, pattern=pattern)

        for entry in urlpatterns:
            print(make_str(getattr(entry, 'name', '?'), entry.regex.pattern))
            if hasattr(entry, 'url_patterns'):
                for child in entry.url_patterns:
                    print('   ' + make_str(getattr(child, 'name', '?'), child.regex.pattern))
