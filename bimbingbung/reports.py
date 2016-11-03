from content.models import Challenge, Participant, ParticipantAnswer, QuestionOption, QuizQuestion
from django.db.models import Avg, Count
import csv


def get_challenge_data(challenges):
    challenge_data = []
    for c in challenges:
        data = {
            'name': c.name,
            'publish_date': c.date_activated,
            'unpublish_date': c.date_activated,
            'users_completed': ParticipantAnswer.objects.filter(challenge_id=c.id, participant__completed=True).count(),
        }
        challenge_data.append(data)
    return challenge_data


def get_quiz_data(challenge):
    question_data = []
    for q in challenge.questions:
        data = {
            'question': q.text,
            'total': ParticipantAnswer.objects.filter(question_id=q.id).count(),
            'correct': ParticipantAnswer.objects.filter(question_id=q.id, selected_option__correct=True).count(),
        }
        question_data.append(data)
    return question_data
