
from django.db.models import Count

from .models import CoachSurvey, CoachSurveySubmission, CoachSurveySubmissionDraft


def survey_aggregates():
    """
    Required fields:
        - Name of survey
        - Date published
        - Total users completed
        - Total users who started but did not complete the survey
        - Total users who choose not to consent
        - Total user who did not respond
    """
    CoachSurveySubmissionDraft.objects.all()

    pass
