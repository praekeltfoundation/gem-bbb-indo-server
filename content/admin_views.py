from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth.decorators import permission_required
from django.http.response import JsonResponse, HttpResponse, StreamingHttpResponse

from wagtail.wagtailadmin import messages

from .reports import GoalReport, UserReport, SavingsReport, SummaryDataPerChallenge, \
    SummaryDataPerQuiz, ChallengeExportPicture, ChallengeExportQuiz, ChallengeExportFreetext, SummaryGoalData, \
    GoalDataPerCategory, RewardsData, RewardsDataPerBadge, RewardsDataPerStreak, UserTypeData, SummarySurveyData, \
    EaTool1SurveyData, BaselineSurveyData, EaTool2SurveyData, EndlineSurveyData

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


def report_index_page(request):
    return render(request, 'admin/reports/index.html')


# Challenge reports
def report_challenge_exports(request):

    if request.method == 'POST':
        response = HttpResponse(content_type='application/zip; charset=utf-8')
        response['Content-Disposition'] = 'attachment;filename=export-' + str(timezone.now().date()) + '.zip'

        if request.POST.get('action') == 'EXPORT-CHALLENGE-SUMMARY':
            if request.POST['date_from'] is '' or request.POST['date_to'] is '':
                date_from = date_to = None
            else:
                date_from = request.POST['date_from']
                date_to = request.POST['date_to']

            success, err = SummaryDataPerChallenge.export_csv(request, response, date_from=date_from, date_to=date_to)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-challenges'))
            return response
        elif request.POST.get('action') == 'EXPORT-CHALLENGE-QUIZ-SUMMARY':
            success, err = SummaryDataPerQuiz.export_csv(request, response)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-challenges'))
            return response
        elif request.POST.get('action') == 'EXPORT-CHALLENGE-PICTURE':
            challenge_name = request.POST['picture-challenge-name']
            success, err = ChallengeExportPicture.export_csv(request, response, challenge_name=challenge_name)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-challenges'))
            return response
        elif request.POST.get('action') == 'EXPORT-CHALLENGE-QUIZ':
            challenge_name = request.POST['quiz-challenge-name']
            success, err = ChallengeExportQuiz.export_csv(request, response, challenge_name=challenge_name)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-challenges'))
            return response
        elif request.POST.get('action') == 'EXPORT-CHALLENGE-FREETEXT':
            challenge_name = request.POST['freetext-challenge-name']
            success, err = ChallengeExportFreetext.export_csv(request, response, challenge_name=challenge_name)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-challenges'))
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

    if request.method == 'POST':
        response = StreamingHttpResponse(content_type='application/zip; charset=utf-8')
        response['Content-Disposition'] = 'attachment;filename=export-' + str(timezone.now().date()) + '.zip'

        if request.POST.get('action') == 'EXPORT-GOAL':
            success, err = GoalReport.export_csv(request, response)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-goals'))
            return response
        elif request.POST.get('action') == 'EXPORT-USER':
            success, err = UserReport.export_csv(request, response)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-goals'))
            return response
        elif request.POST.get('action') == 'EXPORT-SAVINGS':
            success, err = SavingsReport.export_csv(request, response)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-goals'))
            return response
    elif request.method == 'GET':
        return render(request, 'admin/reports/goals.html')


# Aggregate reports
def report_aggregate_exports(request):

    if request.method == 'POST':
        response = StreamingHttpResponse(content_type='application/zip; charset=utf-8')
        response['Content-Disposition'] = 'attachment;filename=export-' + str(timezone.now().date) + '.zip'

        if request.POST.get('action') == 'EXPORT-AGGREGATE-SUMMARY':
            success, err = SummaryGoalData.export_csv(request, response)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-aggregates'))
            return response
        elif request.POST.get('action') == 'EXPORT-AGGREGATE-GOAL-PER-CATEGORY':
            success, err = GoalDataPerCategory.export_csv(request, response)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-aggregates'))
            return response
        elif request.POST.get('action') == 'EXPORT-AGGREGATE-REWARDS-DATA':
            success, err = RewardsData.export_csv(request, response)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-aggregates'))
            return response
        elif request.POST.get('action') == 'EXPORT-AGGREGATE-DATA-PER-BADGE':
            success, err = RewardsDataPerBadge.export_csv(request, response)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-aggregates'))
            return response
        elif request.POST.get('action') == 'EXPORT-AGGREGATE-DATA-PER-STREAK':
            success, err = RewardsDataPerStreak.export_csv(request, response)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-aggregates'))
            return response
        elif request.POST.get('action') == 'EXPORT-AGGREGATE-USER-TYPE':
            success, err = UserTypeData.export_csv(request, response)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-aggregates'))
            return response
    elif request.method == 'GET':
        return render(request, 'admin/reports/aggregates.html')


# Survey exports
def report_survey_exports(request):

    if request.method == 'POST':
        response = HttpResponse(content_type='application/zip; charset=utf-8')
        response['Content-Disposition'] = 'attachment;filename=export-' + str(timezone.now().date) + '.zip'

        if request.POST.get('action') == 'EXPORT-SURVEY-SUMMARY':
            success, err = SummarySurveyData.export_csv(request, response)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-surveys'))
            return response
        elif request.POST.get('action') == 'EXPORT-BASELINE-SURVEY':
            success, err = BaselineSurveyData.export_csv(request, response)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-surveys'))
            return response
        elif request.POST.get('action') == 'EXPORT-EATOOL1-SURVEY':
            success, err = EaTool1SurveyData.export_csv(request, response)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-surveys'))
            return response
        elif request.POST.get('action') == 'EXPORT-EATOOL2-SURVEY':
            success, err = EaTool2SurveyData.export_csv(request, response)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-surveys'))
            return response
        elif request.POST.get('action') == 'EXPORT-ENDLINE-SURVEY':
            success, err = EndlineSurveyData.export_csv(request, response)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-surveys'))
            return response
    elif request.method == 'GET':
        return render(request, 'admin/reports/surveys.html')