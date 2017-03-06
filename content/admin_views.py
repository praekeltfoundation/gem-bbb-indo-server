from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import permission_required
from django.http.response import JsonResponse, HttpResponse

from .reports import GoalReport, UserReport, SavingsReport, SummaryDataPerChallenge, \
    SummaryDataPerQuiz, ChallengeExportPicture, ChallengeExportQuiz, ChallengeExportFreetext

from .models import Challenge, Participant


def participant_list_view(request):
    context = {
        'participants': Participant.objects.all()
    }

    return render(request, 'content/admin/participant/list.html', context)


@permission_required('participant.can_change')
@ensure_csrf_cookie
def participant_mark_read(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)
    participant.is_read = not participant.is_read
    participant.save()
    return JsonResponse({})


@permission_required('participant.can_change')
@ensure_csrf_cookie
def participant_mark_shortlisted(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)
    participant.is_shortlisted = not participant.is_shortlisted
    participant.save()
    return JsonResponse({})


@permission_required('participant.can_change')
@ensure_csrf_cookie
def participant_mark_winner(request, participant_pk):
    participant = get_object_or_404(Participant, pk=participant_pk)
    participant.is_winner = not participant.is_winner
    participant.save()
    return JsonResponse({})


#############
# Reporting #
#############


# Challenge reports
def report_challenge_exports(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment;filename=export.csv'

    if request.method == 'POST':
        if request.POST.get('action') == 'EXPORT-CHALLENGE-SUMMARY':
            if request.POST['date_from'] is '' or request.POST['date_to'] is '':
                date_from = date_to = None
            else:
                date_from = request.POST['date_from']
                date_to = request.POST['date_to']
            SummaryDataPerChallenge.export_csv(response, date_from=date_from, date_to=date_to)
            return response
        elif request.POST.get('action') == 'EXPORT-CHALLENGE-QUIZ-SUMMARY':
            SummaryDataPerQuiz.export_csv(response)
            return response
        elif request.POST.get('action') == 'EXPORT-CHALLENGE-PICTURE':
            challenge_name = request.POST['picture-challenge-name']
            ChallengeExportPicture.export_csv(response, challenge_name=challenge_name)
            return response
        elif request.POST.get('action') == 'EXPORT-CHALLENGE-QUIZ':
            challenge_name = request.POST['quiz-challenge-name']
            ChallengeExportQuiz.export_csv(response, challenge_name=challenge_name)
            return response
        elif request.POST.get('action') == 'EXPORT-CHALLENGE-FREETEXT':
            challenge_name = request.POST['freetext-challenge-name']
            ChallengeExportFreetext.export_csv(response, challenge_name=challenge_name)
            return response
    elif request.method == 'GET':
        context = {
            'quiz_challenges': list(Challenge.objects.filter(type=Challenge.CTP_QUIZ)),
            'picture_challenges': list(Challenge.objects.filter(type=Challenge.CTP_PICTURE)),
            'freetext_challenges': list(Challenge.objects.filter(type=Challenge.CTP_FREEFORM))
        }

        return render(request, 'admin/reports/challenges.html', context=context)


# Goal reports
def report_goal_exports(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment;filename=export.csv'

    if request.POST.get('action') == 'EXPORT-ALL':
        # TODO: Write all csv files, zip and send
        return render(request, 'admin/reports/goals.html')
    elif request.POST.get('action') == 'EXPORT-GOAL':
        GoalReport.export_csv(response)
        return response
    elif request.POST.get('action') == 'EXPORT-USER':
        UserReport.export_csv(response)
        return response
    elif request.POST.get('action') == 'EXPORT-SAVINGS':
        SavingsReport.export_csv(response)
        return response

    return render(request, 'admin/reports/goals.html')
