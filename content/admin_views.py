from datetime import datetime

from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth.decorators import permission_required
from django.http.response import JsonResponse, StreamingHttpResponse
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailadmin import messages

from content.analytics_api import initialize_analytics_reporting, get_report, connect_ga_to_user

from content.tasks import export_goal_summary, export_user_summary, export_challenge_summary, \
    export_challenge_quiz_summary, export_challenge_picture, export_challenge_freetext, export_challenge_quiz, \
    export_savings_summary, export_aggregate_summary, export_aggregate_goal_data_per_category, \
    export_aggregate_rewards_data, export_aggregate_data_per_badge, export_aggregate_data_per_streak, \
    export_aggregate_user_type, export_survey_summary, export_baseline_survey, export_ea1tool_survey, \
    export_ea2tool_survey, export_endline_survey, export_budget_user, export_budget_expense_category, \
    export_budget_aggregate

from .models import Challenge, Participant, Feedback


SUCCESS_MESSAGE_EMAIL_SENT = _('Report and password has been sent in an email.')


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
            export_challenge_summary.delay(request.user.email, export_name, unique_time, date_from=date_from, date_to=date_to)

            messages.success(request, SUCCESS_MESSAGE_EMAIL_SENT)
            return redirect(reverse('content-admin:reports-challenges'))
        elif request.POST.get('action') == 'EXPORT-CHALLENGE-QUIZ-SUMMARY':
            export_name = 'Challenge_Quiz_Summary'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            export_challenge_quiz_summary.delay(request.user.email, export_name, unique_time)
            messages.success(request, SUCCESS_MESSAGE_EMAIL_SENT)
            return redirect(reverse('content-admin:reports-challenges'))
        elif request.POST.get('action') == 'EXPORT-CHALLENGE-PICTURE':
            challenge_name = request.POST['picture-challenge-name']
            export_name = 'Challenge_Picture'
            unique_time = get_report_generation_time()
            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            export_challenge_picture.delay(request.user.email, export_name, unique_time, challenge_name=challenge_name)
            messages.success(request, SUCCESS_MESSAGE_EMAIL_SENT)
            return redirect(reverse('content-admin:reports-challenges'))
        elif request.POST.get('action') == 'EXPORT-CHALLENGE-QUIZ':
            challenge_name = request.POST['quiz-challenge-name']
            export_name = 'Challenge_Quiz'
            unique_time = get_report_generation_time()
            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            export_challenge_quiz.delay(request.user.email, export_name, unique_time, challenge_name=challenge_name)
            messages.success(request, SUCCESS_MESSAGE_EMAIL_SENT)
            return redirect(reverse('content-admin:reports-challenges'))
        elif request.POST.get('action') == 'EXPORT-CHALLENGE-FREETEXT':
            challenge_name = request.POST['freetext-challenge-name']
            export_name = 'Challenge_Freetext'
            unique_time = get_report_generation_time()
            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            export_challenge_freetext.delay(request.user.email, export_name, unique_time, challenge_name=challenge_name)
            messages.success(request, SUCCESS_MESSAGE_EMAIL_SENT)
            return redirect(reverse('content-admin:reports-challenges'))
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
            export_goal_summary.delay(request.user.email, export_name, unique_time)
            messages.success(request, SUCCESS_MESSAGE_EMAIL_SENT)
            return redirect(reverse('content-admin:reports-goals'))
            # return response
        elif request.POST.get('action') == 'EXPORT-USER':
            export_name = 'User_Summary'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            export_user_summary.delay(request.user.email, export_name, unique_time)
            messages.success(request, SUCCESS_MESSAGE_EMAIL_SENT)
            return redirect(reverse('content-admin:reports-goals'))
        elif request.POST.get('action') == 'EXPORT-SAVINGS':
            export_name = 'Savings_Summary'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            export_savings_summary.delay(request.user.email, export_name, unique_time)
            messages.success(request, SUCCESS_MESSAGE_EMAIL_SENT)
            return redirect(reverse('content-admin:reports-goals'))
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
            export_aggregate_summary.delay(request.user.email, export_name, unique_time)
            messages.success(request, SUCCESS_MESSAGE_EMAIL_SENT)
            return redirect(reverse('content-admin:reports-aggregates'))
        elif request.POST.get('action') == 'EXPORT-AGGREGATE-GOAL-PER-CATEGORY':
            export_name = 'Aggregate_Goal_Per_Category'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            export_aggregate_goal_data_per_category.delay(request.user.email, export_name, unique_time)
            messages.success(request, SUCCESS_MESSAGE_EMAIL_SENT)
            return redirect(reverse('content-admin:reports-aggregates'))
        elif request.POST.get('action') == 'EXPORT-AGGREGATE-REWARDS-DATA':
            export_name = 'Aggregate_Rewards_Data'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            export_aggregate_rewards_data.delay(request.user.email, export_name, unique_time)
            messages.success(request, SUCCESS_MESSAGE_EMAIL_SENT)
            return redirect(reverse('content-admin:reports-aggregates'))
        elif request.POST.get('action') == 'EXPORT-AGGREGATE-DATA-PER-BADGE':
            export_name = 'Aggregate_Data_Per_Badge'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            export_aggregate_data_per_badge.delay(request.user.email, export_name, unique_time)
            messages.success(request, SUCCESS_MESSAGE_EMAIL_SENT)
            return redirect(reverse('content-admin:reports-aggregates'))
        elif request.POST.get('action') == 'EXPORT-AGGREGATE-DATA-PER-STREAK':
            export_name = 'Aggregate_Data_Per_Streak'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            export_aggregate_data_per_streak.delay(request.user.email, export_name, unique_time)
            messages.success(request, SUCCESS_MESSAGE_EMAIL_SENT)
            return redirect(reverse('content-admin:reports-aggregates'))
        elif request.POST.get('action') == 'EXPORT-AGGREGATE-USER-TYPE':
            export_name = 'Aggregate_User_Type'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            export_aggregate_user_type.delay(request.user.email, export_name, unique_time)
            messages.success(request, SUCCESS_MESSAGE_EMAIL_SENT)
            return redirect(reverse('content-admin:reports-aggregates'))
        elif request.POST.get('action') == 'RECONCILE-GA-CAMPAIGN':
            print("Starting GA connection")
            analytics = initialize_analytics_reporting()
            response = get_report(analytics)
            connect_ga_to_user(response)
            print("Finished GA connection")
            return render(request, 'admin/reports/aggregates.html')
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
            export_survey_summary.delay(request.user.email, export_name, unique_time)
            messages.success(request, SUCCESS_MESSAGE_EMAIL_SENT)
            return redirect(reverse('content-admin:reports-surveys'))
        elif request.POST.get('action') == 'EXPORT-BASELINE-SURVEY':
            export_name = 'Baseline_Survey'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            export_baseline_survey.delay(request.user.email, export_name, unique_time)
            messages.success(request, SUCCESS_MESSAGE_EMAIL_SENT)
            return redirect(reverse('content-admin:reports-surveys'))
        elif request.POST.get('action') == 'EXPORT-EATOOL1-SURVEY':
            export_name = 'EATool1_Survey'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            export_ea1tool_survey.delay(request.user.email, export_name, unique_time)
            messages.success(request, SUCCESS_MESSAGE_EMAIL_SENT)
            return redirect(reverse('content-admin:reports-surveys'))
        elif request.POST.get('action') == 'EXPORT-EATOOL2-SURVEY':
            export_name = 'EATool2_Survey'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            export_ea2tool_survey.delay(request.user.email, export_name, unique_time)
            messages.success(request, SUCCESS_MESSAGE_EMAIL_SENT)
            return redirect(reverse('content-admin:reports-surveys'))
        elif request.POST.get('action') == 'EXPORT-ENDLINE-SURVEY':
            export_name = 'Endline_Survey'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            export_endline_survey.delay(request.user.email, export_name, unique_time)
            messages.success(request, SUCCESS_MESSAGE_EMAIL_SENT)
            return redirect(reverse('content-admin:reports-surveys'))
    elif request.method == 'GET':
        return render(request, 'admin/reports/surveys.html')


def quiz_challenge_entries(request):
    if request.method == 'GET':
        context = {
            'quiz_challenges': list(Challenge.objects.filter(type=Challenge.CTP_QUIZ))
        }

        return render(request, 'admin/challenge/quizentries.html', context=context)


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
            export_budget_user.delay(request.user.email, export_name, unique_time)
            messages.success(request, SUCCESS_MESSAGE_EMAIL_SENT)
            return redirect(reverse('content-admin:reports-budget'))
        elif request.POST.get('action') == 'EXPORT-BUDGET-EXPENSE-CATEGORY':
            export_name = 'Budget_Expense_Category'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            export_budget_expense_category.delay(request.user.email, export_name, unique_time)
            messages.success(request, SUCCESS_MESSAGE_EMAIL_SENT)
            return redirect(reverse('content-admin:reports-budget'))
        elif request.POST.get('action') == 'EXPORT-BUDGET-AGGREGATE':
            export_name = 'Budget_Aggregate'
            unique_time = get_report_generation_time()

            response['Content-Disposition'] = 'attachment;filename=' \
                                              + export_name \
                                              + unique_time \
                                              + '.zip'
            export_budget_aggregate.delay(request.user.email, export_name, unique_time)
            messages.success(request, SUCCESS_MESSAGE_EMAIL_SENT)
            return redirect(reverse('content-admin:reports-budget'))
    elif request.method == 'GET':
        return render(request, 'admin/reports/budget.html')
