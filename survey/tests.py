
from datetime import timedelta
import json

from django.http.request import QueryDict
from django.shortcuts import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from wagtail.wagtailcore.models import Page

from users.models import RegUser, Profile
from .models import CoachSurvey, CoachFormField, CoachSurveySubmission, CoachSurveySubmissionDraft
from .reports import survey_aggregates

SINGLE_LINE = 'singleline'
RADIO_FIELD = 'radio'


def create_survey(title='Test Survey', intro='Take this challenge', outro='Thanks for taking the challenge',
                  deliver_after=1, **kwargs):
    parent_page = Page.get_root_nodes()[0]
    survey = CoachSurvey(
        title=title,
        intro=intro,
        outro=outro,
        deliver_after=deliver_after,
        **kwargs
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
        """Test that a submission can be received"""
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

    def test_current_after_registration_days_none_available(self):
        """Test that a survey is kept from the user before the specified number of days after registration has passed.
        """
        now = timezone.now()

        user = create_user()
        user.date_joined = now - timedelta(days=2)
        user.save()
        survey = create_survey(deliver_after=3)  # Survey will only be available the next day
        publish(survey, user)

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:surveys-current'))

        self.assertEqual(response.status_code, status.HTTP_200_OK, "Retrieve current survey failed.")
        self.assertFalse(response.data['available'], "Available flag expected to be False.")
        self.assertIsNone(response.data['survey'], "Survey field was unexpectedly populated.")

    def test_current_after_registration_days_available(self):
        """Test that a survey is made available to the user after the specified number of days after registration has
        passed."""
        now = timezone.now()

        user = create_user()
        user.date_joined = now - timedelta(days=3)
        user.save()
        survey = create_survey(deliver_after=3)  # Survey is available today
        publish(survey, user)

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:surveys-current'))

        self.assertEqual(response.status_code, status.HTTP_200_OK, "Retrieve current survey failed.")
        self.assertTrue(response.data['available'], "Available flag expected to be True.")
        self.assertIsNotNone(response.data['survey'], "Survey field was not populated.")

    def test_filter_by_bot_conversation(self):
        """Test that surveys can be filtered by the requested Bot conversation type.
        """
        user = create_user('Anon')
        baseline_survey = create_survey(title='Baseline survey', bot_conversation=CoachSurvey.BASELINE)
        eatool_survey = create_survey(title='EA Tool', bot_conversation=CoachSurvey.EATOOL)

        publish(baseline_survey, user)
        publish(eatool_survey, user)

        self.client.force_authenticate(user=user)

        params = QueryDict(mutable=True)
        params.update({
            'bot-conversation': 'EATOOL'
        })
        response = self.client.get(u'%s?%s' % (reverse('api:surveys-list'), params.urlencode()))

        self.assertEqual(len(response.data), 1, "Unexpected number of surveys returned.")
        self.assertEqual(response.data[0]['id'], eatool_survey.id, "Unexpected Survey returned.")


class DraftAPITest(APITestCase):

    def test_basic_draft_submit(self):
        """Test that a draft can be submitted."""
        user = create_user('anon')
        survey = create_survey()
        survey.form_fields.create(
            key='first',
            label='First',
            field_type=SINGLE_LINE
        )
        survey.form_fields.create(
            key='second',
            label='Second',
            field_type=SINGLE_LINE
        )
        publish(survey, user)

        self.client.force_authenticate(user=user)
        response = self.client.put(reverse('api:surveys-draft', kwargs={'pk': survey.pk}), {
            'first': '1',
            'second': '2'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, "Draft submit request failed")

        updated_draft = CoachSurveySubmissionDraft.objects.get(user=user, survey=survey)
        submission = json.loads(updated_draft.submission)
        self.assertEqual(submission.get('first', None), '1', "First submission field was not set")
        self.assertEqual(submission.get('second', None), '2', "Second submission field was not set")

    def test_ensure_draft_on_submit(self):
        """
        Test that a draft is created when a survey is submitted, if one hasn't been created. This is to simplify
        reporting later, so data can exported using the drafts, and not inferred from existing submissions and missing
        drafts.
        """
        self.skipTest('TODO: Submission view needs to ensure draft is created.')


class SurveyReportingRequirements(APITestCase):

    def test_survey_report_aggregation(self):
        """Test that total data by survey aggregates correctly."""
        staff = create_user('Staff')
        users = [create_user('anon' + str(i)) for i in range(10)]
        surveys = []
        for i in range(3):
            survey = create_survey('Survey ' + str(i))
            publish(survey, staff)
            surveys.append(survey)

        # Users who submitted drafts
        for user in users[0:7]:
            self.client.force_authenticate(user=user)

            # Survey 1
            # self.client.put(reverse('api:surveys-draft', kwargs={'pk': surveys[0].pk}))

        survey_aggregates()
        self.skipTest('TODO')


