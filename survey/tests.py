
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


# ================ #
# Helper functions #
# ================ #


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
            choices='1,2,3,4,5'
        )
        publish(survey, user)

        submission = {
            'field-1': '3'
        }

        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('api:surveys-submission', kwargs={'pk': survey.pk}), submission,
                                    format='json')

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
            'bot-conversation': 'SURVEY_EATOOL'
        })
        response = self.client.get(u'%s?%s' % (reverse('api:surveys-list'), params.urlencode()))

        self.assertEqual(len(response.data), 1, "Unexpected number of surveys returned.")
        self.assertEqual(response.data[0]['id'], eatool_survey.id, "Unexpected Survey returned.")

    def test_unavailable_after_submit(self):
        """Test that a survey is unavailable after a submission is successfully created.
        """
        now = timezone.now()

        user = create_user()
        user.date_joined = now - timedelta(days=4)
        user.save()
        survey = create_survey(deliver_after=3)  # Survey is available today
        survey.form_fields.create(
            key='field-1',
            label='First Form Field',
            field_type=SINGLE_LINE,
            required=False
        )
        publish(survey, create_user('Staff'))

        submission = {
            'field-1': 'one'
        }

        self.client.force_authenticate(user=user)
        self.client.post(reverse('api:surveys-submission', kwargs={'pk': survey.pk}),
                         submission, format='json')

        response = self.client.get(reverse('api:surveys-current'), format='json')

        self.assertFalse(response.data['available'], "Survey still avaialble after submission.")
        self.assertEqual(response.data['inactivity_age'], 0,
                         "Inactivity age was returned when survey was not available.")
        self.assertIsNone(response.data['survey'], "Survey object was returned.")

    def test_next_available(self):
        """If there are multiple surveys set up, and the user submits to the first, then the second must be available.
        """
        now = timezone.now()

        user = create_user()
        user.date_joined = now - timedelta(days=8)  # Both surveys will be available
        user.save()

        survey1 = create_survey('Baseline', deliver_after=3, bot_conversation=CoachSurvey.BASELINE)
        survey1.form_fields.create(
            key='field-1',
            label='First Form Field',
            field_type=SINGLE_LINE,
            required=False
        )
        publish(survey1, create_user('Staff1'))

        survey2 = create_survey('EA Tool', deliver_after=7, bot_conversation=CoachSurvey.EATOOL)
        survey2.form_fields.create(
            key='field-1',
            label='First Form Field',
            field_type=SINGLE_LINE,
            required=False
        )
        publish(survey2, create_user('Staff2'))

        # User submits to first survey
        self.client.force_authenticate(user=user)
        self.client.post(reverse('api:surveys-submission', kwargs={'pk': survey1.pk}), data={
            'field-1': 'one'
        }, format='json')

        # Second survey must now be available
        response = self.client.get(reverse('api:surveys-current'), format='json')

        self.assertTrue(response.data['available'], "Survey is not available.")
        self.assertIsNotNone(response.data['survey'], "Survey is not in response.")
        self.assertEqual(response.data['survey']['id'], survey2.id, "Unexpected survey identity.")
        self.assertEqual(response.data['survey']['bot_conversation'], 'SURVEY_EATOOL',
                         "Unexpected Bot conversation type.")


class SurveyNotificationAgeAPI(APITestCase):
    """
    Tests to ensure that the days of inactivity is measured correctly. They are used by the frontend to determine
    what notification to show the user.
    """

    def test_notification_inactivity_days(self):
        """If the user has not completed the survey in 3 days, the first reminder will be triggered on the frontend."""
        now = timezone.now()

        user = create_user()
        user.date_joined = now - timedelta(days=7)
        user.save()

        survey = create_survey(deliver_after=3)
        publish(survey, create_user('Staff'))

        self.client.force_authenticate(user=user)
        response = self.client.get(reverse('api:surveys-current'), format='json')

        # Age is counted since the survey is available to the user. The user has been registered for 7 days, the survey
        # was available after 3, so the age must be 4.
        self.assertEqual(response.data['inactivity_age'], 4,
                         "Unexpected survey age. Will affect notification thresholds on frontend.")


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
        response = self.client.patch(reverse('api:surveys-draft', kwargs={'pk': survey.pk}), {
            'first': '1',
            'second': '2'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, "Draft submit request failed")

        updated_draft = CoachSurveySubmissionDraft.objects.get(user=user, survey=survey)
        submission_data = json.loads(updated_draft.submission_data)
        self.assertEqual(submission_data.get('first', None), '1', "First submission field was not set")
        self.assertEqual(submission_data.get('second', None), '2', "Second submission field was not set")
        self.assertFalse(updated_draft.complete, "Draft was set to completed.")
        self.assertIsNone(updated_draft.submission, "Draft has submission assigned.")

    def test_draft_partial_submit(self):
        """Test that a draft can be partially submitted."""
        user = create_user()
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
        publish(survey, create_user('Staff'))

        self.client.force_authenticate(user=user)
        self.client.patch(reverse('api:surveys-draft', kwargs={'pk': survey.pk}), {
            'second': '2'
        }, format='json')

        updated_draft = CoachSurveySubmissionDraft.objects.get(user=user, survey=survey)
        data = json.loads(updated_draft.submission_data if updated_draft.has_submission else {})

        self.assertEqual(data.get('second', None), '2', "Second field was not set")

    def test_ensure_draft_on_submit(self):
        """
        Test that a draft is created when a survey is submitted, if one hasn't been created. This is to simplify
        reporting later, so data can exported using the drafts, and not inferred from existing submissions and missing
        drafts.
        """
        user = create_user()
        survey = create_survey()
        survey.form_fields.create(
            key='first',
            label='First',
            field_type=SINGLE_LINE
        )
        publish(survey, create_user('Staff'))

        self.client.force_authenticate(user=user)
        self.client.post(reverse('api:surveys-submission', kwargs={'pk': survey.pk}), {
            CoachSurvey.CONSENT_KEY: CoachSurvey.ANSWER_YES,
            'first': '1'
        }, format='json')

        self.assertTrue(CoachSurveySubmissionDraft.objects.filter(user=user, survey=survey).exists(),
                        "Draft was not created.")

        submission = CoachSurveySubmission.objects.get(user=user, page=survey)
        draft = CoachSurveySubmissionDraft.objects.get(user=user, survey=survey, complete=True)
        self.assertEqual(draft.submission, submission, "Submission was not assigned to draft.")

    def test_consent_set(self):
        """Test that submitting a draft answer containing the appropriate consent answer will store the draft correctly.
        """
        user = create_user()
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
        publish(survey, create_user('Staff'))

        self.client.force_authenticate(user=user)
        self.client.patch(reverse('api:surveys-draft', kwargs={'pk': survey.pk}), {
            CoachSurvey.CONSENT_KEY: CoachSurvey.ANSWER_YES,
            'first': '1',
            'second': '2'
        }, format='json')

        updated_draft = CoachSurveySubmissionDraft.objects.get(user=user, survey=survey)
        data = json.loads(updated_draft.submission_data) if updated_draft.has_submission else {}

        self.assertTrue(updated_draft.consent, "Consent was not stored")
        self.assertIsNone(data.get(CoachSurvey.CONSENT_KEY, None), "Consent was stored in submission data")

    def test_consent_not_unset(self):
        """Test that doing a partial update without a consent value does not set an existing True consent value to
        False.
        """
        user = create_user()
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
        publish(survey, create_user('Staff'))

        self.client.force_authenticate(user=user)

        # User provides consent and first answer
        self.client.patch(reverse('api:surveys-draft', kwargs={'pk': survey.pk}), {
            CoachSurvey.CONSENT_KEY: CoachSurvey.ANSWER_YES,
            'first': '1'
        }, format='json')

        # User provides second answer
        self.client.patch(reverse('api:surveys-draft', kwargs={'pk': survey.pk}), {
            'second': '2'
        }, format='json')

        updated_draft = CoachSurveySubmissionDraft.objects.get(user=user, survey=survey)

        self.assertTrue(updated_draft.consent, "Consent was set to False on second draft update")

    def test_consent_partial(self):
        """Test that a draft can be submitted with only consent."""
        user = create_user()
        survey = create_survey()
        survey.form_fields.create(
            key='first',
            label='First',
            field_type=SINGLE_LINE
        )
        publish(survey, create_user('Staff'))

        self.client.force_authenticate(user=user)
        self.client.patch(reverse('api:surveys-draft', kwargs={'pk': survey.pk}), {
            CoachSurvey.CONSENT_KEY: CoachSurvey.ANSWER_YES
        }, format='json')

        updated_draft = CoachSurveySubmissionDraft.objects.get(user=user, survey=survey)
        data = json.loads(updated_draft.submission_data) if updated_draft.has_submission else {}

        self.assertTrue(updated_draft.consent, "Consent was not set.")
        self.assertEqual(data, {}, "Draft submission unexpectedly contains data.")


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
            self.client.put(reverse('api:surveys-draft', kwargs={'pk': surveys[0].pk}), {}, format='json')

        survey_aggregates()
        self.skipTest('TODO')


class SurveyDataPreservationTests(APITestCase):
    """Tests to check whether submission exports store historical data.
    """

    def test_user_deletion(self):
        """Test whether deleting a user will preserve the data as it was at time of submission."""
        user = RegUser.objects.create(
            username='anon',
            first_name='Anonymous',
            last_name='Rex',
            email='a@b.c'
        )
        Profile.objects.create(
            user=user,
            age=30,
            gender=Profile.GENDER_MALE,
            mobile='12345667890'
        )
        survey = create_survey()
        survey.form_fields.create(
            key='first',
            label='First',
            field_type=SINGLE_LINE
        )
        publish(survey, create_user('Staff'))

        self.client.force_authenticate(user=user)
        self.client.post(reverse('api:surveys-submission', kwargs={'pk': survey.pk}), {
            CoachSurvey.CONSENT_KEY: CoachSurvey.ANSWER_YES,
            'first': '1'
        }, format='json')

        # Copy user info for testing
        user_id = user.id
        user_name = user.get_full_name()
        user_username = user.username
        user_mobile = user.profile.mobile
        user_gender = user.profile.get_gender_display()
        user_age = str(user.profile.age)
        user_email = user.email

        user.delete()

        submission = CoachSurveySubmission.objects.filter(survey=survey).first()
        self.assertIsNotNone(submission, "Submission was deleted along with user")

        data = submission.get_data()
        self.assertEqual(data['user_id'], user_id)
        self.assertEqual(data['name'], user_name)
        self.assertEqual(data['username'], user_username)
        self.assertEqual(data['mobile'], user_mobile)
        self.assertEqual(data['gender'], user_gender)
        self.assertEqual(data['age'], user_age)
        self.assertEqual(data['email'], user_email)


class TestEndlineSurvey(APITestCase):

    pass
