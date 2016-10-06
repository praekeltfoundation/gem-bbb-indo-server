from django import test
from .models import User, RegUser, SysAdminUser, Profile


class TestUserModel(test.TestCase):
    def create_regular_user(self, username='anonymous', **kwargs):
        return RegUser.objects.create(username=username, **kwargs)

    def create_sysadmin(self, username='admin', **kwargs):
        return SysAdminUser.objects.create(username=username, **kwargs)

    def setUp(self):
        self.factory = test.RequestFactory()
        self.reguser = self.create_regular_user('anonymous', password='Honkhonk')
        self.sysadmin = self.create_sysadmin('anon_admin', password='Honkadmin')
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
