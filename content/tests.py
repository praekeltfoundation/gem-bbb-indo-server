
import json

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from wagtail.wagtailcore.models import Page
from users.models import User, RegUser

from .models import Tip
from .models import Goal, GoalTransaction


def create_test_user():
    """Creates a staff user."""
    return User.objects.create(username='Anon', email='anon@ymous.org', password='Blarg',
                               is_staff=True, is_superuser=False)


def create_tip(title='Test tip', body='This is a test tip', **kwargs):
    parent_page = Page.get_root_nodes()[0]
    tip = Tip(
        title=title,
        body=body,
        **kwargs
    )
    parent_page.add_child(instance=tip)
    tip.save()
    tip.unpublish()
    return tip


def publish_page(user, page):
    revision = page.save_revision(
        user=user,
        submitted_for_moderation=False,
    )
    revision.publish()


class TestTipModel(TestCase):

    def setUp(self):
        self.user = create_test_user()

    def tearDown(self):
        self.user.delete()

    def test_create_tip(self):
        tip = create_tip()
        self.assertIsNotNone(tip, 'Tip not created')
        self.assertEqual(tip.title, 'Test tip', 'Test tip title was not set.')

    def test_cover_image_url(self):
        self.skipTest('Needs to instantiate a wagtail Image')
        # TODO: Instatiate Image
        # from django.core.files.images import ImageFile
        # from wagtail.wagtailimages.models import Image
        #
        # image = Image(
        #     title="Image title",
        #
        #     # image_file is your StringIO/BytesIO object
        #     file=ImageFile(image_file, name="image-filename.jpg"),
        # )
        # image.save()

    def test_cover_none(self):
        """When a Tip does not have a cover image set, the image url must be None."""
        tip = create_tip()
        self.assertIsNone(tip.get_cover_image_url(), 'Cover image url is not None.')


class TestTipAPI(APITestCase):

    def setUp(self):
        self.user = create_test_user()
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        self.user.delete()
        self.client.force_authenticate(user=None)

    def test_draft_filter(self):
        """When listing Tips in the REST endpoint, only published tips should be included."""
        draft_tip = create_tip(title='Draft tip')
        draft_tip.unpublish()
        live_tip = create_tip(title='Live tip')
        publish_page(self.user, live_tip)

        response = self.client.get(reverse('api:tips-list'))
        data = json.loads(response.content.decode('utf-8'))
        self.assertEqual(Tip.objects.all().count(), 2, 'Test did not set up Tip pages correctly.')
        self.assertEqual(len(data), 1, 'View returned more than one Tip.')
        self.assertEqual(data[0]['title'], 'Live tip', 'The returned Tip was not the expected live page.')


class TestGoalAPI(APITestCase):

    @staticmethod
    def create_staff_user(username='AnonStaff'):
        return User.objects.create(username=username, email='anon@ymous.org', password='Blarg',
                                   is_staff=True, is_superuser=False)

    @staticmethod
    def create_regular_user(username='AnonReg'):
        return RegUser.objects.create(username=username, email='anon-reg@ymous.org', password='Blarg',
                                      is_staff=False, is_superuser=False)

    def test_admin_list_all(self):
        """A staff member must be able to see all goals."""

        # Model instances
        user_1 = self.create_regular_user('User1')
        user_2 = self.create_regular_user('User2')
        user_admin = self.create_regular_user('AdminUser')

        # TODO: Refactor Goal creation into helper function
        goal_1 = Goal.objects.create(name='Goal 1', user=user_1, value=1000, start_date=timezone.now(), end_date=timezone.now())
        goal_2 = Goal.objects.create(name='Goal 2', user=user_1, value=1000, start_date=timezone.now(), end_date=timezone.now())

        goal_3 = Goal.objects.create(name='Goal 3', user=user_2, value=1000, start_date=timezone.now(), end_date=timezone.now())

        # Test view permissions

        self.skipTest('TODO')

    def test_admin_filter_by_user(self):
        """A staff member must be able to filter any user."""
        self.skipTest('TODO')

    def test_user_list_all_restriction(self):
        """A user must not see other user's Goals when listing all.
        """
        self.skipTest('TODO')

    def test_user_filter_by_owned(self):
        """User must be able to retrieve their own Goals."""
        self.skipTest('TODO')
