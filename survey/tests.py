
import json

from django.shortcuts import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from wagtail.wagtailcore.models import Page

from users.models import RegUser, Profile
from .models import CoachSurvey, CoachFormField, CoachSurveySubmission

RADIO_FIELD = 'radio'


def create_survey(title='Test Survey', intro='Take this challenge', outro='Thanks for taking the challenge',
                  deliver_after=1):
    parent_page = Page.get_root_nodes()[0]
    survey = CoachSurvey(
        title=title,
        intro=intro,
        outro=outro,
        deliver_after=deliver_after
    )
    parent_page.add_child(instance=survey)
    survey.unpublish()
    return survey


def publish(survey, user):
    survey.save_revision(
        user=user,
        submitted_for_moderation=False
    ).publish()


def create_user(username='Anon'):
    user = RegUser.objects.create(
        username=username,
        email='a@b.c'
    )
    Profile.objects.create(
        mobile='1234567890',
        user=user
    )
    return user


class CoachSurveyAPITest(APITestCase):

    def test_basic_submit(self):
        user = create_user()
        survey = create_survey()
        survey.form_fields.create(
            key='field-1',
            label='First Form Field',
            field_type=RADIO_FIELD,
            choices='1,2,3,4,5',
        )
        publish(survey, user)

        submission = {
            'field-1': '3'
        }

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:surveys-submission', kwargs={'pk': survey.pk}), submission, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, "Survey submission request failed.")

        data = json.loads(CoachSurveySubmission.objects.get(user=user, page=survey).form_data)
        self.assertEqual(data.get('field-1'), '3', "Field not found in submission data")
