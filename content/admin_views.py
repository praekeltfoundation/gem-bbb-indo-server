from datetime import datetime

from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth.decorators import permission_required
from django.http.response import JsonResponse, StreamingHttpResponse

from wagtail.wagtailadmin import messages

from .reports import GoalReport, UserReport, SavingsReport, SummaryDataPerChallenge, \
    SummaryDataPerQuiz, ChallengeExportPicture, ChallengeExportQuiz, ChallengeExportFreetext, SummaryGoalData, \
    GoalDataPerCategory, RewardsData, RewardsDataPerBadge, RewardsDataPerStreak, UserTypeData, SummarySurveyData, \
    EaTool1SurveyData, BaselineSurveyData, EaTool2SurveyData, EndlineSurveyData, BudgetUserData

from .models import Challenge, Participant, Feedback


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


@permission_required('feedback.can_change')
@ensure_csrf_cookie
def feedback_mark_read(request, feedback_pk):
    feedback = get_object_or_404(Feedback, pk=feedback_pk)
    feedback.is_read = not feedback.is_read
    feedback.save()
    return JsonResponse({})


#############
# Reporting #
#############

def get_report_generation_time():
    time = datetime.now()
    time = str(time)
    time = time.replace(' ', "_")
    time = time.replace('.', '_')
    time = time.replace(':', '_')

    return time


def report_index_page(request):
    return render(request, 'admin/reports/index.html')


# Challenge reports
def report_challenge_exports(request):

    if request.method == 'POST':
        response = StreamingHttpResponse(content_type='application/zip; charset=utf-8')

        if request.POST.get('action') == 'EXPORT-CHALLENGE-SUMMARY':
            export_name = 'Challenge_Summary'
            unique_time = get_report_generation_time()

            if request.POST['date_from'] is '' or request.POST['date_to'] is '':
                date_from = date_to = None
            else:
                date_from = request.POST['date_from']
                date_to = request.POST['date_to']

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            success, err = SummaryDataPerChallenge.export_csv(request, response, export_name, unique_time,
                                                              date_from=date_from, date_to=date_to)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-challenges'))
            return response
        elif request.POST.get('action') == 'EXPORT-CHALLENGE-QUIZ-SUMMARY':
            export_name = 'Challenge_Quiz_Summary'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            success, err = SummaryDataPerQuiz.export_csv(request, response, export_name, unique_time)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-challenges'))
            return response
        elif request.POST.get('action') == 'EXPORT-CHALLENGE-PICTURE':
            challenge_name = request.POST['picture-challenge-name']
            export_name = 'Challenge_Picture'
            unique_time = get_report_generation_time()
            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            success, err = ChallengeExportPicture.export_csv(request, response, export_name, unique_time, challenge_name=challenge_name)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-challenges'))
            return response
        elif request.POST.get('action') == 'EXPORT-CHALLENGE-QUIZ':
            challenge_name = request.POST['quiz-challenge-name']
            export_name = 'Challenge_Quiz'
            unique_time = get_report_generation_time()
            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            success, err = ChallengeExportQuiz.export_csv(request, response, export_name, unique_time, challenge_name=challenge_name)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-challenges'))
            return response
        elif request.POST.get('action') == 'EXPORT-CHALLENGE-FREETEXT':
            challenge_name = request.POST['freetext-challenge-name']
            export_name = 'Challenge_Freetext'
            unique_time = get_report_generation_time()
            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            success, err = ChallengeExportFreetext.export_csv(request, response, export_name, unique_time, challenge_name=challenge_name)
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

        if request.POST.get('action') == 'EXPORT-GOAL':
            export_name = 'Goal_Summary'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            success, err = GoalReport.export_csv(request, response, export_name, unique_time)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-goals'))
            return response
        elif request.POST.get('action') == 'EXPORT-USER':
            export_name = 'User_Summary'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            success, err = UserReport.export_csv(request, response, export_name, unique_time)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-goals'))
            return response
        elif request.POST.get('action') == 'EXPORT-SAVINGS':
            export_name = 'Savings_Summary'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            success, err = SavingsReport.export_csv(request, response, export_name, unique_time)
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

        if request.POST.get('action') == 'EXPORT-AGGREGATE-SUMMARY':
            export_name = 'Aggregate_Summary'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            success, err = SummaryGoalData.export_csv(request, response, export_name, unique_time)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-aggregates'))
            return response
        elif request.POST.get('action') == 'EXPORT-AGGREGATE-GOAL-PER-CATEGORY':
            export_name = 'Aggregate_Goal_Per_Category'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            success, err = GoalDataPerCategory.export_csv(request, response, export_name, unique_time)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-aggregates'))
            return response
        elif request.POST.get('action') == 'EXPORT-AGGREGATE-REWARDS-DATA':
            export_name = 'Aggregate_Rewards_Data'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            success, err = RewardsData.export_csv(request, response, export_name, unique_time)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-aggregates'))
            return response
        elif request.POST.get('action') == 'EXPORT-AGGREGATE-DATA-PER-BADGE':
            export_name = 'Aggregate_Data_Per_Badge'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            success, err = RewardsDataPerBadge.export_csv(request, response, export_name, unique_time)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-aggregates'))
            return response
        elif request.POST.get('action') == 'EXPORT-AGGREGATE-DATA-PER-STREAK':
            export_name = 'Aggregate_Data_Per_Streak'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            success, err = RewardsDataPerStreak.export_csv(request, response, export_name, unique_time)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-aggregates'))
            return response
        elif request.POST.get('action') == 'EXPORT-AGGREGATE-USER-TYPE':
            export_name = 'Aggregate_User_Type'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            success, err = UserTypeData.export_csv(request, response, export_name, unique_time)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-aggregates'))
            return response
    elif request.method == 'GET':
        return render(request, 'admin/reports/aggregates.html')


# Survey exports
def report_survey_exports(request):

    if request.method == 'POST':
        response = StreamingHttpResponse(content_type='application/zip; charset=utf-8')

        if request.POST.get('action') == 'EXPORT-SURVEY-SUMMARY':
            export_name = 'Survey_Summary'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            success, err = SummarySurveyData.export_csv(request, response, export_name, unique_time)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-surveys'))
            return response
        elif request.POST.get('action') == 'EXPORT-BASELINE-SURVEY':
            export_name = 'Baseline_Survey'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            success, err = BaselineSurveyData.export_csv(request, response, export_name, unique_time)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-surveys'))
            return response
        elif request.POST.get('action') == 'EXPORT-EATOOL1-SURVEY':
            export_name = 'EATool1_Survey'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            success, err = EaTool1SurveyData.export_csv(request, response, export_name, unique_time)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-surveys'))
            return response
        elif request.POST.get('action') == 'EXPORT-EATOOL2-SURVEY':
            export_name = 'EATool2_Survey'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            success, err = EaTool2SurveyData.export_csv(request, response, export_name, unique_time)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-surveys'))
            return response
        elif request.POST.get('action') == 'EXPORT-ENDLINE-SURVEY':
            export_name = 'Endline_Survey'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            success, err = EndlineSurveyData.export_csv(request, response, export_name, unique_time)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-surveys'))
            return response
    elif request.method == 'GET':
        return render(request, 'admin/reports/surveys.html')

# Budget exports
def report_budget_exports(request):
    if request.method == 'POST':
        response = StreamingHttpResponse(content_type='application/zip; charset=utf-8')
        if request.POST.get('action') == 'EXPORT-BUDGET-USER':
            export_name = 'Budget_User'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            success, err = BudgetUserData.export_csv(request, response, export_name, unique_time)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-surveys'))
            return response
        elif request.POST.get('action') == 'EXPORT-BUDGET-AGGREGATE':
            export_name = 'Budget_Aggregate'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            success, err = BudgetUserData.export_csv(request, response, export_name, unique_time)
            if not success:
                messages.error(request, err)
                return redirect(reverse('content-admin:reports-surveys'))
            return response
    elif request.method == 'GET':
        return render(request, 'admin/reports/budget.html')

