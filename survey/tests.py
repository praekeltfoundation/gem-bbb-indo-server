
from django.test import TestCase
from rest_framework.test import APITestCase

from .models import CoachSurvey, CoachFormField


def create_survey(title='Test Survey', intro='Take this challenge', outro='Thanks for taking the challenge',
                  deliver_after=1):
    return CoachSurvey.objects.create(
        title=title,
        intro=intro,
        outro=outro,
        deliver_after=deliver_after
    )


def publish(survey):
    survey.save_revision(
        user=creator,
        submitted_for_moderation=False
    ).publish()


class CoachSurveyAPITest(APITestCase):

    pass
