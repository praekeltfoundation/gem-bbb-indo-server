
from datetime import timedelta
import json
from io import BytesIO

from django import test
from django.core.files import File
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from .models import User, RegUser, SysAdminUser, Profile
from .serializers import RegUserDeepSerializer


class TestUserModel(APITestCase):

    @staticmethod
    def create_regular_user(username='anonymous', **kwargs):
        return RegUser.objects.create(username=username, **kwargs)

    @staticmethod
    def create_sysadmin(username='admin', **kwargs):
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

    def test_regular_user_password_hash(self):
        password = 'foobar'
        response = self.client.post(reverse('api:users-list'), data={
            'username': 'anon',
            'password': password,
            'profile': {'mobile': ''}
        }, format='json')
        data = json.loads(response.content.decode('utf-8'))
        u = RegUser.objects.get(pk=data['id'])
        self.assertNotEqual(password, u.password, 'Password was stored as plain text.')
        self.assertNotEqual(u.password, '', 'Password was excluded.')
        self.assertIsNotNone(u.password, 'Password was excluded.')


class TestUserAPI(APITestCase):

    def test_user_registration(self):
        data = {
            'username': 'anon',
            'password': 'blargh',
            'profile': {
                'mobile': '1112223334',
                'age': 18,
                'gender': Profile.GENDER_FEMALE
            }
        }
        response = self.client.post(reverse('api:users-list'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "User was not registered.")

        user = User.objects.get(pk=response.data['id'])
        # Verify profile data
        self.assertFalse(bool(user.profile.profile_image), "Profile image unexpectedly exists.")
        self.assertEqual(user.profile.mobile, '1112223334', "Unexpected mobile number.")
        self.assertEqual(user.profile.age, 18, "Unexpected age.")
        self.assertEqual(user.profile.gender, Profile.GENDER_FEMALE, "Unexpected gender.")

    def test_username_update(self):
        user = RegUser.objects.create(username='First', password='password1')

        data = {'username': 'Second'}

        self.client.force_authenticate(user=user)
        response = self.client.patch(reverse('api:users-detail', kwargs={'pk': user.pk}), data, format='json')

        update_user = RegUser.objects.get(id=user.id)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, "Username update request failed.")
        self.assertEqual(update_user.username, 'Second', "Username was not update.")

    def test_password_update(self):
        # TODO: Disallow password to be patched
        user = User.objects.create(username='anon')
        user.set_password('first')
        user.save()

        data = {'password': 'second'}

        self.client.login(username='anon', password='first')
        response = self.client.patch(reverse('api:users-detail', kwargs={'pk': user.pk}), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, "Username update request failed.")

        self.client.logout()
        self.assertTrue(self.client.login(username='anon', password='second'), "Could not log in with new password.")

    def test_password_change(self):
        """The user must confirm their existing password to update it."""
        user = User.objects.create(username='anon')
        user.set_password('first')
        user.save()

        data = {
            'old_password': 'first',
            'new_password': 'second'
        }

        self.client.login(username='anon', password='first')
        response = self.client.post(reverse('api:users-password', kwargs={'pk': user.pk}), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, "Password change failed")

        self.client.logout()
        self.assertTrue(self.client.login(username='anon', password='second'), "Could not log in with new password")

    def test_password_change_old_password_check(self):
        """If the provided old password doesn't match the new password, a bad request will be raised."""
        user = User.objects.create(username='anon')
        user.set_password('first')
        user.save()

        data = {
            'old_password': 'incorrect',
            'new_password': 'second'
        }

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:users-password', kwargs={'pk': user.pk}), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, "Password change unexpectedly succeeded.")

        self.client.logout()
        self.assertTrue(self.client.login(username='anon', password='first'), "Password was unexpectedly changed.")

    def test_user_retrieve_own_profile(self):
        user_1 = RegUser.objects.create(username='User1', password='password1')

        self.client.force_authenticate(user=user_1)
        response = self.client.get(reverse('api:users-detail', kwargs={'pk': user_1.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK, "User could not access own data.")
        self.assertEqual(response.data['id'], user_1.id, "Unexpected User id.")

    def test_user_restriction(self):
        """Users can't retrieve each other's profiles."""
        user_1 = RegUser.objects.create(username='User1', password='password1')
        user_2 = RegUser.objects.create(username='User2', password='password2')

        self.client.force_authenticate(user=user_1)
        response = self.client.get(reverse('api:users-detail', kwargs={'pk': user_2.pk}))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, "User can access restricted user data.")

    def test_anonymous_restriction(self):
        """Users can't retrieve each other's profiles."""
        user_1 = RegUser.objects.create(username='User1', password='password1')
        user_2 = RegUser.objects.create(username='User2', password='password2')

        response_1 = self.client.get(reverse('api:users-detail', kwargs={'pk': user_1.pk}))
        response_2 = self.client.get(reverse('api:users-detail', kwargs={'pk': user_2.pk}))

        self.assertEqual(response_1.status_code, status.HTTP_403_FORBIDDEN, "Anonymous can access restricted user data.")
        self.assertEqual(response_2.status_code, status.HTTP_403_FORBIDDEN, "Anonymous can access restricted user data.")

    def test_first_name_partial_update(self):
        user = RegUser.objects.create(username='anon')
        first_name = 'Anonymous'

        self.client.force_authenticate(user=user)
        response = self.client.patch(reverse('api:users-detail', kwargs={'pk': user.pk}), {
            'first_name': first_name
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, "User update failed.")

        updated_user = User.objects.get(pk=user.pk)
        self.assertEqual(updated_user.first_name, first_name, "User first name was not updated.")

    def test_first_name_partial_update_restrictions(self):
        first_name = 'Anon9977'
        user_1 = RegUser.objects.create(username='User1')
        user_2 = RegUser.objects.create(username='User2', first_name=first_name)

        self.client.force_authenticate(user=user_1)
        response = self.client.patch(reverse('api:users-detail', kwargs={'pk': user_2.pk}), {
            'first_name': 'Anon'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN, "User1 was allowed to update User2's first name.")

        existing_user = User.objects.get(pk=user_2.pk)
        self.assertEqual(existing_user.first_name, first_name, "User2's fist name was changed.")


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


class TestProfile(test.TestCase):

    def test_days_since_joined_true(self):
        threshold = 1
        user = RegUser.objects.create(username='Anon')
        Profile.objects.create(user=user)
        user.date_joined = timezone.now() - timedelta(days=3)
        user.save()

        self.assertTrue(user.profile.is_joined_days_passed(threshold))

    def test_days_since_joined_false(self):
        threshold = 4
        user = RegUser.objects.create(username='Anon')
        Profile.objects.create(user=user)
        user.date_joined = timezone.now() - timedelta(days=3)
        user.save()

        self.assertFalse(user.profile.is_joined_days_passed(threshold))


class TestProfileImage(APITestCase):

    @staticmethod
    def create_user(username='anon'):
        user = RegUser.objects.create(username=username)
        Profile.objects.create(user=user, mobile='1112223334')
        return user

    @staticmethod
    def create_admin_user(username='anon admin'):
        user = User.objects.create(username=username, is_staff=True)
        user.profile.mobile = '1112223334'
        return user

    def test_profile_image_upload(self):
        user = self.create_user()

        headers = {
            'HTTP_CONTENT_TYPE': 'image/png',
            'HTTP_CONTENT_DISPOSITION': 'attachment;filename="profile.png"'
        }

        self.client.force_login(user=user)
        tmp_file = BytesIO(b'foobar')
        response = self.client.post(reverse('api:profile-image', kwargs={'user_pk': user.pk}),
                                    data={'file': tmp_file}, **headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_profile_image_upload_for_admin(self):
        user = self.create_admin_user()

        headers = {
            'HTTP_CONTENT_TYPE': 'image/png',
            'HTTP_CONTENT_DISPOSITION': 'attachment;filename="profile.png"'
        }

        self.client.force_login(user=user)
        tmp_file = BytesIO(b'foobar')
        response = self.client.post(reverse('api:profile-image', kwargs={'user_pk': user.pk}),
                                    data={'file': tmp_file}, **headers)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_upload_restricted(self):
        user = self.create_user('anon')
        wrong_user = self.create_user('wrong')

        headers = {
            'HTTP_CONTENT_TYPE': 'image/png',
            'HTTP_CONTENT_DISPOSITION': 'attachment;filename="profile.png"'
        }

        self.client.force_login(user=user)
        tmp_file = BytesIO(b'foobar')
        response = self.client.post(reverse('api:profile-image', kwargs={'user_pk': wrong_user.pk}),
                                    data={'file': tmp_file}, **headers)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         "View did not prevent user from uploading to someone else's profile image")

    def test_no_image(self):
        """When the user has no profile image, the url field should be None.
        """
        user = self.create_user()
        data = RegUserDeepSerializer(user).data
        url = data['profile']['profile_image_url']
        self.assertIsNone(url, "User data includes has url to nonexistent image '%s'" % url)

    def test_basic_retrieve(self):
        user = self.create_user('anon')
        user.profile.profile_image.save('profile.png', File(BytesIO(b'foobar')))

        self.client.force_authenticate(user=user)

        # Attempt to retrieve it
        response = self.client.get(reverse('api:profile-image', kwargs={'user_pk': user.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK, "Failed retrieving profile image.")


class TestEmailAPI(APITestCase):

    def test_email_change(self):
        user = RegUser.objects.create(username='anon', email='first@email.com')
        new_email = 'second@email.com'

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:users-email', kwargs={'pk': user.pk}), {
            'email': new_email
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, "Email change request failed.")

        updated_user = RegUser.objects.get(pk=user.pk)
        self.assertEqual(updated_user.email, new_email, "Email was not changed.")

