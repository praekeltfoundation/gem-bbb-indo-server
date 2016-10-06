from django.test import TestCase
from .models import User, RegUser, SysAdminUser, Profile


class TestUserModel(TestCase):
    def create_regular_user(self, first_name='Anon', last_name='Ymous', username='anonymous', password='Honkhonk'):
        return RegUser.objects.create(first_name=first_name, last_name=last_name, username=username, password=password)

    def setUp(self):
        # TODO: Add test setup
        return None

    def test_create_regular_user(self):
        self.assertIsNotNone(self.create_regular_user())