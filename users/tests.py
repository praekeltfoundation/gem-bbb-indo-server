from django import test
from rest_framework.authtoken.models import Token
from .models import User, RegUser, SysAdminUser, Profile


class TestUserModel(test.TestCase):
    def create_regular_user(self, username='anonymous', **kwargs):
        return RegUser.objects.create(username=username, **kwargs)

    def create_sysadmin(self, username='admin', **kwargs):
        return SysAdminUser.objects.create(username=username, **kwargs)

    def setUp(self):
        self.factory = test.RequestFactory()
        return None

    def test_create_user(self):
        u = User.objects.create_user(username='Anon', email='anon@ymous.org', password='Blarg')
        self.assertIsNotNone(u, 'User not created.')
        self.assertEqual(u.username, 'Anon', 'Username does not match')
        p = Profile.objects.get(user=u)
        self.assertIsNotNone(p, 'User profile not created.')

    def test_create_regular_user(self):
        u = self.create_regular_user(username='anonymous', password='Honkhonk')
        self.assertIsNotNone(u, 'Regular user not created by proxy.')
        self.assertFalse(u.is_staff, 'Regular user set as staff.')
        self.assertFalse(u.is_superuser, 'Regular user set as superuser.')

    def test_create_sysadmin(self):
        u = self.create_sysadmin(username='anonadmin', password='Honkhonk')
        self.assertIsNotNone(u, 'System administrator not created by proxy.')
        self.assertTrue(u.is_staff, 'System administrator not set as staff.')
        self.assertTrue(u.is_superuser, 'System administrator not set as superuser.')


class TestToken(test.TestCase):

    @staticmethod
    def create_user(username='anonymous', **kwargs):
        return RegUser.objects.create(username=username, **kwargs)

    def test_token_create(self):
        user = self.create_user()
        Token.objects.get_or_create(user=user)
        try:
            token = Token.objects.get(user=user)
        except Token.DoesNotExist:
            token = None
        self.assertIsNotNone(token, 'Token was not created.')

    def test_reset_token_on_password_change(self):
        user = self.create_user(password='first')
        first_token, _ = Token.objects.get_or_create(user=user)

        user.set_password('second')
        user.save()

        try:
            second_token = Token.objects.get(user=user)
        except Token.DoesNotExist:
            second_token = None

        self.assertNotEqual(first_token, second_token, 'Token stayed the same after reset.')
        self.assertIsNone(second_token, 'Token was not deleted.')

    def test_reset_other_users(self):
        """When a user resets their password, and their token is deleted, it should not affect the tokens of other
        users.
        """
        user_1 = self.create_user('user_1')
        user_2 = self.create_user('user_2')
        token_1, _ = Token.objects.get_or_create(user=user_1)
        token_2, _ = Token.objects.get_or_create(user=user_2)

        user_1.set_password('second')
        user_1.save()

        try:
            user_2_token = Token.objects.get(user=user_2)
        except Token.DoesNotExist:
            user_2_token = None

        self.assertIsNotNone(user_2_token, "User 2 had it's token deleted.")
        self.assertEqual(token_2, user_2_token, "User's previous token doesn't match on second retrieve.")

    def test_reset_when_password_same(self):
        """When a user object is edited and saved, but the password has not changed, the token should not change.
        """
        user = self.create_user('anon')
        token, _ = Token.objects.get_or_create(user=user)

        user.email = 'anon@ymous.com'
        user.save()

        try:
            new_token = Token.objects.get(user=user)
        except Token.DoesNotExist:
            new_token = None

        self.assertEqual(token, new_token, "Token was changed unexpectedly.")
