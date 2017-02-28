
import json
from datetime import datetime, date, timedelta
import unittest
from unittest import mock
from unittest.mock import Mock, patch
from unittest.mock import PropertyMock

# django imports
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

# REST framework imports
from rest_framework import status
from rest_framework.test import APITestCase
import rest_framework.exceptions as rest_exceptions

# wagtail imports
from wagtail.wagtailcore.models import Site, Page

# auth imports?
from users.models import User, RegUser, Profile

# content function imports
from .models import award_challenge_win, QuizQuestion, FreeTextQuestion, PictureQuestion, QuestionOption, \
    award_first_goal, CustomNotification, ParticipantPicture, Entry, ParticipantAnswer, ParticipantFreeText

# content model imports
from .models import Badge, BadgeSettings, UserBadge
from .models import Challenge, Participant
from .models import Feedback
from .models import WeekCalc
from .models import GoalPrototype, Goal, GoalTransaction
from .models import Tip, TipFavourite

# content serializer imports
from .serializers import FeedbackSerializer
from .serializers import ParticipantRegisterSerializer
from django.http import HttpRequest

from wagtail.wagtailimages import models as wagtail_image_models


# TODO: Mock datetime.now instead of using timedelta


def create_test_regular_user(username='AnonReg'):
    return RegUser.objects.create(username=username, email='anon-reg@ymous.org', password='Blarg',
                                  is_staff=False, is_superuser=False)


def create_test_admin_user(username='Anon'):
    """Creates a staff user."""
    return User.objects.create(username=username, email='anon@ymous.org', password='Blarg',
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


def create_goal(name, user, target):
    return Goal.objects.create(name=name, user=user, target=target, start_date=timezone.now(), end_date=timezone.now())


def create_test_challenge(**kwargs):
    """
    Create a test challenge. Params can be set via kwargs.
    @param name default='Test Challenge'
    @param activation_date default=timezone.now() + timedelta(days=-7)
    @param deactivation_date default=timezone.now() + timedelta(days=+7)
    @param publish default=True
    """
    challenge = Challenge(
        name=kwargs.get('name', 'Test Challenge'),
        activation_date=kwargs.get('activation_date', timezone.now() + timedelta(days=-7)),
        deactivation_date=kwargs.get('deactivation_date', timezone.now() + timedelta(days=7))
    )

    if kwargs.get('publish', True):
        challenge.publish()
    challenge.save()

    return challenge


# ========== #
# Challenges #
# ========== #


class TestChallengeModel(TestCase):

    def test_is_not_active(self):
        challenge = Challenge.objects.create(
            name='Test Challenge',
            activation_date=timezone.now() + timedelta(days=1),
            deactivation_date=timezone.now() + timedelta(days=2)
        )
        self.assertFalse(challenge.is_active, "Challenge was unexpectedly active.")

    def test_is_not_active_but_published(self):
        challenge = Challenge.objects.create(
            name='Test Challenge',
            activation_date=timezone.now() + timedelta(days=1),
            deactivation_date=timezone.now() + timedelta(days=2)
        )
        challenge.publish()
        challenge.save()
        self.assertFalse(challenge.is_active, "Challenge was unexpectedly active.")

    def test_is_active(self):
        challenge = Challenge.objects.create(
            name='Test Challenge',
            activation_date=timezone.now() + timedelta(days=-1),
            deactivation_date=timezone.now() + timedelta(days=2)
        )
        challenge.publish()
        challenge.save()
        self.assertTrue(challenge.is_active, "Challenge was unexpectedly inactive.")

    def test_get_next(self):
        """The next challenge is chosen according to the activation date, whether it is active or not."""
        challenge_later = Challenge.objects.create(
            name='Later Challenge',
            activation_date=timezone.now() + timedelta(days=3),
            deactivation_date=timezone.now() + timedelta(days=5)
        )
        challenge_later.publish()
        challenge_later.save()

        challenge_now = Challenge.objects.create(
            name='Current Challenge',
            activation_date=timezone.now() + timedelta(days=1),
            deactivation_date=timezone.now() + timedelta(days=5)
        )
        challenge_now.publish()
        challenge_now.save()

        challenge_much_later = Challenge.objects.create(
            name='Much Later Challenge',
            activation_date=timezone.now() + timedelta(days=18),
            deactivation_date=timezone.now() + timedelta(days=30)
        )
        challenge_much_later.publish()
        challenge_much_later.save()

        next_challenge = Challenge.get_current()
        self.assertEqual(challenge_now, next_challenge, "Unexpected challenge was returned.")

    def test_ignore_over(self):
        """When a Challenge is past it's deactivation date, the next Challenge should be chosen."""
        challenge_old = Challenge.objects.create(
            name='Old Challenge',
            activation_date=timezone.now() + timedelta(days=-14),
            deactivation_date=timezone.now() + timedelta(days=-7)
        )
        challenge_old.publish()
        challenge_old.save()

        challenge_current = Challenge.objects.create(
            name='Current Challenge',
            activation_date=timezone.now() + timedelta(days=-2),
            deactivation_date=timezone.now() + timedelta(days=2)
        )
        challenge_current.publish()
        challenge_current.save()

        next_challenge = Challenge.get_current()

        self.assertEqual(challenge_current, next_challenge, "Unexpected challenge returned.")

    def test_prefer_published(self):
        """When an unpublished and published challenge overlap on dates, the published should be preferred."""
        Challenge.objects.create(
            name='Unpublished Challenge',
            activation_date=timezone.now() + timedelta(days=-7),
            deactivation_date=timezone.now() + timedelta(days=7)
        )

        challenge_published = Challenge.objects.create(
            name='Published Challenge',
            activation_date=timezone.now() + timedelta(days=-7),
            deactivation_date=timezone.now() + timedelta(days=7)
        )
        challenge_published.publish()
        challenge_published.save()

        Challenge.objects.create(
            name='Later Unpublished Challenge',
            activation_date=timezone.now() + timedelta(days=-7),
            deactivation_date=timezone.now() + timedelta(days=7)
        )

        next_challenge = Challenge.get_current()

        self.assertEqual(challenge_published, next_challenge, "Unexpected challenge returned.")


class TestChallengeAPI(APITestCase):

    # def test_date_filtering(self):
    #     """When the current date is outside the Challenge's activation and deactivation time, it should not be available.
    #     """
    #     self.skipTest('TODO')

    def test_no_challenge_available(self):
        user = create_test_regular_user('anon')
        # No Challenge created

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:challenges-current'), format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ============ #
# Participants #
# ============ #


class ChallengeParticipantRegistrationAPI(APITestCase):

    def test_create_participant(self):
        """Before a user can participate in a Challenge, they must register for the Challenge."""
        user = create_test_regular_user('anon')
        challenge = create_test_challenge()

        serializer = ParticipantRegisterSerializer(data={'user': user.id, 'challenge': challenge.id})
        if serializer.is_valid(raise_exception=True):
            participant = serializer.save()

    def test_participant_no_user(self):
        """Participant registration requires a valid user."""
        challenge = create_test_challenge()
        serializer = ParticipantRegisterSerializer(data={'user': 0xDEADBEEF, 'challenge': challenge.id})

        with self.assertRaises(rest_exceptions.ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_participant_no_challenge(self):
        """Participant registration requires a valid challenge."""
        user = create_test_regular_user('anon')
        serializer = ParticipantRegisterSerializer(data={'user': user.id, 'challenge': 0xDEADBEEF})

        with self.assertRaises(rest_exceptions.ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_create_participant_multiple_times(self):
        """Registering for a challenge multiple times should return the same participant."""
        user = create_test_regular_user('anon')
        challenge = create_test_challenge()

        participant1 = None
        serializer1 = ParticipantRegisterSerializer(data={'user': user.id, 'challenge': challenge.id})
        if serializer1.is_valid(raise_exception=True):
            participant1 = serializer1.save()

        participant2 = None
        serializer2 = ParticipantRegisterSerializer(data={'user': user.id, 'challenge': challenge.id})
        if serializer2.is_valid(raise_exception=True):
            participant2 = serializer2.save()

        self.assertEqual(participant1.id, participant2.id, msg='Should be the same participant')

    def test_create_participant_invalid_time(self):
        """Participants should only be able to register for active challenges."""
        user = create_test_regular_user('anon')
        challenge = create_test_challenge(activation_date=timezone.now() + timedelta(days=+1),
                                          deactivation_date=timezone.now() + timedelta(days=+7))

        serializer = ParticipantRegisterSerializer(data={'user': user.id, 'challenge': challenge.id})
        with self.assertRaises(rest_exceptions.ValidationError):
            serializer.is_valid(raise_exception=True)

        challenge.activation_date = timezone.now() + timedelta(days=-7)
        challenge.deactivation_date = timezone.now() + timedelta(days=-1)
        serializer = ParticipantRegisterSerializer(data={'user': user.id, 'challenge': challenge.id})
        with self.assertRaises(rest_exceptions.ValidationError):
            serializer.is_valid(raise_exception=True)


# ================= #
# Challenge Entries #
# ================= #


class ChallengeParticipantIntegrationAPI(APITestCase):

    def test_filter_challenge(self):
        """When the user has participated in a Challenge, they should receive the next available Challenge."""
        user = create_test_regular_user('anon')

        # Both challenges are active
        challenge_first = Challenge.objects.create(
            name='First Challenge',
            activation_date=timezone.now() + timedelta(days=-7),
            deactivation_date=timezone.now() + timedelta(days=7)
        )
        challenge_first.publish()
        challenge_first.save()

        challenge_second = Challenge.objects.create(
            name='Second Challenge',
            activation_date=timezone.now() + timedelta(days=-6),
            deactivation_date=timezone.now() + timedelta(days=8)
        )
        challenge_second.publish()
        challenge_second.save()

        # Participate and complete
        challenge_first.participants\
            .create(user=user)\
            .entries.create()

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:challenges-current'), {'exclude-done': 'true'})

        self.assertEqual(response.data['id'], challenge_second.id, "Unexpected challenge returned.")

class TestParticipantPicture(APITestCase):

    def test_adding_caption_to_participant_picture_that_exists(self):
        user = create_test_regular_user('anon')

        challenge_first = Challenge.objects.create(
            name='First Challenge',
            activation_date=timezone.now() + timedelta(days=-7),
            deactivation_date=timezone.now() + timedelta(days=7,),
            type=2
        )
        challenge_first.publish()
        challenge_first.save()

        participant = Participant.objects.create(user=user,
                                   challenge=challenge_first,
                                   date_created=timezone.now(),
                                   date_completed=timezone.now())

        question = PictureQuestion.objects.create(challenge=challenge_first,
                                                  text="A Question?")

        ParticipantPicture.objects.create(participant=participant,
                                          question=question)


        self.client.force_authenticate(user=user)

        response = self.client.post(reverse('api:participantpicture-caption', kwargs={'pk' : participant.id}),
                                    data={'caption':"caption words"})
        self.assertEquals(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_adding_caption_to_participant_picture_that_does_not_exist(self):
        user = create_test_regular_user('anon')

        challenge_first = Challenge.objects.create(
            name='First Challenge',
            activation_date=timezone.now() + timedelta(days=-7),
            deactivation_date=timezone.now() + timedelta(days=7,),
            type=2
        )
        challenge_first.publish()
        challenge_first.save()

        participant = Participant.objects.create(user=user,
                                   challenge=challenge_first,
                                   date_created=timezone.now(),
                                   date_completed=timezone.now())

        question = PictureQuestion.objects.create(challenge=challenge_first,
                                                  text="A Question?")


        self.client.force_authenticate(user=user)

        response = self.client.post(reverse('api:participantpicture-caption', kwargs={'pk' : participant.id}),
                                    data={'caption':"caption words"})
        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)

# ==== #
# Tips #
# ==== #


class TestTipModel(TestCase):

    def setUp(self):
        self.user = create_test_admin_user()

    def tearDown(self):
        self.user.delete()

    def test_create_tip(self):
        tip = create_tip()
        self.assertIsNotNone(tip, 'Tip not created')
        self.assertEqual(tip.title, 'Test tip', 'Test tip title was not set.')

    # def test_cover_image_url(self):
    #     self.skipTest('Needs to instantiate a wagtail Image')
    #     # TODO: Instatiate Image
    #     from django.core.files.images import ImageFile
    #     from wagtail.wagtailimages.models import Image
    #
    #     image = Image(
    #         title="Image title",
    #
    #         # image_file is your StringIO/BytesIO object
    #         file=ImageFile(image_file, name="image-filename.jpg"),
    #     )
    #     image.save()


class TestTipAPI(APITestCase):

    def setUp(self):
        self.user = create_test_admin_user()
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

    def test_cover_none(self):
        """When a Tip does not have a cover image set, the image url must be None."""
        tip = create_tip()
        response = self.client.get(reverse('api:tips-detail', kwargs={'pk': tip.pk}))
        self.assertIsNone(response.data['cover_image_url'], 'Cover image url is not None.')

    def test_inline_favourite_flag(self):
        """The tip itself should have a field indicating that it is favourited for the current user."""
        user = create_test_regular_user()
        tip1 = create_tip(title='Fav tip')
        tip2 = create_tip(title='Unfav tip')

        publish_page(user, tip1)
        publish_page(user, tip2)

        tip1.favourites.create(user=user)

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:tips-list'))

        # Tips are ordered from newest to oldest.
        self.assertTrue(response.data[1]['is_favourite'], "Tip 1 was not favourited.")
        self.assertFalse(response.data[0]['is_favourite'], "Tip 2 was not favourited.")

    def test_inline_favourite_flag_removed(self):
        """Flag should be false when a tip was removed from favourites."""
        user = create_test_regular_user()
        tip1 = create_tip(title='Fav tip')

        publish_page(user, tip1)

        fav = tip1.favourites.create(user=user)
        fav.unfavourite()
        fav.save()

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:tips-list'))

        self.assertFalse(response.data[0]['is_favourite'], "Tip 1 was still favourited.")


class TestFavouriteAPI(APITestCase):
    """Testing favouriting functionality via Tip sub routes."""

    @staticmethod
    def create_regular_user(username='AnonReg'):
        return RegUser.objects.create(username=username, email='anon-reg@ymous.org', password='Blarg',
                                      is_staff=False, is_superuser=False)

    def test_favouriting(self):
        user = self.create_regular_user()
        tip = create_tip('Tip 1')

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:tips-favourite', kwargs={'pk': tip.id}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_duplicate_favourites(self):
        """Favouriting a Tip more than once should not fail."""

        user = self.create_regular_user()
        tip = create_tip('Tip 1')

        # Once
        tip.favourites.create(user=user)

        # Twice
        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:tips-favourite', kwargs={'pk': tip.id}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, "Favouriting a Tip a second time failed.")

    def test_unfavouriting(self):
        user = self.create_regular_user()
        tip = create_tip('Tip 1')
        fav = TipFavourite.objects.create(
            user=user,
            tip=tip
        )

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:tips-unfavourite', kwargs={'pk': tip.id}))
        updated_fav = TipFavourite.objects.get(id=fav.id)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(updated_fav.is_active)

    def test_favourite_again(self):
        """After a Tip has been favourited and unfavourited, it should be favourted again."""
        user = self.create_regular_user()
        tip = create_tip('Tip 1')

        fav = tip.favourites.create(user=user)
        fav.unfavourite()
        fav.save()

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:tips-favourite', kwargs={'pk': tip.id}))

        updated_fav = TipFavourite.objects.get(user_id=user.id, tip_id=tip.id)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(updated_fav.is_active, "Updated Tip is not favourited.")


    def test_favourite_list(self):
        user = self.create_regular_user()
        tip1 = create_tip('Tip 1')
        tip2 = create_tip('Tip 2')
        publish_page(user, tip1)
        publish_page(user, tip2)
        TipFavourite.objects.create(user=user, tip=tip2)

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:tips-favourites'))

        self.assertEqual(response.status_code, status.HTTP_200_OK, "Listing favourite tips failed.")
        self.assertEqual(len(response.data), 1, "Unexpected number of favourite tips returned.")
        self.assertEqual(response.data[0].get('id', None), tip2.id, "Returned unexpected favourite tip.")

    def test_favourite_user_access(self):
        admin = create_test_admin_user('Admin User')

        tip1 = create_tip('Tip 1')
        tip2 = create_tip('Tip 2')
        publish_page(admin, tip1)
        publish_page(admin, tip2)

        user1 = self.create_regular_user('User 1')
        user2 = self.create_regular_user('User 2')
        TipFavourite.objects.create(user=user1, tip=tip1)
        TipFavourite.objects.create(user=user2, tip=tip2)

        self.client.force_authenticate(user=user2)
        response = self.client.get(reverse('api:tips-favourites'), format='json')

        self.assertEqual(len(response.data), 1, "Unexpected number of favourite tips returned.")
        self.assertEqual(response.data[0].get('id', None), tip2.id)


# ===== #
# Goals #
# ===== #


class TestWeekCalc(unittest.TestCase):

    def test_week_diff_basic(self):
        start = datetime(2017, 2, 1)
        end = datetime(2017, 2, 15)

        self.assertEqual(2, WeekCalc.week_diff(start, end, WeekCalc.Rounding.DOWN),
                         "Week calculation unexpected result")

    def test_week_diff_up(self):
        start = datetime(2017, 2, 1)
        end = datetime(2017, 2, 17)

        self.assertEqual(3, WeekCalc.week_diff(start, end, WeekCalc.Rounding.UP),
                         "Week calculation unexpected result.")

    def test_week_diff_round_down(self):
        start = datetime(2017, 2, 1)
        end = datetime(2017, 2, 17)

        self.assertEqual(2, WeekCalc.week_diff(start, end, WeekCalc.Rounding.DOWN),
                         "Week calculation unexpected result.")

    def test_week_diff_seven(self):
        """Ensure that when two days are separated by seven days, a full week will be counted. Historic issue with
        frontend counting days inclusively.
        """
        start = datetime(2017, 2, 1)
        end = datetime(2017, 2, 8)

        self.assertEqual(1, WeekCalc.week_diff(start, end, WeekCalc.Rounding.UP),
                         "Expected one full week.")

    def test_day_diff_basic(self):
        start = datetime(2017, 2, 1)
        end = datetime(2017, 2, 17)

        self.assertEqual(16, WeekCalc.day_diff(start, end),
                         "Day calculation unexpected result.")

    def test_remainder_basic(self):
        start = datetime(2017, 2, 1)
        end = datetime(2017, 2, 18)

        self.assertEqual(3, WeekCalc.remainder(start, end),
                         "Remainder calculation unexpected result.")


class TestGoalModel(TestCase):

    def test_value_property(self):
        user = create_test_regular_user()
        goal = create_goal('Goal 1', user, 1000)
        goal.transactions.create(date=timezone.now(), value=100)
        goal.transactions.create(date=timezone.now(), value=-90)
        goal.transactions.create(date=timezone.now(), value=300)
        goal.transactions.create(date=timezone.now(), value=-50)

        self.assertEqual(goal.value, 260, "Unexpected Goal value.")

    def test_week_count(self):
        user = create_test_regular_user()
        goal = Goal.objects.create(
            name='Goal 1',
            user=user,
            target=25000,
            start_date=timezone.make_aware(datetime(2017, 2, 1)),
            end_date=timezone.make_aware(datetime(2017, 2, 16))
        )
        self.assertEqual(3, goal.weeks, "Unexpected number of weeks.")

    def test_weeks_to_now(self):
        dt = timezone.make_aware(datetime(2017, 2, 8))
        with patch.object(timezone, 'now', lambda: dt):
            user = create_test_regular_user()
            goal = Goal.objects.create(
                name='Goal 1',
                user=user,
                target=25000,
                start_date=timezone.make_aware(datetime(2017, 2, 1)).date(),
                end_date=timezone.make_aware(datetime(2017, 2, 16)).date()
            )
            self.assertEqual(1, goal.weeks_to_now, "Unexpected weeks left.")

    def test_weeks_left(self):
        dt = timezone.make_aware(datetime(2017, 2, 8))
        with patch.object(timezone, 'now', lambda: dt):
            user = create_test_regular_user()
            goal = Goal.objects.create(
                name='Goal 1',
                user=user,
                target=25000,
                start_date=date(2017, 2, 1),
                end_date=date(2017, 2, 16)
            )
            self.assertEqual(2, goal.weeks_left, "Unexpected weeks left.")

    def test_weekly_target(self):
        user = create_test_regular_user()
        goal = Goal.objects.create(
            name='Goal 1',
            user=user,
            target=1000,
            start_date=date(2017, 2, 1),
            end_date=date(2017, 3, 1)
        )

        self.assertEqual(250, goal.weekly_target, "Unexpected weekly target.")

    def test_weekly_average(self):
        dt = timezone.make_aware(datetime(2017, 2, 15))
        with patch.object(timezone, 'now', lambda: dt):
            user = create_test_regular_user()
            goal = Goal.objects.create(
                name='Goal 1',
                user=user,
                target=10000,
                start_date=date(2017, 2, 1),
                end_date=date(2017, 2, 28)
            )

            # Week 1
            goal.transactions.create(
                date=timezone.make_aware(datetime(2017, 2, 2)),
                value=200
            )

            # Week 2
            goal.transactions.create(
                date=timezone.make_aware(datetime(2017, 2, 9)),
                value=200
            )
            goal.transactions.create(
                date=timezone.make_aware(datetime(2017, 2, 10)),
                value=200
            )

            self.assertEqual(300, goal.weekly_average, "Unexpected weekly average.")

    def test_week_aggregates(self):
        user = create_test_regular_user()
        goal = Goal.objects.create(
            name='Goal 1',
            user=user,
            target=25000,
            start_date=date(2016, 11, 1),
            end_date=date(2016, 11, 25)
        )

        # Week 1
        goal.transactions.create(date=date(2016, 11, 2), value=100)

        # Week 2
        goal.transactions.create(date=date(2016, 11, 8), value=100)
        goal.transactions.create(date=date(2016, 11, 9), value=100)

        # Week 3
        goal.transactions.create(date=date(2016, 11, 15), value=100)
        goal.transactions.create(date=date(2016, 11, 16), value=100)
        goal.transactions.create(date=date(2016, 11, 17), value=100)

        # Week 4
        goal.transactions.create(date=date(2016, 11, 22), value=100)
        goal.transactions.create(date=date(2016, 11, 23), value=100)
        goal.transactions.create(date=date(2016, 11, 24), value=100)
        goal.transactions.create(date=date(2016, 11, 25), value=100)

        weekly_aggregates = goal.get_weekly_aggregates()

        self.assertEqual(weekly_aggregates[0], 100)
        self.assertEqual(weekly_aggregates[1], 200)
        self.assertEqual(weekly_aggregates[2], 300)
        self.assertEqual(weekly_aggregates[3], 400)


class TestGoalAPI(APITestCase):

    @staticmethod
    def find_by_attr(lst, attr, val, default=None):
        """
        Helper to find dict in list.
        :param lst: List to search
        :param attr: Name of dict property to match
        :param val: Value to match
        :param default: Value to return if not found
        :return:
        """
        try:
            return [e for e in lst if e.get(attr, None) == val][0]
        except IndexError:
            return default

    @staticmethod
    def create_staff_user(username='AnonStaff'):
        return User.objects.create(username=username, email='anon@ymous.org', password='Blarg',
                                   is_staff=True, is_superuser=False)

    @staticmethod
    def create_regular_user(username='AnonReg'):
        return RegUser.objects.create(username=username, email='anon-reg@ymous.org', password='Blarg',
                                      is_staff=False, is_superuser=False)

    @staticmethod
    def create_goal(name, user, target):
        return Goal.objects.create(name=name, user=user, target=target,
                                   start_date=timezone.now(), end_date=timezone.now())

    def test_user_list_all_restriction(self):
        """A user must not see other user's Goals when listing all.
        """
        user_1 = self.create_regular_user('User 1')
        user_2 = self.create_regular_user('User 2')

        goal_1 = self.create_goal('Goal 1', user_1, 900)
        goal_2 = self.create_goal('Goal 2', user_2, 900)

        # Authenticate User 1, request Goals for User 2
        self.client.force_authenticate(user=user_1)
        response = self.client.get(reverse('api:goals-detail', kwargs={'pk': goal_2.id}), format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_filter_by_owned(self):
        """User must be able to retrieve their own Goals."""
        user = self.create_regular_user('User 1')
        goal = self.create_goal('Goal 1', user, 1000)

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:goals-list'))

        goal_data = self.find_by_attr(response.data, 'name', 'Goal 1', {})

        self.assertEqual(response.status_code, status.HTTP_200_OK, "Request failed.")
        self.assertEqual(goal.id, goal_data.get('id', None), "Retrieved goal is not the same as created goal.")

    def test_user_goal_create(self):
        """User must be able to create their own goals."""
        user = self.create_regular_user('User 1')

        data = {
            "name": "Goal 1",
            "transactions": [],
            "start_date": datetime.utcnow().strftime('%Y-%m-%d'),
            "end_date": datetime.utcnow().strftime('%Y-%m-%d'),
            "target": 1000,
            "image": None,
            "weekly_target": 100
        }

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:goals-list'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_goal_update(self):
        """User must be able to update their own goals."""

        # Create Models
        user = self.create_regular_user('User 1')
        goal = self.create_goal('Goal 1', user, 1000)

        # Send updates
        data = {
            "name": "Goal 2",
            "start_date": '2015-11-01',
            "end_date": '2015-11-30',
            "target": 9000,
            "image": None,
            "weekly_target": 1000
        }

        self.client.force_authenticate(user=user)
        response = self.client.put(reverse('api:goals-detail', kwargs={'pk': goal.pk}), data, format='json')

        updated_goal = Goal.objects.get(pk=goal.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK, "Request was unsuccessful.")
        self.assertEqual(goal.pk, updated_goal.pk, "Returned Goal was not the same instance as the sent goal.")
        self.assertEqual("Goal 2", updated_goal.name, "Name was not updated.")
        self.assertEqual(9000, updated_goal.target, "Target was not updated.")
        self.assertEqual(date(2015, 11, 30), updated_goal.end_date, "Goal date was not updated.")

    def test_user_goal_update_modified_flags(self):
        """Flag fields must be set to record when a user modifies the goal end date or target"""

        # Create Models
        user = self.create_regular_user('User 1')
        goal = self.create_goal('Goal 1', user, 1000)

        # Send updates
        data = {
            "name": "Goal 2",
            "start_date": '2015-11-01',
            "end_date": '2015-11-30',
            "target": 9000,
            "image": None,
            "weekly_target": 2500
        }

        self.assertEquals(goal.end_date_modified, None, "Unmodified goal end date should be null")
        self.assertEquals(goal.target_modified, None, "Unmodified goal target should be null")

        self.client.force_authenticate(user=user)
        response = self.client.put(reverse('api:goals-detail', kwargs={'pk': goal.pk}), data, format='json')

        updated_goal = Goal.objects.get(pk=goal.pk)

        # Date modified are within two seconds of current check
        self.assertAlmostEqual(updated_goal.end_date_modified, datetime.now(timezone.utc),
                               msg="Modified date not close enough to when was actually modified",
                               delta=timedelta(seconds=2))

        self.assertAlmostEqual(updated_goal.target_modified, datetime.now(timezone.utc),
                               msg="Modified date not close enough to when was actually modified",
                               delta=timedelta(seconds=2))

    def test_user_goal_create_for_other_restricted(self):
        """A User must not be able to create a Goal for another user."""

        user_1 = self.create_regular_user('User 1')
        user_2 = self.create_regular_user('User 2')

        data = {
            "name": "Goal 1",
            "transactions": [],
            "start_date": datetime.utcnow().strftime('%Y-%m-%d'),
            "end_date": datetime.utcnow().strftime('%Y-%m-%d'),
            "target": 1000,
            "weekly_target": 250,
            "image": None,
            "user": user_2.id  # Different user
        }

        self.client.force_authenticate(user=user_1)
        response = self.client.post(reverse('api:goals-list'), data, format='json')

        goal = Goal.objects.get(id=response.data['id'])

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Creating Goal failed.")
        self.assertEqual(user_1, goal.user, "User managed to create Goal for someone else.")

    def test_goal_delete(self):
        user = create_test_regular_user()
        goal = create_goal('Goal 1', user, 1000)

        self.client.force_authenticate(user=user)
        response = self.client.delete(reverse('api:goals-detail', kwargs={'pk': goal.pk}))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, "Goal delete request failed.")

        updated_goal = Goal.objects.get(id=goal.id)
        self.assertFalse(updated_goal.is_active, "Goal was not marked as inactive.")

    def test_deleted_goal_filter(self):
        user = create_test_regular_user()
        goal = create_goal('Goal 1', user, 1000)
        goal.deactivate()
        goal.save()

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:goals-list'), format=json)

        self.assertEqual(len(response.data), 0, "Deleted Goal included in list.")


class TestGoalTransactionAPI(APITestCase):

    def test_create_transactions(self):
        user = create_test_regular_user()
        goal = create_goal('Goal 1', user, 1000)

        data = [{
            "date": datetime.utcnow().isoformat(),
            "value": 100
        }]

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:goals-transactions', kwargs={'pk': goal.pk}),
                                    data, format='json')
        transactions = goal.transactions.all()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Creating Transactions request failed")
        self.assertEqual(len(transactions), 1, "No transactions created.")
        self.assertEqual(transactions[0].value, 100, "Transaction value was not the same")

    def test_create_avoid_duplicates(self):
        user = create_test_regular_user()
        goal = create_goal('Goal 1', user, 1000)
        trans = GoalTransaction.objects.create(goal=goal, date=timezone.now(), value=90)
        trans2 = GoalTransaction.objects.create(goal=goal, date=timezone.now(), value=10)
        trans3 = GoalTransaction.objects.create(goal=goal, date=timezone.now(), value=110)

        data = [{
            "date": trans.date.isoformat(),
            "value": trans.value
        }]

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:goals-transactions', kwargs={'pk': goal.pk}),
                                    data, format='json')
        transactions = goal.transactions.all()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Creating Transactions request failed")
        self.assertEqual(len(transactions), 3, "Duplicate was possibly added.")
        self.assertEqual(trans, transactions[0],
                         "Returned transaction was not the same as the originally created one")

    def test_goal_update_transaction_avoid_duplicates(self):
        user = create_test_regular_user()
        goal = create_goal('Goal 1', user, 1000)
        trans = GoalTransaction.objects.create(goal=goal, date=timezone.now(), value=50)
        trans2 = GoalTransaction.objects.create(goal=goal, date=timezone.now()+timezone.timedelta(seconds=1), value=100)
        trans3 = GoalTransaction.objects.create(goal=goal, date=timezone.now()+timezone.timedelta(seconds=2), value=200)

        next_date = timezone.now()+timezone.timedelta(seconds=3)

        data = {
            "name": "Goal 2",
            "start_date": datetime.utcnow().strftime('%Y-%m-%d'),
            "end_date": datetime.utcnow().strftime('%Y-%m-%d'),
            "target": 9000,
            "weekly_target": 1000,
            "transactions": [{
                # Duplicate
                "date": trans.date.isoformat(),
                "value": trans.value
            }, {
                # New transaction
                "date": next_date.isoformat(),
                "value": 300
            }],
            "image": None
        }

        self.client.force_authenticate(user=user)
        response = self.client.put(reverse('api:goals-detail', kwargs={'pk': goal.pk}), data, format='json')
        updated_goal = Goal.objects.first()
        updated_trans = goal.transactions.all().order_by('date')

        self.assertEqual(response.status_code, status.HTTP_200_OK, "Update Goal request failed.")
        self.assertEqual(len(updated_trans), 4, "Unexpected number of transactions.")
        self.assertEqual(updated_trans[0], trans, "Unexpected transaction.")
        self.assertEqual(updated_trans[1], trans2, "Unexpected transaction.")
        self.assertEqual(updated_trans[2], trans3, "Unexpected transaction.")
        self.assertEqual(updated_trans[3].value, 300, "Unexpected transaction.")


class TestGoalPrototypesAPI(APITestCase):

    def test_goal_proto_list(self):
        user = create_test_regular_user('anon')
        proto = GoalPrototype.objects.create(name='Proto 1')
        proto.activate()
        proto.save()

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:goal-prototypes-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK, "Listing Goal prototypes failed.")
        self.assertEqual(len(response.data), 1, "No prototypes returned.")

    def test_goal_create_with_proto(self):
        """Test basic Goal creation from a prototype."""
        user = create_test_regular_user('anon')
        proto = GoalPrototype.objects.create(name='Proto 1')

        data = {
            'name': 'Goal 1',
            'target': 12000,
            'start_date': datetime(2016, 11, 1, tzinfo=timezone.utc).strftime('%Y-%m-%d'),
            'end_date': datetime(2016, 11, 30, tzinfo=timezone.utc).strftime('%Y-%m-%d'),
            'prototype': proto.id,
            "weekly_target": 1000
        }

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:goals-list'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Create Goal failed.")

        created_goal = Goal.objects.get(id=response.data['id'])
        self.assertEqual(created_goal.prototype, proto, "Goal Prototype was not set.")

    def test_goal_proto_num_users_field_caculation(self):
        user1 = create_test_regular_user("sam")
        user2 = create_test_regular_user("dan")
        user3 = create_test_regular_user("vlad")

        proto1 = GoalPrototype.objects.create(name='Proto 1')
        proto2 = GoalPrototype.objects.create(name='Proto 2')

        goal1 = Goal.objects.create(name="Name One", user=user1, target=1000, start_date=timezone.now(),
                                    end_date=timezone.now(), prototype=proto1)
        goal2 = Goal.objects.create(name="Name Two", user=user1, target=1000, start_date=timezone.now(),
                                    end_date=timezone.now(), prototype=proto2)
        goal3 = Goal.objects.create(name="Name Tree", user=user3, target=1000, start_date=timezone.now(),
                                    end_date=timezone.now(), prototype=proto1)

        self.assertNotEqual(proto1.num_users, 0, "num_users field on Goal Prototype not updated correctly")
        self.assertEquals(proto1.num_users, 2, "num_users field on Goal Prototype not calculated correctly")
        self.assertEquals(proto2.num_users, 1, "num_users field on Goal Prototype not calculated correctly")


class TestGoalPrototypesModel(TestCase):

    def test_goal_proto_num_users_field_caculation(self):
        user1 = create_test_regular_user("sam")
        user2 = create_test_regular_user("dan")
        user3 = create_test_regular_user("vlad")

        proto1 = GoalPrototype.objects.create(name='Proto 1')
        proto2 = GoalPrototype.objects.create(name='Proto 2')

        goal1 = Goal.objects.create(name="Name One", user=user1, target=1000, start_date=timezone.now(),
                                    end_date=timezone.now(), prototype=proto1)
        goal2 = Goal.objects.create(name="Name Two", user=user1, target=1000, start_date=timezone.now(),
                                    end_date=timezone.now(), prototype=proto2)
        goal3 = Goal.objects.create(name="Name Tree", user=user3, target=1000, start_date=timezone.now(),
                                    end_date=timezone.now(), prototype=proto1)

        self.assertNotEqual(proto1.num_users, 0, "num_users field on Goal Prototype not updated correctly")
        self.assertEquals(proto1.num_users, 2, "num_users field on Goal Prototype not calculated correctly")
        self.assertEquals(proto2.num_users, 1, "num_users field on Goal Prototype not calculated correctly")


# ============ #
# Achievements #
# ============ #


class TestWeeklyStreaks(TestCase):

    def test_basic_streak(self):
        now = datetime(2016, 11, 30, tzinfo=timezone.utc)

        user = create_test_regular_user('anon')
        goal = Goal.objects.create(
            name='Goal 1',
            user=user,
            target=100000,
            start_date=now - timedelta(days=-30),
            end_date=now
        )

        # Three week savings streak
        # Week 3
        goal.transactions.create(value=1000, date=now + timedelta(days=-14))
        goal.transactions.create(value=1000, date=now + timedelta(days=-15))
        goal.transactions.create(value=1000, date=now + timedelta(days=-16))

        # Week 4
        goal.transactions.create(value=2000, date=now + timedelta(days=-7))
        goal.transactions.create(value=2000, date=now + timedelta(days=-8))
        goal.transactions.create(value=2000, date=now + timedelta(days=-9))

        # Week 5
        goal.transactions.create(value=3000, date=now + timedelta(days=-1))
        goal.transactions.create(value=3000, date=now + timedelta(days=-2))
        goal.transactions.create(value=3000, date=now + timedelta(days=-3))

        streak = Goal.get_current_streak(user, now)

        self.assertEqual(streak, 3, "Unexpected weekly streak.")

    def test_broken_streak(self):
        now = datetime(2016, 11, 30, tzinfo=timezone.utc)

        user = create_test_regular_user('anon')
        goal = Goal.objects.create(
            name='Goal 1',
            user=user,
            target=100000,
            start_date=now - timedelta(days=30),
            end_date=now
        )

        # Week 2
        goal.transactions.create(value=1000, date=now + timedelta(days=-21))
        goal.transactions.create(value=1000, date=now + timedelta(days=-22))
        goal.transactions.create(value=1000, date=now + timedelta(days=-23))

        # Streak breaks here
        # Week 4
        goal.transactions.create(value=2000, date=now + timedelta(days=-7))
        goal.transactions.create(value=2000, date=now + timedelta(days=-8))
        goal.transactions.create(value=2000, date=now + timedelta(days=-9))

        # Week 5
        goal.transactions.create(value=3000, date=now + timedelta(days=-1))
        goal.transactions.create(value=3000, date=now + timedelta(days=-2))
        goal.transactions.create(value=3000, date=now + timedelta(days=-3))

        streak = Goal.get_current_streak(user, now)

        self.assertEqual(streak, 2, "Unexpected weekly streak.")

    def test_inactivity(self):
        """When the user has saved before, but has been inactive since, the streak should be 0."""
        now = datetime(2016, 11, 30, tzinfo=timezone.utc)

        user = create_test_regular_user('anon')
        goal = Goal.objects.create(
            name='Goal 1',
            user=user,
            target=100000,
            start_date=now - timedelta(days=30),
            end_date=now
        )

        # Week 1
        goal.transactions.create(value=2000, date=now + timedelta(days=-28))
        goal.transactions.create(value=2000, date=now + timedelta(days=-29))
        goal.transactions.create(value=2000, date=now + timedelta(days=-30))

        # Week 2
        goal.transactions.create(value=1000, date=now + timedelta(days=-21))
        goal.transactions.create(value=1000, date=now + timedelta(days=-22))
        goal.transactions.create(value=1000, date=now + timedelta(days=-23))

        # Streak breaks here

        streak = Goal.get_current_streak(user, now)

        self.assertEqual(streak, 0, "Unexpected weekly streak.")

    def test_no_savings(self):
        now = datetime(2016, 11, 30, tzinfo=timezone.utc)

        user = create_test_regular_user('anon')
        goal = Goal.objects.create(
            name='Goal 1',
            user=user,
            target=100000,
            start_date=now - timedelta(days=30),
            end_date=now
        )

        streak = Goal.get_current_streak(user, now)

        self.assertEqual(streak, 0, "Unexpected weekly streak.")


class TestWeeklyTargetStreaks(TestCase):

    def test_basic_streak_2(self):
        now = datetime(2017, 1, 27, tzinfo=timezone.utc)

        user = create_test_regular_user('anon')
        goal = Goal.objects.create(
            name='Goal 1',
            user=user,
            target=36, #Thus the weekly target is 6 for 6 weeks to reach the target
            start_date=now + timedelta(days=-36), #Goal duration is 6 weeks
            end_date=now,
        )

        # Week 5
        goal.transactions.create(value=1, date=now + timedelta(days=-7))
        goal.transactions.create(value=2, date=now + timedelta(days=-8))
        goal.transactions.create(value=3, date=now + timedelta(days=-9))

        # Week 6
        goal.transactions.create(value=1, date=now + timedelta(days=-1))
        goal.transactions.create(value=3, date=now + timedelta(days=-2))
        goal.transactions.create(value=3, date=now + timedelta(days=-3))

        streak = Goal.get_current_weekly_target_badge(user, goal, now)

        self.assertEqual(streak, 2, "Unexpected streak returned, should be 2")

    def test_basic_streak_4(self):
        now = datetime(2017, 1, 27, tzinfo=timezone.utc)

        user = create_test_regular_user('anon')
        goal = Goal.objects.create(
            name='Goal 1',
            user=user,
            target=36, #Thus the weekly target is 6 for 6 weeks to reach the target
            start_date=now + timedelta(days=-36), #Goal duration is 6 weeks
            end_date=now,
        )

        # Week 3
        goal.transactions.create(value=1, date=now + timedelta(days=-21))
        goal.transactions.create(value=2, date=now + timedelta(days=-23))
        goal.transactions.create(value=3, date=now + timedelta(days=-25))

        # Week 4
        goal.transactions.create(value=1, date=now + timedelta(days=-14))
        goal.transactions.create(value=3, date=now + timedelta(days=-15))
        goal.transactions.create(value=3, date=now + timedelta(days=-18))

        # Week 5
        goal.transactions.create(value=1, date=now + timedelta(days=-7))
        goal.transactions.create(value=2, date=now + timedelta(days=-8))
        goal.transactions.create(value=3, date=now + timedelta(days=-9))

        # Week 6
        goal.transactions.create(value=1, date=now + timedelta(days=-1))
        goal.transactions.create(value=3, date=now + timedelta(days=-2))
        goal.transactions.create(value=3, date=now + timedelta(days=-3))

        streak = Goal.get_current_weekly_target_badge(user, goal, now)

        self.assertEqual(streak, 4, "Unexpected streak returned, should be 4")

    def test_basic_streak_6(self):
        now = datetime(2017, 1, 27, tzinfo=timezone.utc)

        user = create_test_regular_user('anon')
        goal = Goal.objects.create(
            name='Goal 1',
            user=user,
            target=36, #Thus the weekly target is 6 for 6 weeks to reach the target
            start_date=now + timedelta(days=-36), #Goal duration is 6 weeks
            end_date=now,
        )

        # Week 1
        goal.transactions.create(value=1, date=now + timedelta(days=-35))
        goal.transactions.create(value=2, date=now + timedelta(days=-36))
        goal.transactions.create(value=3, date=now + timedelta(days=-37))

        # Week 2
        goal.transactions.create(value=1, date=now + timedelta(days=-28))
        goal.transactions.create(value=3, date=now + timedelta(days=-29))
        goal.transactions.create(value=3, date=now + timedelta(days=-30))

        # Week 3
        goal.transactions.create(value=1, date=now + timedelta(days=-21))
        goal.transactions.create(value=2, date=now + timedelta(days=-23))
        goal.transactions.create(value=3, date=now + timedelta(days=-25))

        # Week 4
        goal.transactions.create(value=1, date=now + timedelta(days=-14))
        goal.transactions.create(value=3, date=now + timedelta(days=-15))
        goal.transactions.create(value=3, date=now + timedelta(days=-18))

        # Week 5
        goal.transactions.create(value=1, date=now + timedelta(days=-7))
        goal.transactions.create(value=2, date=now + timedelta(days=-8))
        goal.transactions.create(value=3, date=now + timedelta(days=-9))

        # Week 6
        goal.transactions.create(value=1, date=now + timedelta(days=-1))
        goal.transactions.create(value=3, date=now + timedelta(days=-2))
        goal.transactions.create(value=3, date=now + timedelta(days=-3))

        streak = Goal.get_current_weekly_target_badge(user, goal, now)

        self.assertEqual(streak, 6, "Unexpected streak returned, should be 2")

    def test_broken_streak(self):
        now = datetime(2017, 1, 27, tzinfo=timezone.utc)

        user = create_test_regular_user('anon')
        goal = Goal.objects.create(
            name='Goal 1',
            user=user,
            target=36, #Thus the weekly target is 6 for 6 weeks to reach the target
            start_date=now + timedelta(days=-36), #Goal duration is 6 weeks
            end_date=now,
        )

        # Week 3
        goal.transactions.create(value=1, date=now + timedelta(days=-21))
        goal.transactions.create(value=2, date=now + timedelta(days=-23))
        goal.transactions.create(value=3, date=now + timedelta(days=-25))

        #Streak breaks here

        # Week 5
        goal.transactions.create(value=1, date=now + timedelta(days=-7))
        goal.transactions.create(value=2, date=now + timedelta(days=-8))
        goal.transactions.create(value=3, date=now + timedelta(days=-9))

        # Week 6
        goal.transactions.create(value=1, date=now + timedelta(days=-1))
        goal.transactions.create(value=3, date=now + timedelta(days=-2))
        goal.transactions.create(value=3, date=now + timedelta(days=-3))

        streak = Goal.get_current_weekly_target_badge(user, goal, now)

        self.assertEqual(streak, 2, "Unexpected weekly streak, should be 2")

    def test_inactivity(self):
        """When the user has saved before, but has been inactive since, the streak should be 0."""
        now = datetime(2017, 1, 27, tzinfo=timezone.utc)

        user = create_test_regular_user('anon')
        goal = Goal.objects.create(
            name='Goal 1',
            user=user,
            target=36,  # Thus the weekly target is 6 for 6 weeks to reach the target
            start_date=now + timedelta(days=-36),  # Goal duration is 6 weeks
            end_date=now,
        )

        # Week 1
        goal.transactions.create(value=2, date=now + timedelta(days=-28))
        goal.transactions.create(value=2, date=now + timedelta(days=-29))
        goal.transactions.create(value=5, date=now + timedelta(days=-30))

        # Week 2
        goal.transactions.create(value=2, date=now + timedelta(days=-21))
        goal.transactions.create(value=2, date=now + timedelta(days=-22))
        goal.transactions.create(value=5, date=now + timedelta(days=-23))

        # Streak breaks here

        streak = Goal.get_current_weekly_target_badge(user, goal, now)

        self.assertEqual(streak, 0, "Unexpected weekly streak, should be 0")

    def test_no_savings(self):
        now = datetime(2016, 11, 30, tzinfo=timezone.utc)

        user = create_test_regular_user('anon')
        goal = Goal.objects.create(
            name='Goal 1',
            user=user,
            target=100000,
            start_date=now - timedelta(days=30),
            end_date=now
        )

        streak = Goal.get_current_weekly_target_badge(user, goal, now)

        self.assertEqual(streak, 0, "Unexpected weekly streak, should be 0")


class TestAchievementAPI(APITestCase):

    def test_basic(self):
        """Basic test to ensure view is accessible."""
        user = create_test_regular_user('anon')

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:achievements', kwargs={'user_pk': user.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK, "Achievement request failed.")

    def test_last_saved(self):
        now = timezone.now()
        user = create_test_regular_user('anon')
        goal = Goal.objects.create(
            name='Goal 1',
            start_date=now - timedelta(days=30),
            end_date=now + timedelta(days=30),
            target=2000,
            user=user
        )
        goal.transactions.create(
            date=now - timedelta(days=21),
            value=100
        )
        goal.transactions.create(
            date=now - timedelta(days=20),
            value=100
        )

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:achievements', kwargs={'user_pk': user.pk}))

        self.assertEqual(response.data['weeks_since_saved'], 2, "Unexpected weeks since saved.")


class TestBadgeAwarding(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.goal_first_created = Badge.objects.create(name='First Goal')
        cls.goal_halfway = Badge.objects.create(name='First Goal Halfway')
        cls.goal_week_left = Badge.objects.create(name='Week Left')
        cls.goal_first_done = Badge.objects.create(name='First Goal Done')
        cls.transaction_first = Badge.objects.create(name='First Savings Created')
        cls.streak_2 = Badge.objects.create(name='2 Week Streak')
        cls.weekly_target_2 = Badge.objects.create(name='2 Weekly Target Streak of 2')
        cls.challenge_entry = Badge.objects.create(name='Challenge Participation')
        cls.challenge_win = Badge.objects.create(name='Challenge Win')

        site = Site.objects.get(is_default_site=True)
        BadgeSettings.objects.create(
            site=site,
            goal_first_created=cls.goal_first_created,
            goal_half=cls.goal_halfway,
            goal_week_left=cls.goal_week_left,
            goal_first_done=cls.goal_first_done,
            transaction_first=cls.transaction_first,
            streak_2=cls.streak_2,
            challenge_entry=cls.challenge_entry,
            weekly_target_2=cls.weekly_target_2,
            challenge_win=cls.challenge_win
        )

    # ------------------------ #
    # Award First Goal Created #
    # ------------------------ #

    def test_first_goal(self):
        user = create_test_regular_user('anon')

        data = {
            'name': 'Goal 1',
            'target': 10000,
            'start_date': '2016-11-01',
            'end_date': '2016-11-30',
            'weekly_target': 2500
        }

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:goals-list'), data, format='json')

        self.assertEqual(len(response.data.get('new_badges', [])), 1, "Badge was not added to new Goal.")

    def test_avoid_first_twice(self):
        now = timezone.now()
        user = create_test_regular_user('anon')
        Goal.objects.create(
            name='Goal 1',
            user=user,
            target=100000,
            start_date=now - timedelta(days=30),
            end_date=now,
            weekly_target=5000
        )
        UserBadge.objects.create(user=user, badge=self.goal_first_created)

        data = {
            'name': 'Goal 1',
            'target': 10000,
            'start_date': '2016-11-01',
            'end_date': '2016-11-30',
            'weekly_target': 2500
        }

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:goals-list'), data, format='json')

        self.assertEqual(len(response.data['new_badges']), 0, "Badge was earned on second goal as well")

    # ------------------------ #
    # Award First Goal Reached #
    # ------------------------ #

    def test_first_goal_done(self):
        now = timezone.now()
        user = create_test_regular_user('anon')
        goal = Goal.objects.create(
            name='Goal 1',
            user=user,
            target=10000,
            start_date=now - timedelta(days=30),
            end_date=now + timedelta(days=30),
            weekly_target=500
        )

        data = [{
            'date': timezone.now().isoformat(),
            'value': 10000
        }]

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:goals-transactions', kwargs={'pk': goal.pk}), data, format='json')

        self.assertNotEqual(len(response.data['new_badges']), 0, "No new Badges were returned.")

        badges = [b for b in response.data['new_badges'] if b['name'] == self.goal_first_done.name]
        self.assertEqual(len(badges), 1, "Expected badge was not included")

    def test_first_goal_done_badge_duplicate(self):
        """Test to see what happens when a user already has a first goal badge, and gets awarded it again"""
        now = timezone.now()
        user = create_test_regular_user('anon')
        profile = Profile.objects.create(user=user)

        goal = Goal.objects.create(
            name='Goal',
            user=user,
            target=5000,
            start_date=now - timedelta(days=30),
            end_date=now + timedelta(days=30)
        )

        # Create a dummy request
        site = Site.objects.get(is_default_site=True)
        request = HttpRequest
        request.site = site

        # Badge should be returned the first time the goal is created
        first_goal_badge = award_first_goal(request, goal)
        self.assertIsNotNone(first_goal_badge, "Goal added badge not awarded")

        # Badge is not returned when goal is created again
        first_goal_badge_again = award_first_goal(request, goal)
        self.assertIsNone(first_goal_badge_again, "Goal added badge was repeatedly awarded")

    # ------------------------ #
    # Award First Goal Halfway #
    # ------------------------ #

    def test_goal_halfway(self):
        dt = timezone.make_aware(datetime(2017, 2, 15))
        with patch.object(timezone, 'now', lambda: dt):
            user = create_test_regular_user('anon')
            goal = Goal.objects.create(
                name='Goal 1',
                user=user,
                target=10000,
                start_date=timezone.make_aware(datetime(2017, 2, 1)),
                end_date=timezone.make_aware(datetime(2017, 2, 28))
            )

            data = [{
                'date': timezone.now().isoformat(),
                'value': 5000
            }]

            self.client.force_authenticate(user=user)
            response = self.client.post(reverse('api:goals-transactions', kwargs={'pk': goal.pk}), data, format='json')

            self.assertNotEqual(len(response.data), 0, "No new Badges were returned.")

            badges = [b for b in response.data['new_badges'] if b['name'] == self.goal_halfway.name]
            self.assertEqual(len(badges), 1, "Expected badge was not included")

    def test_goal_halfway_early(self):
        """User should not receive this badge before the halfway mark"""
        now = timezone.now()
        user = create_test_regular_user('anon')
        goal = Goal.objects.create(
            name='Goal 1',
            user=user,
            target=10000,
            start_date=now - timedelta(days=30),
            end_date=now + timedelta(days=30)
        )

        data = [{
            'date': now.isoformat(),
            'value': 3000  # Short of halfway
        }]

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:goals-transactions', kwargs={'pk': goal.pk}), data, format='json')

        badges = [b for b in response.data['new_badges'] if b['name'] == self.goal_halfway.name]
        self.assertEqual(len(badges), 0, "Badge was included unexpectedly")

    def test_goal_halfway_avoid_duplicate(self):
        now = timezone.now()
        user = create_test_regular_user('anon')
        goal = Goal.objects.create(
            name='Goal 1',
            user=user,
            target=10000,
            start_date=now - timedelta(days=30),
            end_date=now + timedelta(days=30)
        )

        self.client.force_authenticate(user=user)
        self.client.post(reverse('api:goals-transactions', kwargs={'pk': goal.pk}), [{
            'date': (now - timedelta(days=1)).isoformat(),
            'value': 5500  # Halfway
        }], format='json')

        response = self.client.post(reverse('api:goals-transactions', kwargs={'pk': goal.pk}), [{
            'date': now.isoformat(),
            'value': 1000  # Further over half
        }], format='json')

        badges = [b for b in response.data['new_badges'] if b['name'] == self.goal_halfway.name]
        self.assertEqual(len(badges), 0, "Badge was included unexpectedly")

    # ------------------ #
    # Goal One Week Left #
    # ------------------ #

    def test_goal_week_left(self):
        now = timezone.now()
        user = create_test_regular_user('anon')
        goal = Goal.objects.create(
            name='Goal 1',
            user=user,
            target=10000,
            start_date=now - timedelta(days=30),
            end_date=now + timedelta(days=3)  # Less than a week left
        )

        data = [{
            'date': now.isoformat(),
            'value': 1000
        }]

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:goals-transactions', kwargs={'pk': goal.pk}), data, format='json')

        badges = [b for b in response.data['new_badges'] if b['name'] == self.goal_week_left.name]
        self.assertEqual(len(badges), 1, "Expected badge was not included")

    # --------------------------- #
    # Award First Savings Created #
    # --------------------------- #

    def test_first_savings_created(self):
        now = timezone.now()
        user = create_test_regular_user('anon')
        goal = Goal.objects.create(
            name='Goal 1',
            user=user,
            target=10000,
            start_date=now - timedelta(days=30),
            end_date=now + timedelta(days=30)
        )

        data = [{
            'date': timezone.now().isoformat(),
            'value': 100
        }]

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:goals-transactions', kwargs={'pk': goal.pk}), data, format='json')

        self.assertNotEqual(len(response.data), 0, "No new Badges were returned.")

        badges = [b for b in response.data['new_badges'] if b['name'] == self.transaction_first.name]
        self.assertEqual(len(badges), 1, "Expected badge was not included")

    def test_first_savings_created_avoid_duplicate(self):
        now = timezone.now()
        user = create_test_regular_user('anon')
        goal = Goal.objects.create(
            name='Goal 1',
            user=user,
            target=10000,
            start_date=now - timedelta(days=30),
            end_date=now + timedelta(days=30)
        )

        self.client.force_authenticate(user=user)

        # First
        self.client.post(reverse('api:goals-transactions', kwargs={'pk': goal.pk}), [{
            'date': now,
            'value': 100
        }], format='json')

        # Second
        response = self.client.post(reverse('api:goals-transactions', kwargs={'pk': goal.pk}), [{
            'date': timezone.now().isoformat(),
            'value': 200
        }], format='json')

        badges = [b for b in response.data['new_badges'] if b['name'] == self.transaction_first.name]
        self.assertEqual(len(badges), 0, "First savings was unexpectedly awarded.")

    # -------------------------- #
    # Award Week Savings Streaks #
    # -------------------------- #

    def test_streak_2(self):
        now = timezone.now()
        user = create_test_regular_user('anon')
        goal = Goal.objects.create(
            name='Goal 1',
            user=user,
            target=10000,
            start_date=now - timedelta(days=30),
            end_date=now + timedelta(days=30)
        )
        goal.transactions.create(
            date=now - timedelta(days=7),  # One Week back
            value=100
        )
        data = [{
            'date': now.isoformat(),
            'value': 200
        }]

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:goals-transactions', kwargs={'pk': goal.pk}), data, format='json')

        badges = [b for b in response.data['new_badges'] if b['name'] == self.streak_2.name]
        self.assertEqual(len(badges), 1, "Expected badge was not included")

    # ----------------------------- #
    # Award Challenge participation #
    # ----------------------------- #

    def test_challenge_participation_freetext(self):
        user = create_test_regular_user('anon')
        profile = Profile.objects.create(user=user)

        challenge = Challenge.objects.create(
            name='Free Text Challenge',
            activation_date=timezone.now() + timedelta(days=-7),
            deactivation_date=timezone.now() + timedelta(days=7),
            type=3
        )

        question = FreeTextQuestion.objects.create(challenge=challenge, text="FreeTextQuestion1")

        challenge.publish()
        challenge.save()

        # Participate and complete, be awarded participation badge
        badge = challenge.participants \
            .create(user=user) \
            .entries.create()

        data = {
            "text": "abc",
            "date_answered": "2017-01-30T08:25:23.951+02:00",
            "participant": 1,
            "question": 1
        }

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:participantfreetext-list'), data, format='json')

        self.assertEquals(response.data['available'], True, "Badge not available")

        self.assertNotEquals(response.status_code, status.HTTP_400_BAD_REQUEST, "Badge not created")

        self.assertIsNotNone(badge, "Participation badge was not awarded")

    def test_challenge_participation_image(self):
        self.skipTest("Need to build a POST request")
        # TODO: Image challenge participation badge
        # Haven't been able to construct a POST request in order to test

    def test_challenge_participation_quiz(self):
        user = create_test_regular_user('anon')
        profile = Profile.objects.create(user=user)

        challenge = Challenge.objects.create(
            name='Quiz Challenge',
            activation_date=timezone.now() + timedelta(days=-7),
            deactivation_date=timezone.now() + timedelta(days=7),
            type=1
        )

        question = QuizQuestion.objects.create(challenge=challenge, text="QuizQuestion")
        questionOption1 = QuestionOption.objects.create(question=question, text="Question1")
        questionOption2 = QuestionOption.objects.create(question=question, text="Question2")

        challenge.publish()
        challenge.save()

        # Participate and complete, be awarded participation badge
        badge = challenge.participants \
            .create(user=user) \
            .entries.create()

        data = {
             "answers": [
                 {"selected_option": 1, "challenge": 1, "date_answered": "2017-01-30T16:59:26.054+02:00", "question": 1,
                  "user": 1, "participant": 1},
                 {"selected_option": 1, "challenge": 1, "date_answered": "2017-01-30T16:59:29.746+02:00", "question": 1,
                  "user": 1, "participant": 1}
             ],
             "date_completed": "2017-01-30T16:59:32.427+02:00",
             "participant": 1
        }

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:entries-list'), data, format='json')

        self.assertNotEquals(response.status_code, status.HTTP_400_BAD_REQUEST, "Badge not created")

        self.assertIsNotNone(badge, "Participation badge was not awarded")

    # -------------------------- #
    # Award Weekly Target Streaks #
    # -------------------------- #

    def test_weekly_target_2(self):
        now = timezone.now()
        user = create_test_regular_user('anon')
        goal = Goal.objects.create(
            name='Goal 1',
            user=user,
            target=100,
            start_date=now - timedelta(days=30),
            end_date=now + timedelta(days=30)
        )
        goal.transactions.create(
            date=now - timedelta(days=7),  # One Week back
            value=20
        )
        data = [{
            'date': now.isoformat(),
            'value': 20
        }]

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:goals-transactions', kwargs={'pk': goal.pk}), data, format='json')

        badges = [b for b in response.data['new_badges'] if b['name'] == self.weekly_target_2.name]
        self.assertEqual(len(badges), 1, "Expected badge was not included")

    # ---------------------- #
    # Award Challenge Winner #
    # ---------------------- #

    def test_challenge_win(self):
        user = create_test_regular_user('anon')
        profile = Profile.objects.create(user=user)

        challenge = Challenge.objects.create(
            name='First Challenge',
            activation_date=timezone.now() + timedelta(days=-7),
            deactivation_date=timezone.now() + timedelta(days=7)
        )

        challenge.publish()
        challenge.save()

        # Participate and complete
        challenge.participants \
            .create(user=user) \
            .entries.create()

        participant = Participant.objects.get(user=user, challenge=challenge)
        participant.is_winner = True

        site = Site.objects.get(is_default_site=True)
        user_badge = award_challenge_win(site, user, participant)

        self.assertIsNotNone(user_badge, "Badge was not awarded")

    def test_challenge_win_endpoint(self):
        user = create_test_regular_user('anon')
        Profile.objects.create(user=user)

        challenge = Challenge.objects.create(
            name='Challenge',
            activation_date=timezone.now() + timedelta(days=-7),
            deactivation_date=timezone.now() + timedelta(days=7)
        )
        challenge.publish()
        challenge.save()

        # Participate and complete
        challenge.participants \
            .create(user=user) \
            .entries.create()

        participant = Participant.objects.get(user=user, challenge=challenge)
        participant.is_winner = True
        participant.save()

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:challenges-winning'), format='json')

        self.assertTrue(response.data['available'], "Winner not available.")
        self.assertIsNotNone(response.data['badge'], "Badge was None.")
        self.assertIsNotNone(response.data['challenge'], "Challenge was None")

        self.assertEqual(response.data['badge']['name'], self.challenge_win.name, "Unexpected Badge returned.")
        self.assertEqual(response.data['challenge']['id'], challenge.id, "Unexpected Challenge returned.")


class TestNotification(APITestCase):

    def test_notification(self):
        """Test that the user can POST to /notification to mark their win as being 'read' """
        user = create_test_regular_user('anon_winner')
        profile = Profile.objects.create(user=user)

        challenge = Challenge.objects.create(
            name='Challenge',
            activation_date=timezone.now() + timedelta(days=-7),
            deactivation_date=timezone.now() + timedelta(days=7)
        )
        challenge.publish()
        challenge.save()

        # Participate and complete
        challenge.participants \
            .create(user=user) \
            .entries.create()

        participant = Participant.objects.get(user=user, challenge=challenge)
        participant.is_winner = True
        participant.save()

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:challenges-notification', kwargs={'pk': challenge.pk}), format='json')

        self.assertEquals(response.status_code, status.HTTP_204_NO_CONTENT,
                          "The POST request to mark winning as being read did not go through")

        # Fetch participant again after POST call updated has_read value
        participant = Participant.objects.get(user=user, challenge=challenge)

        self.assertEqual(participant.has_been_notified, True,
                         "Participant has not been marked as having read their winning badge")

    def test_winner_filter(self):
        """Test that when a winning participant notification has been confirmed, it will no longer be available."""
        user = create_test_regular_user('anon')
        Profile.objects.create(user=user)

        challenge = Challenge.objects.create(
            name='Challenge',
            activation_date=timezone.now() + timedelta(days=-7),
            deactivation_date=timezone.now() + timedelta(days=7)
        )
        challenge.publish()
        challenge.save()

        # Participate and complete
        challenge.participants \
            .create(user=user) \
            .entries.create()

        participant = Participant.objects.get(user=user, challenge=challenge)
        participant.is_winner = True
        participant.save()

        self.client.force_authenticate(user=user)
        self.client.post(reverse('api:challenges-notification', kwargs={'pk': challenge.pk}), {}, format='json')
        winning_response = self.client.get(reverse('api:challenges-winning'), format=json)

        self.assertFalse(winning_response.data['available'], "Winner still available")
        self.assertIsNone(winning_response.data['badge'], "Badge still available")
        self.assertIsNot(winning_response.data['challenge'], "Challenge still available")

    def test_goal_deadline_missed_notification_active(self):
        """Checks to see that a user gets a notification when they have missed challenge deadline"""
        user = create_test_regular_user('anon')

        goal = Goal.objects.create(name="goal 1",
                                   user=user,
                                   target=10000,
                                   weekly_target=100,
                                   start_date=timezone.now() - timedelta(days=30),
                                   end_date=timezone.now() - timedelta(days=25))

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:goals-deadline'), format='json')

        self.assertEqual(response.data['available'], True,
                         "Could not retrieve goal deadline missed notifications")

    def test_goal_deadline_missed_notification_inactive(self):
        """Checks to see that a user gets a doesn't get a notification when no deadline is missed"""
        user = create_test_regular_user('anon')

        goal = Goal.objects.create(name="goal 1",
                                   user=user,
                                   target=10000,
                                   weekly_target=100,
                                   start_date=timezone.now() - timedelta(days=30),
                                   end_date=timezone.now() + timedelta(days=30))

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:goals-deadline'), format='json')

        self.assertEqual(response.data['available'], False,
                         "Goal deadline notification was inadvertently sent")

    def test_challenge_completion_notification_quiz_active(self):
        """
        Creates a regular user
        Creates a quiz challenge
        Creates a quiz question
        Creates a quiz question option
        Creates a challenge participant
        Creates a quiz entry
        Creates a quiz question answer
        Checks to see if user should receive notification for not having completed challenge and it closes in two days
        """

        user = create_test_regular_user('anon')

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:challenges-challenge-incomplete'), format='json')

        self.assertFalse(response.data['available'],
                         "Challenge incomplete notification available when no challenge is available")

        challenge = Challenge.objects.create(name="challenge 1",
                                             type=Challenge.CTP_QUIZ,
                                             activation_date=timezone.now() - timedelta(days=30),
                                             deactivation_date=timezone.now() + timedelta(days=1),
                                             state=Challenge.CST_PUBLISHED)
        challenge.save()

        quiz_question = QuizQuestion.objects.create(challenge=challenge,
                                                    text="Quiz question text")

        question_option = QuestionOption.objects.create(question=quiz_question,
                                                        text="Quiz question option 1",
                                                        correct=True)

        response = self.client.get(reverse('api:challenges-challenge-incomplete'), format='json')

        self.assertFalse(response.data['available'],
                         "Quiz challenge incomplete notification available without having participated")

        participant = Participant.objects.create(user=user,
                                                 challenge=challenge)

        quiz_entry = Entry.objects.create(participant=participant,
                                          date_saved=timezone.now() - timedelta(days=20))

        quiz_answer = ParticipantAnswer.objects.create(entry=quiz_entry,
                                                       question=quiz_question,
                                                       selected_option=question_option,
                                                       date_answered=timezone.now() - timedelta(days=5))

        response = self.client.get(reverse('api:challenges-challenge-incomplete'), format='json')
        self.assertTrue(response.data['available'], "Quiz challenge completion notification not sent")

    def test_challenge_completion_notification_quiz_inactive(self):
        """
        Creates a regular user
        Creates a quiz challenge
        Creates a quiz question
        Creates a quiz question option
        Creates a challenge participant
        Creates a quiz entry
        Creates a quiz question answer
        Checks to see a user doesn't receive notification for not completing challenge not closing in two days
        """

        user = create_test_regular_user('anon')

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:challenges-challenge-incomplete'), format='json')

        self.assertFalse(response.data['available'],
                         "Challenge incomplete notification available when no challenge is available")

        challenge = Challenge.objects.create(name="challenge 1",
                                             type=Challenge.CTP_QUIZ,
                                             activation_date=timezone.now() - timedelta(days=30),
                                             deactivation_date=timezone.now() + timedelta(days=3),
                                             state=Challenge.CST_PUBLISHED)
        challenge.save()

        quiz_question = QuizQuestion.objects.create(challenge=challenge,
                                                    text="Quiz question text")

        question_option = QuestionOption.objects.create(question=quiz_question,
                                                        text="Quiz question option 1",
                                                        correct=True)

        response = self.client.get(reverse('api:challenges-challenge-incomplete'), format='json')

        self.assertFalse(response.data['available'],
                         "Quiz challenge incomplete notification available without having participated")

        participant = Participant.objects.create(user=user,
                                                 challenge=challenge)

        quiz_entry = Entry.objects.create(participant=participant,
                                          date_saved=timezone.now() - timedelta(days=20))

        quiz_answer = ParticipantAnswer.objects.create(entry=quiz_entry,
                                                       question=quiz_question,
                                                       selected_option=question_option,
                                                       date_answered=timezone.now() - timedelta(days=5))

        response = self.client.get(reverse('api:challenges-challenge-incomplete'), format='json')
        self.assertFalse(response.data['available'], "Quiz challenge completion notification incorrectly sent")

    def test_challenge_completion_notification_picture_active(self):
        """
        Creates a regular user
        Creates a picture challenge
        Creates a picture question
        Creates a challenge participant
        Creates a picture entry
        Checks to see if user should receive notification for not having completed challenge and it closes in two days
        """

        user = create_test_regular_user('anon')

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:challenges-challenge-incomplete'), format='json')

        self.assertFalse(response.data['available'],
                         "Challenge incomplete notification available when no challenge is available")

        challenge = Challenge.objects.create(name="challenge 1",
                                             type=Challenge.CTP_PICTURE,
                                             activation_date=timezone.now() - timedelta(days=30),
                                             deactivation_date=timezone.now() + timedelta(days=1),
                                             state=Challenge.CST_PUBLISHED)
        challenge.save()

        picture_question = PictureQuestion.objects.create(challenge=challenge,
                                                          text="Picture question text")

        response = self.client.get(reverse('api:challenges-challenge-incomplete'), format='json')

        self.assertFalse(response.data['available'],
                         "Picture challenge incomplete notification available without having participated")

        participant = Participant.objects.create(user=user,
                                                 challenge=challenge)

        picture_entry = ParticipantPicture.objects.create(participant=participant,
                                                          question=picture_question,
                                                          date_answered=timezone.now() - timedelta(days=20))

        response = self.client.get(reverse('api:challenges-challenge-incomplete'), format='json')
        self.assertTrue(response.data['available'], "Picture challenge completion notification not sent")

    def test_challenge_completion_notification_picture_inactive(self):
        """
        Creates a regular user
        Creates a picture challenge
        Creates a picture question
        Creates a challenge participant
        Creates a picture entry
        Checks to see if user should receive notification for not having completed challenge and it closes in two days
        """

        user = create_test_regular_user('anon')

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:challenges-challenge-incomplete'), format='json')

        self.assertFalse(response.data['available'],
                         "Challenge incomplete notification available when no challenge is available")

        challenge = Challenge.objects.create(name="challenge 1",
                                             type=Challenge.CTP_PICTURE,
                                             activation_date=timezone.now() - timedelta(days=30),
                                             deactivation_date=timezone.now() + timedelta(days=3),
                                             state=Challenge.CST_PUBLISHED)
        challenge.save()

        picture_question = PictureQuestion.objects.create(challenge=challenge,
                                                          text="Picture question text")

        response = self.client.get(reverse('api:challenges-challenge-incomplete'), format='json')

        self.assertFalse(response.data['available'],
                         "Picture challenge incomplete notification available without having participated")

        participant = Participant.objects.create(user=user,
                                                 challenge=challenge)

        picture_entry = ParticipantPicture.objects.create(participant=participant,
                                                          question=picture_question,
                                                          date_answered=timezone.now() - timedelta(days=20))

        response = self.client.get(reverse('api:challenges-challenge-incomplete'), format='json')
        self.assertFalse(response.data['available'], "Picture challenge completion notification incorrectly sent")

    def test_challenge_completion_notification_freeform_active(self):
        """
        Creates a regular user
        Creates a freeform challenge
        Creates a freeform question
        Creates a challenge participant
        Creates a freeform entry
        Checks to see if user should receive notification for not having completed challenge and it closes in two days
        """

        user = create_test_regular_user('anon')

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:challenges-challenge-incomplete'), format='json')

        self.assertFalse(response.data['available'],
                         "Challenge incomplete notification available when no challenge is available")

        challenge = Challenge.objects.create(name="challenge 1",
                                             type=Challenge.CTP_FREEFORM,
                                             activation_date=timezone.now() - timedelta(days=30),
                                             deactivation_date=timezone.now() + timedelta(days=1),
                                             state=Challenge.CST_PUBLISHED)
        challenge.save()

        free_text_question = FreeTextQuestion.objects.create(challenge=challenge,
                                                             text="Free Text question")

        response = self.client.get(reverse('api:challenges-challenge-incomplete'), format='json')

        self.assertFalse(response.data['available'],
                         "Free text challenge incomplete notification available without having participated")

        participant = Participant.objects.create(user=user,
                                                 challenge=challenge)

        free_text_entry = ParticipantFreeText.objects.create(participant=participant,
                                                             question=free_text_question,
                                                             text="Free Text Answer 1",
                                                             date_answered=timezone.now() - timedelta(days=20))

        response = self.client.get(reverse('api:challenges-challenge-incomplete'), format='json')
        self.assertTrue(response.data['available'], "Challenge completion notification not available")

    def test_challenge_completion_notification_freeform_inactive(self):
        """
        Creates a regular user
        Creates a freeform challenge
        Creates a freeform question
        Creates a challenge participant
        Creates a freeform entry
        Checks to see if user should receive notification for not having completed challenge and it closes in two days
        """

        user = create_test_regular_user('anon')

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:challenges-challenge-incomplete'), format='json')

        self.assertFalse(response.data['available'],
                         "Challenge incomplete notification available when no challenge is available")

        challenge = Challenge.objects.create(name="challenge 1",
                                             type=Challenge.CTP_FREEFORM,
                                             activation_date=timezone.now() - timedelta(days=30),
                                             deactivation_date=timezone.now() + timedelta(days=3),
                                             state=Challenge.CST_PUBLISHED)
        challenge.save()

        free_text_question = FreeTextQuestion.objects.create(challenge=challenge,
                                                             text="Free Text question")

        response = self.client.get(reverse('api:challenges-challenge-incomplete'), format='json')

        self.assertFalse(response.data['available'],
                         "Free text challenge incomplete notification available without having participated")

        participant = Participant.objects.create(user=user,
                                                 challenge=challenge)

        free_text_entry = ParticipantFreeText.objects.create(participant=participant,
                                                             question=free_text_question,
                                                             text="Free Text Answer 1",
                                                             date_answered=timezone.now() - timedelta(days=20))

        response = self.client.get(reverse('api:challenges-challenge-incomplete'), format='json')
        self.assertFalse(response.data['available'], "Challenge completion notification incorrectly available")

    def test_custom_notifications_active(self):
        """Checks to see a custom notification can be retrieved"""
        user = create_test_regular_user('anon')
        notification = CustomNotification.objects.create(message="Test notification 1",
                                                         publish_date=timezone.now(),
                                                         expiration_date=timezone.now() + timedelta(days=30))
        notification.save()

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:notifications-current'))

        self.assertEqual(response.status_code, status.HTTP_200_OK, "Error when retrieving custom notifications")

        self.assertTrue(response.data['available'], "Custom notification not available")
        self.assertIsNotNone(response.data['notifications'], "Empty notification response")

    def test_custom_notifications_inactive(self):
        """Checks to see a custom notification can't be read once it's expired"""
        user = create_test_regular_user('anon')
        notification = CustomNotification.objects.create(message="Test notification 1",
                                                         publish_date=timezone.now() - timedelta(days=30),
                                                         expiration_date=timezone.now() - timedelta(days=5))
        notification.save()

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:notifications-current'))

        self.assertEqual(response.status_code, status.HTTP_200_OK, "Error when retrieving custom notifications")

        self.assertFalse(response.data['available'], "Custom notification available after expiration")
        self.assertEqual(len(response.data['notifications']), 0, "Custom notification has unexpected content")

    def test_multiple_custom_notifications_active(self):
        """Checks to multiple notifications can be returned"""
        user = create_test_regular_user('anon')
        notification = CustomNotification.objects.create(message="Test notification 1",
                                                         publish_date=timezone.now() - timedelta(days=30),
                                                         expiration_date=timezone.now() + timedelta(days=30))
        notification.save()

        notification = CustomNotification.objects.create(message="Test notification 2",
                                                         publish_date=timezone.now() - timedelta(days=20),
                                                         expiration_date=timezone.now() + timedelta(days=40))
        notification.save()

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:notifications-current'))

        self.assertEqual(response.status_code, status.HTTP_200_OK, "Error when retrieving custom notifications")

        self.assertTrue(response.data['available'], "Multiple custom notifications not available")
        self.assertEquals(len(response.data), 2, "Incorrect number of notifications returned")


class TestBadgeUrls(APITestCase):
    def test_urls_returned(self):
        with mock.patch('content.models.Badge.image', new_callable=PropertyMock) as mock_image:

            file1 = PropertyMock(url="url1")
            mock_image.return_value = PropertyMock(file=file1)

            badge = Badge.objects.create(
                name="Badge 1",
                slug="badgie 1",
                intro="into 1",
            )
            response = self.client.get(reverse('api:badge-urls', kwargs={}), format='json')
            self.assertEquals(response.data['urls'].__len__(), 1, "One url should have been returned")
            self.assertEquals(response.data['urls'][0], 'http://testserver/api/badge-urls/url1', "Incorrect url name")

    def test_no_urls_returned(self):
            response = self.client.get(reverse('api:badge-urls', kwargs={}), format='json')
            self.assertEquals(response.data['urls'].__len__(), 0, "No urls should have been returned")

    def test_when_badge_image_is_none(self):
            badge = Badge.objects.create(
                name="Badge 1",
                slug="badgie 1",
                intro="into 1",
            )
            response = self.client.get(reverse('api:badge-urls', kwargs={}), format='json')
            self.assertEquals(response.data['urls'].__len__(), 0, "No urls should have been returned")


class TestFeedback(APITestCase):
    def test_create_feedback(self):
        user = create_test_regular_user()
        feedback = Feedback.objects.create(
            text='How does this work?',
            type=Feedback.FT_ASK,
            user=user
        )
        self.assertIsNotNone(feedback.date_created)

    def test_create_feedback_anon(self):
        feedback = Feedback.objects.create(
            text='How does this work?',
            type=Feedback.FT_ASK
        )
        self.assertIsNotNone(feedback.date_created)

    def test_serialize_feedback(self):
        user = create_test_regular_user()
        data = {
            'text': 'How does this work?',
            'type': 'ask',
            'user': user.id
        }

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:feedback-list'), data, format='json')

        self.assertEquals(response.data['text'], data['text'])

    def test_serialize_feedback_anon(self):
        user = create_test_regular_user()
        data = {
            'text': 'How does this work?',
            'type': 'ask',
        }

        response = self.client.post(reverse('api:feedback-list'), data, format='json')
        print(response.data)

        self.assertEquals(response.data['text'], data['text'])

    def test_serialize_feedback_wrong_user(self):
        user1 = create_test_regular_user('anon1')
        user2 = create_test_regular_user('anon2')
        data = {
            'text': 'How does this work?',
            'type': 'ask',
            'user': user1.id
        }

        self.client.force_authenticate(user=user2)
        response = self.client.post(reverse('api:feedback-list'), data, format='json')

        self.assertEquals(response.data['text'], data['text'])
