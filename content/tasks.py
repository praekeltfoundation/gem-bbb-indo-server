# -*- coding: utf-8 -*-
import os
import json

from celery.task import task

from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from content.analytics_api import get_report, connect_ga_to_user, initialize_analytics_reporting
from content.celery import app
from content.models import Goal, GoalTransaction, UserBadge, Badge, Participant, Challenge, QuizQuestion, \
    QuestionOption, ParticipantAnswer, ParticipantPicture, ParticipantFreeText, GoalPrototype, Budget, ExpenseCategory, \
    Expense
from content.utilities import append_to_csv, create_csv, pass_zip_encrypt_email
from survey.models import CoachSurveySubmission, CoachSurvey, CoachSurveySubmissionDraft
from users.models import Profile, CampaignInformation

SUCCESS_MESSAGE_EMAIL_SENT = _('Report and password has been sent in an email.')
ERROR_MESSAGE_NO_EMAIL = _('No email address associated with this account.')
ERROR_MESSAGE_DATA_CLEANUP = _('Report generation ran during data cleanup - try again')


@task(ignore_result=False, max_retries=10, default_retry_delay=10)
def just_print():
    print("Just Print")


@app.task(ignore_result=True, max_retries=10, default_retry_delay=10)
def remove_report_archives():
    print("Starting removal")
    for filename in os.listdir(settings.SENDFILE_ROOT):
        if filename.endswith('.csv') or filename.endswith('.zip'):
            try:
                os.remove(settings.SENDFILE_ROOT + '\\' + filename)
            except FileNotFoundError:
                # Do nothing as there is no file to delete, name has changed
                pass


@app.task(ignore_result=True, max_retries=10, default_retry_delay=10)
def ga_task_handler():
    print("Starting GA connection")
    analytics = initialize_analytics_reporting()
    response = get_report(analytics)
    connect_ga_to_user(response)
    print("Finished GA connection")


###########################
# Report Generation Tasks #
###########################


STORAGE_DIRECTORY = settings.SENDFILE_ROOT + '\\'


#####################
# Goal Data Reports #
#####################


@task(name="export_goal_summary")
def export_goal_summary(email, export_name, unique_time):
    goals = Goal.objects.filter(user__is_staff=False, user__is_active=True)

    filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'

    create_csv(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        append_to_csv(('username', 'prototype_bahasa', 'prototype_english', 'goal_name', 'goal_target',
                       'goal_value', 'goal_progress', 'weekly_target', 'total_weeks', 'weeks_left',
                       'weeks_saved', 'week_saved_on_target', 'weeks_saved_below_target',
                       'weeks_saved_above_target', 'weeks_not_saved', 'withdrawals',

                       # Goal edit history
                       'original_goal_date', 'current_goal_date', 'original_weekly_target',
                       'current_weekly_target', 'original_goal_target', 'current_goal_target', 'date_edited',

                       'date_created', 'goal_achieved', 'goal_deleted', 'date_deleted'),
                      csvfile)

        for goal in goals:
            data = [
                # Weekly savings
                get_username(goal),
                '',  # TODO: Goal prototype in Bahasa (Not implemented)
                goal.prototype,
                goal.name,
                goal.target,
                goal.value,
                goal.progress,
                goal.weekly_target,
                goal.weeks,
                goal.weeks_left,
                num_weeks_saved(goal),
                num_weeks_saved_on_target(goal),
                num_weeks_saved_below(goal),
                num_weeks_saved_above(goal),
                num_weeks_not_saved(goal),
                num_withdrawals(goal),

                # Goal edits
                goal.original_end_date,
                goal.end_date,
                goal.original_weekly_target,
                goal.weekly_target,
                goal.original_target,
                goal.target,
                goal.last_edit_date,

                # Goal dates
                goal.start_date,
                date_achieved(goal),
                not goal.is_active,
                goal.date_deleted
            ]

            append_to_csv(data, csvfile)

    pass_zip_encrypt_email(email, export_name, unique_time)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


def get_username(goal):
    """Returns the user whom the goal belongs too"""
    return goal.user.username


def num_weeks_saved(goal):
    """Returns the number of weeks that the user has saved"""

    weekly_aggregates = goal.get_weekly_aggregates_to_date()

    weeks_saved = 0
    for weekly_savings in weekly_aggregates:
        if weekly_savings is not 0:
            weeks_saved += 1

    return weeks_saved


def num_weeks_saved_on_target(goal):
    """Returns the number of weeks the user saved the same as their weekly target"""

    weekly_aggregates = goal.get_weekly_aggregates_to_date()

    weeks_saved_on_target = 0
    for weekly_savings in weekly_aggregates:
        if weekly_savings == goal.weekly_target:
            weeks_saved_on_target += 1

    return weeks_saved_on_target


def num_weeks_saved_below(goal):
    """Returns the number of weeks, that when the user saved, they saved below their weekly target"""

    weekly_aggregates = goal.get_weekly_aggregates_to_date()

    weeks_saved_below_target = 0
    for weekly_savings in weekly_aggregates:
        if 0 < weekly_savings < goal.weekly_target:
            weeks_saved_below_target += 1

    return weeks_saved_below_target


def num_weeks_saved_above(goal):
    """Returns the number of weeks the user saved above their weekly target"""

    weekly_aggregates = goal.get_weekly_aggregates_to_date()

    weeks_saved_above_target = 0
    for weekly_savings in weekly_aggregates:
        if weekly_savings > goal.weekly_target:
            weeks_saved_above_target += 1

    return weeks_saved_above_target


def num_weeks_not_saved(goal):
    """Returns the number of weeks the user did not save"""

    weekly_aggregates = goal.get_weekly_aggregates_to_date()

    weeks_not_saved = 0
    for weekly_savings in weekly_aggregates:
        if weekly_savings == 0:
            weeks_not_saved += 1

    return weeks_not_saved


def num_withdrawals(goal):
    """Returns the number of withdrawals made on a goal"""
    transactions = GoalTransaction.objects.filter(goal=goal)

    if not transactions:
        return 0

    withdrawals = 0

    for t in transactions:
        if t.is_withdraw:
            withdrawals += 1

    return withdrawals


def date_achieved(goal):
    """Returns the date of the transaction that caused the user to achieve their goal"""
    if goal.progress < 100:
        return None

    transactions = GoalTransaction.objects.filter(goal=goal)

    amount_saved = 0
    target = goal.target

    for transaction in transactions:
        amount_saved += transaction.value

        if amount_saved >= target:
            return transaction.date

    return None


@task(name="export_user_summary")
def export_user_summary(email, export_name, unique_time):
    profiles = Profile.objects.filter(user__is_staff=False, user__is_active=True)
    filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
    create_csv(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        append_to_csv(('username', 'name', 'mobile', 'email', 'gender', 'age', 'user_type_source_medium',
                       'date_joined', 'number_of_goals', 'total_badges_earned', 'first_goal_created_badges',
                       'first_savings_created_badges', 'halfway_badges', 'one_week_left_badges',
                       '2_week_streak_badges', '4_week_streak_badges', '6_week_streak_badges',
                       '2_week_on_track_badges', '4_week_on_track_badges', '8_week_on_track_badges',
                       'goal_reached_badges', 'budget_created_badges', 'budget_revision_badges',
                       'highest_streak_earned', 'total_streak_and_ontrack_badges', 'baseline_survey_complete',
                       'ea_tool1_completed', 'ea_tool2_completed', 'endline_survey_completed'),
                      csvfile)

        for profile in profiles:
            try:
                campaign_info = CampaignInformation.objects.get(user=profile.user)
                user_type = campaign_info.source + '/' + campaign_info.medium
            except:
                user_type = ''

            data = [
                profile.user.username,
                profile.user.first_name + " " + profile.user.last_name,
                profile.mobile,
                profile.user.email,
                profile.gender,
                profile.age,
                user_type,
                profile.user.date_joined,
                number_of_goals(profile),
                total_badges_earned(profile),
                num_first_goal_created_badges(profile),
                num_first_savings_created_badges(profile),
                num_halfway_badges(profile),
                num_one_week_left_badges(profile),
                num_2_week_streak_badges(profile),
                num_4_week_streak_badges(profile),
                num_6_week_streak_badges(profile),
                num_2_week_on_track_badges(profile),
                num_4_week_on_track_badges(profile),
                num_8_week_on_track_badges(profile),
                num_goal_reached_badges(profile),
                num_budget_created_badges(profile),
                num_budget_revision_badges(profile),
                highest_streak_earned(profile),
                total_streaks_earned(profile),
                total_streak_and_ontrack_badges(profile),
                baseline_survey_complete(profile),
                ea_tool1_completed(profile),
                ea_tool2_completed(profile),
                endline_survey_completed(profile)
            ]

            append_to_csv(data, csvfile)

    pass_zip_encrypt_email(email, export_name, unique_time)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


def number_of_goals(profile):
    """Returns the number of goals the user has"""
    user = profile.user
    return Goal.objects.filter(user=user).count()


def total_badges_earned(profile):
    """Returns the total number of badges earned by the user"""
    user = profile.user
    return UserBadge.objects.filter(user=user).count()


def num_first_goal_created_badges(profile):
    return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.GOAL_FIRST_CREATED).count()


def num_first_savings_created_badges(profile):
    return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.TRANSACTION_FIRST).count()


def num_halfway_badges(profile):
    return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.GOAL_HALFWAY).count()


def num_one_week_left_badges(profile):
    return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.GOAL_WEEK_LEFT).count()


def num_2_week_streak_badges(profile):
    return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.STREAK_2).count()


def num_4_week_streak_badges(profile):
    return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.STREAK_4).count()


def num_6_week_streak_badges(profile):
    return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.STREAK_6).count()


def num_2_week_on_track_badges(profile):
    return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.WEEKLY_TARGET_2).count()


def num_4_week_on_track_badges(profile):
    return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.WEEKLY_TARGET_4).count()


def num_6_week_on_track_badges(profile):
    return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.WEEKLY_TARGET_6).count()


def num_8_week_on_track_badges(profile):
    # TODO: Count number of 8 week on Track badges (Not implemented)
    return 0


def num_goal_reached_badges(profile):
    return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.GOAL_FIRST_DONE).count()


def num_challenge_participation_badges(profile):
    return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.CHALLENGE_ENTRY).count()


def highest_streak_earned(profile):
    """Returns the highest streak of weeks a user has saved, regardless of weekly target"""
    goals = Goal.objects.filter(user=profile.user)
    highest_streak = 0
    current_count = 0
    for goal in goals:
        transactions = goal.get_weekly_aggregates_to_date()
        for trans in transactions:
            if trans != 0:
                current_count += 1
                if current_count > highest_streak:
                    highest_streak = current_count
            else:
                current_count = 0
    return highest_streak


def total_streak_and_ontrack_badges(profile):
    """Returns the total amount of streak and on track badges"""
    total_2_week_streak = UserBadge.objects.filter(user=profile.user,
                                                   badge__badge_type=Badge.STREAK_2).count()
    total_4_week_streak = UserBadge.objects.filter(user=profile.user,
                                                   badge__badge_type=Badge.STREAK_4).count()
    total_6_week_streak = UserBadge.objects.filter(user=profile.user,
                                                   badge__badge_type=Badge.STREAK_6).count()
    total_2_week_on_target = UserBadge.objects.filter(user=profile.user,
                                                      badge__badge_type=Badge.WEEKLY_TARGET_2).count()
    total_4_week_on_target = UserBadge.objects.filter(user=profile.user,
                                                      badge__badge_type=Badge.WEEKLY_TARGET_4).count()
    total_6_week_on_target = UserBadge.objects.filter(user=profile.user,
                                                      badge__badge_type=Badge.WEEKLY_TARGET_6).count()
    total_streaks = total_2_week_streak + total_4_week_streak + total_6_week_streak
    total_on_targets = total_2_week_on_target + total_4_week_on_target + total_6_week_on_target
    total_all = total_streaks + total_on_targets
    return total_all


def total_streaks_earned(profile):
    """Returns the total number of streaks a user has saved for. Since saving for 1 week counts as a streak
    this is basically just the number of weeks saved"""
    goals = Goal.objects.filter(user=profile.user)
    total_streaks = 0
    current_count = 0
    for goal in goals:
        transactions = goal.get_weekly_aggregates_to_date()
        for trans in transactions:
            if trans != 0:
                current_count += 1
                if current_count > 1:
                    total_streaks += 1
            else:
                current_count = 0
    return total_streaks


def num_quiz_complete_badges(profile):
    # TODO: Return the number of Quiz Completed badges (Not implemented)
    return 0


def num_5_challenges_completed_badge(profile):
    # TODO: Return the number of 5 Challenges badges (Not implemented)
    return 0


def num_5_quizzes_badges(profile):
    # TODO: Return the number of 5 Quizzes badges (Not implemented)
    return 0


def num_perfect_score_badges(profile):
    # TODO: Return the number of Perfect Score badges (Not implemented)
    return 0


def num_budget_created_badges(profile):
    return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.BUDGET_CREATE).count()


def num_budget_revision_badges(profile):
    return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.BUDGET_EDIT).count()


def baseline_survey_complete(profile):
    """Return True/False if a user has completed the baseline survey"""
    try:
        CoachSurveySubmission.objects.get(user=profile.user, survey__bot_conversation=CoachSurvey.BASELINE)
        return True
    except:
        return False


def ea_tool1_completed(profile):
    try:
        CoachSurveySubmission.objects.get(user=profile.user, survey__bot_conversation=CoachSurvey.EATOOL)
        return True
    except:
        return False


def ea_tool2_completed(profile):
    # TODO: Return true/False if a user has completed the EA Tool 2 survey (Not implemented)
    return False


def endline_survey_completed(profile):
    # TODO: Return true/False if a user has completed the endline survey (Not implemented)
    return False


@task(name="export_savings_summary")
def export_savings_summary(email, export_name, unique_time):
    goals = Goal.objects.filter(user__is_staff=False, user__is_active=True)

    filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
    create_csv(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        append_to_csv(('username', 'goal_name', 'goal_weekly_target', 'transaction_type', 'transaction_value',
                       'transaction_date', 'amount_saved'),
                      csvfile)

        for goal in goals:
            amount_saved = 0
            for transaction in GoalTransaction.objects.filter(goal=goal):
                amount_saved += transaction.value
                data = [
                    # User
                    goal.user.username,

                    # Savings plan details
                    goal.name,
                    goal.weekly_target,

                    # Deposit/Withdrawal details
                    transaction.is_deposit,
                    transaction.value,
                    transaction.date,
                    amount_saved
                ]

                append_to_csv(data, csvfile)

    pass_zip_encrypt_email(email, export_name, unique_time)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


#####################
# Challenge Reports #
#####################

@task(name="export_challenge_summary")
def export_challenge_summary(email, export_name, unique_time, date_from, date_to):
    if date_from is not None and date_to is not None:
        challenges = Challenge.objects.filter(activation_date__gte=date_from, deactivation_date__lte=date_to)
    else:
        challenges = Challenge.objects.all()

    filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
    create_csv(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:

        append_to_csv(('challenge_name', 'challenge_type', 'call_to_action', 'activation_date', 'deactivation_date',
                       'total_challenge_completions', 'total_users_in_progress', 'total_no_response'),
                      csvfile)

        for challenge in challenges:
            data = [
                challenge.name,
                challenge.get_type_display(),
                challenge.call_to_action,
                challenge.activation_date,
                challenge.deactivation_date,
                total_challenge_completions(challenge),
                total_users_in_progress(challenge),
                total_no_response(challenge)
            ]

            append_to_csv(data, csvfile)

    pass_zip_encrypt_email(email, export_name, unique_time)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


def total_challenge_completions(challenge):
    """Returns the number of participants who have completed a challenge"""

    return Participant.objects.filter(user__is_staff=False, user__is_active=True,
                                      challenge=challenge, date_completed__isnull=False).count()


def total_users_in_progress(challenge):
    """Returns the total number of participants who have started the challenge but not completed it"""
    return Participant.objects.filter(user__is_staff=False, user__is_active=True,
                                      challenge=challenge, date_completed__isnull=True).count()


def total_no_response(challenge):
    """Checks to see which users don't have a participant for the given challenge"""
    total_amount_of_users = User.objects.filter(is_staff=False, user__is_active=True).count()
    total_amount_of_participants = Participant.objects.filter(user__is_staff=False,
                                                              user__is_active=True,
                                                              challenge=challenge).count()

    num_no_responses = total_amount_of_users - total_amount_of_participants

    return num_no_responses


@task(name="export_challenge_quiz_summary")
def export_challenge_quiz_summary(email, export_name, unique_time):
    challenges = Challenge.objects.filter(type=Challenge.CTP_QUIZ)

    filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
    create_csv(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        append_to_csv(('quiz_name', 'quiz_question', 'number_of_options', 'avg_attempts'), csvfile)

        for challenge in challenges:
            quiz_questions = QuizQuestion.objects.filter(challenge=challenge)

            quiz_question_data = []
            for quiz_question in quiz_questions:
                question_options = QuestionOption.objects.filter(question=quiz_question)

                unique_user_attempts = ParticipantAnswer.objects.filter(question=quiz_question).values('entry__participant').distinct().count()
                total_attempts = ParticipantAnswer.objects.filter(question=quiz_question).count()

                if total_attempts != 0:
                    avg_no_of_attempts = total_attempts / unique_user_attempts
                else:
                    avg_no_of_attempts = 0

                quiz_question_data.extend([quiz_question.text, question_options.count(), avg_no_of_attempts],)

            data = [
                challenge.name,
            ]

            data.extend(quiz_question_data)

            append_to_csv(data, csvfile)

    pass_zip_encrypt_email(email, export_name, unique_time)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


@task(name="export_challenge_picture")
def export_challenge_picture(email, export_name, unique_time, challenge_name):
    challenges = Challenge.objects.filter(type=Challenge.CTP_PICTURE, name=challenge_name)

    filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
    create_csv(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        append_to_csv(('username', 'name', 'mobile', 'email', 'gender', 'age',
                       'user_type_source_medium', 'date_joined', 'call_to_action'),
                      csvfile)

        for challenge in challenges:
            participants = Participant.objects.filter(user__is_staff=False, user__is_active=True, challenge=challenge)

            for participant in participants:
                profile = Profile.objects.get(user=participant.user)
                participant_picture = ParticipantPicture.objects.filter(participant=participant).first()

                if participant_picture:
                    date_answered = str(participant_picture.date_answered)
                else:
                    date_answered = ''

                try:
                    campaign_info = CampaignInformation.objects.get(user=profile.user)
                    user_type = campaign_info.source + '/' + campaign_info.medium
                except:
                    user_type = ''

                data = [
                    participant.user.username,
                    participant.user.first_name,
                    profile.mobile,
                    participant.user.email,
                    profile.gender,
                    profile.age,
                    user_type,
                    profile.user.date_joined,
                    challenge.call_to_action + ' ' + date_answered
                ]

                append_to_csv(data, csvfile)

    pass_zip_encrypt_email(email, export_name, unique_time)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


@task(name="export_challenge_quiz")
def export_challenge_quiz(email, export_name, unique_time, challenge_name):
    challenges = Challenge.objects.filter(type=Challenge.CTP_QUIZ, name=challenge_name)

    filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
    create_csv(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        append_to_csv(('username', 'name', 'mobile', 'email', 'gender', 'age', 'user_type_source_medium',
                       'date_joined', 'submission_date', 'selected_option', 'number_of_attempts'),
                      csvfile)

        for challenge in challenges:
            participants = Participant.objects.filter(user__is_staff=False,
                                                      user__is_active=True,
                                                      challenge=challenge)

            quiz_questions = QuizQuestion.objects.filter(challenge=challenge)

            for participant in participants:
                profile = Profile.objects.get(user=participant.user)
                try:
                    campaign_info = CampaignInformation.objects.get(user=profile.user)
                    user_type = campaign_info.source + '/' + campaign_info.medium
                except:
                    user_type = ''

                all_answers = ParticipantAnswer.objects.filter(entry__participant=participant)

                if len(all_answers.reverse()) > 0:
                    date_completed = all_answers.reverse()[0].date_saved
                else:
                    date_completed = 'incomplete'

                data = [
                    participant.user.username,
                    participant.user.first_name,
                    profile.mobile,
                    participant.user.email,
                    profile.gender,
                    profile.age,
                    user_type,  # user type
                    participant.user.date_joined,
                    date_completed,
                ]

                correct_answers = ParticipantAnswer.objects.filter(entry__participant=participant, selected_option__correct=True)
                for correct_answer in correct_answers:
                    question_data = [correct_answer.selected_option.text,
                                     all_answers.filter(question=correct_answer.question).count()]
                    data.extend(question_data)

                append_to_csv(data, csvfile)

    pass_zip_encrypt_email(email, export_name, unique_time)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


@task(name="export_challenge_freetext")
def export_challenge_freetext(email, export_name, unique_time, challenge_name):
    challenges = Challenge.objects.filter(type=Challenge.CTP_FREEFORM, name=challenge_name)

    filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
    create_csv(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        append_to_csv(('username', 'name', 'mobile', 'email', 'gender', 'age', 'user_type_source_medium',
                       'date_registered', 'submission', 'submission_date'),
                      csvfile)

        for challenge in challenges:
            participants = Participant.objects.filter(user__is_staff=False, user__is_active=True, challenge=challenge)

            for participant in participants:
                try:
                    campaign_info = CampaignInformation.objects.get(user=participant.user)
                    user_type = campaign_info.source + '/' + campaign_info.medium
                except:
                    user_type = ''
                profile = Profile.objects.get(user=participant.user)

                # With a free text challenge, there can be a participant but no entry
                # This try/catch prevents a crash for when the user has started a challenge but not submitted an entry
                try:
                    participant_free_text = ParticipantFreeText.objects.get(participant=participant)

                    data = [
                        participant.user.username,
                        participant.user.first_name,
                        profile.mobile,
                        participant.user.email,
                        profile.gender,
                        profile.age,
                        user_type,  # user type
                        participant.date_created,
                        participant_free_text.text,
                        participant_free_text.date_answered
                    ]

                    append_to_csv(data, csvfile)

                except ParticipantFreeText.DoesNotExist:
                    pass

    pass_zip_encrypt_email(email, export_name, unique_time)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


##########################
# Aggregate Data Reports #
##########################

@task(name="export_aggregate_summary")
def export_aggregate_summary(email, export_name, unique_time):

    filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
    create_csv(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        append_to_csv(('total_users_set_at_least_one_goal', 'total_users_achieved_at_least_one_goal',
                       'total_achieved_goals', 'percentage_of_weeks_saved_out_of_total_weeks'),
                      csvfile)

        data = [
            num_users_set_at_least_one_goal(),
            num_users_achieved_one_goal(),
            num_achieved_goals(),
            percentage_weeks_saved()
        ]

        append_to_csv(data, csvfile)

    pass_zip_encrypt_email(email, export_name, unique_time)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


def num_users_set_at_least_one_goal():
    """Number of users with at least one goal set"""
    return Goal.objects.filter(user__is_staff=False, user__is_active=True).values('user_id').distinct().count()


def num_users_achieved_one_goal():
    """Total amount of users who have achieved at least one goal"""
    num_users_achieved_one_goal = 0
    array_of_users = Goal.objects.filter(user__is_staff=False, user__is_active=True).values('user_id').distinct()

    for user in array_of_users:
        goals = Goal.objects.filter(user_id=user['user_id'], user__is_staff=False, user__is_active=True)
        for goal in goals:
            if goal.progress >= 100:
                num_users_achieved_one_goal += 1
                break

    return num_users_achieved_one_goal


def num_achieved_goals():
    """Number of achieved goals"""
    goals = Goal.objects.filter(user__is_staff=False, user__is_active=True)
    num_achieved_goals = 0
    for goal in goals:
        if goal.progress >= 100:
            num_achieved_goals += 1

    return num_achieved_goals


def percentage_weeks_saved():
    """Percentage weeks saved out of total weeks"""
    percentage_weeks_saved = 0
    goals = Goal.objects.filter(user__is_staff=False, user__is_active=True)
    total_weeks = 0
    total_weeks_saved = 0

    for goal in goals:
        weekly_savings = goal.get_weekly_aggregates_to_date()
        total_weeks += goal.weeks
        for amount_saved_in_week in weekly_savings:
            if amount_saved_in_week != 0:
                total_weeks_saved += 1

    if total_weeks is not 0 and total_weeks_saved is not 0:
        percentage_weeks_saved = (total_weeks_saved / total_weeks) * 100

    return percentage_weeks_saved


@task(name="export_aggregate_goal_data_per_category")
def export_aggregate_goal_data_per_category(email, export_name, unique_time):

    filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
    create_csv(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        append_to_csv(('category', 'total_users_at_least_one_goal', 'total_goals_set',
                       'total_users_achieved_one_goal', 'average_goal_amount', 'average_percentage_goal_reached',
                       'total_users_50_percent_achieved', 'total_users_100_percent_achieved',
                       'percentage_of_weeks_saved_out_of_total_weeks'),
                      csvfile)

        goal_prototypes = GoalPrototype.objects.all()

        for goal_prototype in goal_prototypes:
            data = [
                goal_prototype.name,
                Goal.objects.filter(prototype=goal_prototype).values('user_id').distinct().count(),
                Goal.objects.filter(prototype=goal_prototype).count(),
                total_users_achieved_at_least_one_goal(goal_prototype),
                average_total_goal_amount(goal_prototype),
                average_percentage_of_goal_reached(goal_prototype),
                total_users_50_percent_achieved(goal_prototype),
                total_users_100_percent_achieved(goal_prototype),
                percentage_of_weeks_saved_out_of_total_weeks(goal_prototype)
            ]

            append_to_csv(data, csvfile)

    pass_zip_encrypt_email(email, export_name, unique_time)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


def total_users_achieved_at_least_one_goal(goal_prototype):
    """
    Returns the number of users that have achieved the goal prototype
    unique users
    """
    users_with_goals = Goal.objects.filter(user__is_staff=False, user__is_active=True,
                                           prototype=goal_prototype).values('user_id').distinct()

    num_achieved_one_goal = 0
    for user in users_with_goals:
        users_goals = Goal.objects.filter(user__is_staff=False, user__is_active=True,
                                          prototype=goal_prototype, user_id=user['user_id'])

        for goal in users_goals:
            if goal.progress >= 100:
                num_achieved_one_goal += 1
                break

    return num_achieved_one_goal


def average_total_goal_amount(goal_prototype):
    """Returns the average goal amount for the given goal prototype"""
    goals = Goal.objects.filter(user__is_staff=False, user__is_active=True, prototype=goal_prototype)

    total_amount_of_goals_count = goals.count()

    total_goals_value = 0
    for goal in goals:
        total_goals_value += goal.value

    if total_goals_value is not 0 and total_amount_of_goals_count is not 0:
        return total_goals_value / total_amount_of_goals_count
    else:
        return 0


def average_percentage_of_goal_reached(goal_prototype):
    """Returns the average percentage of completions for the given goal prototype"""
    goals = Goal.objects.filter(user__is_staff=False, user__is_active=True, prototype=goal_prototype)

    total_amount_of_goals = goals.count()

    num_achieved_goals = 0
    for goal in goals:
        if goal.progress >= 100:
            num_achieved_goals += 1

    if num_achieved_goals is not 0 and total_amount_of_goals is not 0:
        return (num_achieved_goals / total_amount_of_goals) * 100
    else:
        return 0


def total_users_50_percent_achieved(goal_prototype):
    """Returns the total amount of users who have achieved 50% of the given goal prototype"""
    users_with_goals = Goal.objects.filter(user__is_staff=False, user__is_active=True,
                                           prototype=goal_prototype).values('user_id').distinct()

    num_50_percent_achieved = 0
    for user in users_with_goals:
        users_goals = Goal.objects.filter(user__is_staff=False, user__is_active=True,
                                          prototype=goal_prototype, user_id=user['user_id'])

        for goal in users_goals:
            if goal.progress >= 50:
                num_50_percent_achieved += 1
                break

    return num_50_percent_achieved


def total_users_100_percent_achieved(goal_prototype):
    """
    Returns the total amount of users who have achieved 100% of the given goal prototype
    not unique users
    """
    goals = Goal.objects.filter(user__is_staff=False, user__is_active=True, prototype=goal_prototype)

    num_100_percent_achieved = 0
    for goal in goals:
        users_goals = Goal.objects.filter(user__is_staff=False, user__is_active=True,
                                          prototype=goal_prototype, user_id=goal.user_id)

        for user_goal in users_goals:
            if user_goal.progress >= 100:
                num_100_percent_achieved += 1
                break

    return num_100_percent_achieved


def percentage_of_weeks_saved_out_of_total_weeks(goal_prototype):
    """Percentage of weeks saved for given goal prototype"""
    goals = Goal.objects.filter(user__is_staff=False, user__is_active=True, prototype=goal_prototype)
    total_weeks = 0
    total_weeks_saved = 0

    for goal in goals:
        agg = goal.get_weekly_aggregates_to_date()
        total_weeks += goal.weeks
        for aggCount in agg:
            if aggCount != 0:
                total_weeks_saved += 1

    if total_weeks == 0:
        return 0

    return (total_weeks_saved/total_weeks) * 100


@task(name="export_aggregate_rewards_data")
def export_aggregate_rewards_data(email, export_name, unique_time):

    filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
    create_csv(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        append_to_csv(('total_badges_earned_by_all_users', 'total_users_at_least_one_streak',
                       'average_percentage_weeks_saved_weekly_target_met', 'average_percentage_weeks_saved'),
                      csvfile)

        data = [
            UserBadge.objects.filter(user__is_staff=False, user__is_active=True).count(),
            total_users_at_least_one_streak(),
            average_percentage_weeks_saved_weekly_target_met(),
            average_percentage_weeks_saved()
        ]

        append_to_csv(data, csvfile)

    pass_zip_encrypt_email(email, export_name, unique_time)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


def total_users_at_least_one_streak():
    """Returns the total number of users that have at least one streak"""
    users_with_streaks = 0
    users = User.objects.filter(is_staff=False, user__is_active=True)

    for user in users:
        goals = Goal.objects.filter(user=user, user__is_staff=False, user__is_active=True)
        current_count = 0

        user_has_streak = False

        goal_generator = (goal for goal in goals if user_has_streak is False)

        for goal in goal_generator:
            transactions = goal.get_weekly_aggregates_to_date()

            transaction_generator = (transaction for transaction in transactions if user_has_streak is False)

            for trans in transaction_generator:
                if trans != 0:
                    current_count += 1
                    if current_count > 1:
                        users_with_streaks += 1
                        user_has_streak = True
                else:
                    current_count = 0

    return users_with_streaks


def average_percentage_weeks_saved_weekly_target_met():
    """Average % of weeks saved where users reached their weekly target savings amount"""
    total_weeks_saved = 0
    total_weeks = 0

    users = User.objects.filter(is_staff=False, user__is_active=True)

    for user in users:
        goals = Goal.objects.filter(user__is_staff=False, user__is_active=True, user=user)

        for goal in goals:
            weekly_aggregates = goal.get_weekly_aggregates_to_date()

            for week in weekly_aggregates:
                if week >= goal.weekly_target:
                    total_weeks_saved += 1

                total_weeks += 1

    if total_weeks_saved is not 0 and total_weeks is not 0:
        return (total_weeks_saved / total_weeks) * 100
    else:
        return 0


def average_percentage_weeks_saved():
    """Average % of weeks saved - regardless of savings amount"""
    total_weeks_saved = 0
    total_weeks = 0

    users = User.objects.filter(is_staff=False, user__is_active=True)

    for user in users:
        goals = Goal.objects.filter(user=user, user__is_staff=False, user__is_active=True)

        for goal in goals:
            weekly_aggregates = goal.get_weekly_aggregates_to_date()

            for week in weekly_aggregates:
                if week > 0:
                    total_weeks_saved += 1

                total_weeks += 1

    if total_weeks_saved is not 0 and total_weeks is not 0:
        return (total_weeks_saved / total_weeks) * 100
    else:
        return 0


@task(name="export_aggregate_data_per_badge")
def export_aggregate_data_per_badge(email, export_name, unique_time):

    filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
    create_csv(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        append_to_csv(('badge_name', 'total_earned_by_all_users', 'total_earned_at_least_once'),
                      csvfile)

        badges = Badge.objects.all()

        for badge in badges:
            data = [
                badge.name,
                total_earned_by_all_users(badge),
                total_earned_at_least_once(badge)
            ]

            append_to_csv(data, csvfile)

    pass_zip_encrypt_email(email, export_name, unique_time)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


def total_earned_by_all_users(badge):
    """Returns the total number of badges won for the given badge for all users"""
    return Badge.objects.filter(user__is_staff=False, user__is_active=True,
                                badge_type=badge.badge_type).values('user').count()


def total_earned_at_least_once(badge):
    """Return the total number of users that have earned the given badge at least once"""
    return Badge.objects.filter(user__is_staff=False, user__is_active=True,
                                badge_type=badge.badge_type).values('user').distinct().count()


@task(name="export_aggregate_data_per_streak")
def export_aggregate_data_per_streak(email, export_name, unique_time):
    filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
    create_csv(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:

        append_to_csv(('streak_type', 'total_streaks_by_all_users', 'total_users_who_have_earned_a_streak',
                       'total_users_reached_weekly_savings_amount', 'total_users_not_reached_weekly_savings_amount'),
                      csvfile)

        total_streaks_all_users = get_total_streaks_all_users()
        num_users_min_one_streak = get_total_users_earned_streak()
        total_weekly_target_weeks = get_total_users_reached_weekly_savings_for_weeks()
        total_not_weekly_target_weeks = get_total_users_not_reached_weekly_savings_for_weeks()

        for i in range(1, 7):
            week = ''
            if i % 2 == 0:
                if i == 2:
                    week = '2 weeks'
                if i == 4:
                    week = '4 weeks'
                if i == 6:
                    week = '6 weeks'

                data = [
                    week,
                    total_streaks_all_users[int_to_str(i)],
                    num_users_min_one_streak[int_to_str(i)],
                    total_weekly_target_weeks[int_to_str(i)],
                    total_not_weekly_target_weeks[int_to_str(i)]
                ]

                append_to_csv(data, csvfile)

    pass_zip_encrypt_email(email, export_name, unique_time)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


def int_to_str(num):
    """Helper method to convert week streak number to word for accesing dicts"""
    if num == 2:
        return 'two'
    if num == 4:
        return 'four'
    if num == 6:
        return 'six'


def get_total_streaks_all_users():
    """Get the total number of 2, 4, 6 week saving streaks for up to 6 weeks in a row"""
    streak_weeks = {
        'two': 0,
        'four': 0,
        'six': 0
    }

    # Iterate through all goals, checking for 2, 4, 6 week streaks
    # Note: A 6 week streak must not also count as 3 two week streaks
    goals = Goal.objects.all()
    for goal in goals:
        goal_weekly_agg = goal.get_weekly_aggregates()
        streak = 0

        for week in range(0, len(goal_weekly_agg)):
            if goal_weekly_agg[week] != 0:
                streak += 1
                if (week + 1) < len(goal_weekly_agg):
                    # If the streak doesn't continue, count it then reset streak
                    if goal_weekly_agg[week + 1] == 0:
                        if streak == 2 or streak == 3:
                            streak_weeks['two'] += 1
                        if streak == 4 or streak == 5:
                            streak_weeks['four'] += 1
                        if streak >= 6:
                            streak_weeks['six'] += 1

                        streak = 0

    return streak_weeks


def get_total_users_earned_streak():
    """Get the number of users with 2, 4, 6 week savings streaks for up to 6 weeks in a row"""
    streak_weeks = {
        'two': 0,
        'four': 0,
        'six': 0
    }

    # Iterate through all goals, checking for 2, 4, 6 week streaks
    # Note: A 6 week streak must not also count as 3 two week streaks
    users = User.objects.all()
    for user in users:
        user_2_week = 0
        user_4_week = 0
        user_6_week = 0

        goals = Goal.objects.filter(user=user)
        for goal in goals:
            goal_weekly_agg = goal.get_weekly_aggregates()
            streak = 0

            for week in range(0, len(goal_weekly_agg)):
                if goal_weekly_agg[week] != 0:
                    streak += 1
                    if (week + 1) < len(goal_weekly_agg):
                        # If the streak doesn't continue, count it then reset streak
                        if goal_weekly_agg[week + 1] == 0:
                            if (streak == 2 or streak == 3) and user_2_week == 0:
                                user_2_week = 1
                                streak_weeks['two'] += 1
                            if (streak == 4 or streak == 5) and user_4_week == 0:
                                user_4_week = 1
                                streak_weeks['four'] += 1
                            if streak >= 6 and user_6_week == 0:
                                user_6_week = 1
                                streak_weeks['six'] += 1

                            streak = 0

    return streak_weeks


def get_total_users_reached_weekly_savings_for_weeks():
    """Get the total number of streaks for up to 6 weeks in a row"""
    streak_weeks = {
        'two': 0,
        'four': 0,
        'six': 0
    }

    # Iterate through all goals, checking for 2, 4, 6 week streaks
    # Note: A 6 week streak must not also count as 3 two week streaks
    users = User.objects.all()
    for user in users:
        user_2_week = 0
        user_4_week = 0
        user_6_week = 0

        goals = Goal.objects.filter(user=user)
        for goal in goals:
            goal_weekly_agg = goal.get_weekly_aggregates()
            streak = 0

            for week in range(0, len(goal_weekly_agg)):
                if goal_weekly_agg[week] >= goal.weekly_target:
                    streak += 1
                    if (week + 1) < len(goal_weekly_agg):
                        # If the streak doesn't continue, count it then reset streak
                        if goal_weekly_agg[week + 1] == 0:
                            if (streak == 2 or streak == 3) and user_2_week == 0:
                                user_2_week = 1
                                streak_weeks['two'] += 1
                            if (streak == 4 or streak == 5) and user_4_week == 0:
                                user_4_week = 1
                                streak_weeks['four'] += 1
                            if streak >= 6 and user_6_week == 0:
                                user_6_week = 1
                                streak_weeks['six'] += 1

                            streak = 0

    return streak_weeks


def get_total_users_not_reached_weekly_savings_for_weeks():
    """Get the total number of streaks for up to 6 weeks in a row"""
    streak_weeks = {
        'two': 0,
        'four': 0,
        'six': 0
    }

    # Iterate through all goals, checking for 2, 4, 6 week streaks
    # Note: A 6 week streak must not also count as 3 two week streaks
    users = User.objects.all()
    for user in users:
        user_2_week = 0
        user_4_week = 0
        user_6_week = 0

        goals = Goal.objects.filter(user=user)
        for goal in goals:
            goal_weekly_agg = goal.get_weekly_aggregates()
            streak = 0

            for week in range(0, len(goal_weekly_agg)):
                if goal_weekly_agg[week] < goal.weekly_target:
                    streak += 1
                    if (week + 1) < len(goal_weekly_agg):
                        # If the streak doesn't continue, count it then reset streak
                        if goal_weekly_agg[week + 1] == 0:
                            if (streak == 2 or streak == 3) and user_2_week == 0:
                                user_2_week = 1
                                streak_weeks['two'] += 1
                            if (streak == 4 or streak == 5) and user_4_week == 0:
                                user_4_week = 1
                                streak_weeks['four'] += 1
                            if streak >= 6 and user_6_week == 0:
                                user_6_week = 1
                                streak_weeks['six'] += 1

                            streak = 0

    return streak_weeks


@task(name="export_aggregate_user_type")
def export_aggregate_user_type(email, export_name, unique_time):

    filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
    create_csv(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        append_to_csv(('username', 'name', 'email', 'mobile', 'gender', 'age', 'date_joined',
                       'campaign', 'source', 'medium'),
                      csvfile)

        users = User.objects.filter(is_staff=False, user__is_active=True)

        for user in users:
            campaign_info = CampaignInformation.objects.filter(user=user).first()
            profile = Profile.objects.get(user=user)

            data = [
                user.username,
                user.get_full_name(),
                user.email,
                profile.mobile,
                'M' if profile.gender == Profile.GENDER_MALE else 'F',
                profile.age,
                user.date_joined,
            ]

            if campaign_info is None:
                data.append('')  # Campaign
                data.append('')  # Source
                data.append('')  # Medium
            else:
                data.append(campaign_info.campaign)
                data.append(campaign_info.source)
                data.append(campaign_info.medium)

            append_to_csv(data, csvfile)

    pass_zip_encrypt_email(email, export_name, unique_time)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


##################
# Survey Exports #
##################

@task(name="export_survey_summary")
def export_survey_summary(email, export_name, unique_time):

    filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
    create_csv(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        append_to_csv(('survey_name', 'total_users_completed', 'total_users_in_progress', 'total_users_no_consent',
                       'total_users_claim_over_17', 'total_no_engagement', 'total_no_first_conversation'),
                      csvfile)

        # Baseline Survey

        num_completed_users = CoachSurveySubmission.objects.filter(
            user__is_staff=False,
            user__is_active=True,
            survey__bot_conversation=CoachSurvey.BASELINE).count()

        num_in_progress_users = CoachSurveySubmissionDraft.objects.filter(
            user__is_staff=False,
            user__is_active=True,
            survey__bot_conversation=CoachSurvey.BASELINE,
            complete=False).count()

        num_first_convo_no = 0
        num_no_consent = 0
        num_claim_over_17_users = 0

        submitted_survey_drafts = CoachSurveySubmissionDraft.objects.filter(
            user__is_staff=False,
            user__is_active=True,
            survey__bot_conversation=CoachSurvey.BASELINE,
            consent=False)

        # Counts number of first conversation no responses, others checks to see if they have no consent
        for survey in submitted_survey_drafts:
            if survey.has_submission:
                submission_data = json.loads(survey.submission_data)
                try:
                    if submission_data['survey_baseline_intro'] == '0':
                        num_first_convo_no += 1
                    elif survey.consent is False:
                        num_no_consent += 1
                except KeyError:
                    pass

        submitted_surveys = CoachSurveySubmission.objects.filter(
            user__is_staff=False,
            user__is_active=True,
            survey__bot_conversation=CoachSurvey.BASELINE)

        for survey in submitted_surveys:
            survey_data = survey.get_data()
            try:
                if survey_data['survey_baseline_q1_consent'] == 1:
                    num_claim_over_17_users += 1
            except KeyError:
                pass

        num_total_users = User.objects.filter(is_staff=False).count()
        num_participated_survey = CoachSurveySubmission.objects\
            .filter(user__is_staff=False, user__is_active=True, survey__bot_conversation=CoachSurvey.BASELINE)\
            .values('user')\
            .distinct()\
            .count()

        num_no_engagement = num_total_users - num_participated_survey - num_first_convo_no

        data = [
            'Baseline Survey',
            num_completed_users,
            num_in_progress_users,
            num_no_consent,
            num_claim_over_17_users,
            num_no_engagement,
            num_first_convo_no
        ]
        append_to_csv(data, csvfile)

        # Ea Tool 1 Survey

        num_completed_users = CoachSurveySubmission.objects.filter(
            user__is_staff=False,
            user__is_active=True,
            survey__bot_conversation=CoachSurvey.EATOOL).count()

        num_in_progress_users = CoachSurveySubmissionDraft.objects.filter(
            user__is_staff=False,
            user__is_active=True,
            survey__bot_conversation=CoachSurvey.EATOOL,
            complete=False).count()

        num_first_convo_no = 0
        num_no_consent = 0
        num_claim_over_17_users = 0

        submitted_survey_drafts = CoachSurveySubmissionDraft.objects.filter(
            user__is_staff=False,
            user__is_active=True,
            survey__bot_conversation=CoachSurvey.EATOOL,
            consent=False)

        # Counts number of first conversation no responses, others checks to see if they have no consent
        for survey in submitted_survey_drafts:
            if survey.has_submission:
                submission_data = json.loads(survey.submission_data)
                try:
                    if submission_data['survey_eatool_intro'] == '0':
                        num_first_convo_no += 1
                    elif survey.consent is False:
                        num_no_consent += 1
                except KeyError:
                    pass

        submitted_surveys = CoachSurveySubmission.objects.filter(
            user__is_staff=False,
            user__is_active=True,
            survey__bot_conversation=CoachSurvey.EATOOL)

        for survey in submitted_surveys:
            survey_data = survey.get_data()
            try:
                if survey_data['survey_eatool_q1_consent'] == 1:
                    num_claim_over_17_users += 1
            except KeyError:
                pass

        num_total_users = User.objects.filter(is_staff=False).count()
        num_participated_survey = CoachSurveySubmissionDraft.objects \
            .filter(user__is_staff=False, user__is_active=True, survey__bot_conversation=CoachSurvey.EATOOL) \
            .values('user') \
            .distinct() \
            .count()

        num_no_engagement = num_total_users - num_participated_survey - num_first_convo_no

        data = [
            'EA Tool 1 Survey',
            num_completed_users,
            num_in_progress_users,
            num_no_consent,
            num_claim_over_17_users,
            num_no_engagement,
            num_first_convo_no
        ]
        append_to_csv(data, csvfile)

        # EA Tool 2 Survey

        data = [
            'EA Tool 2 Survey',

        ]
        append_to_csv(data, csvfile)

        # Endline Survey

        data = [
            'Endline Survey',

        ]
        append_to_csv(data, csvfile)

    pass_zip_encrypt_email(email, export_name, unique_time)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


@task(name="export_baseline_survey")
def export_baseline_survey(email, export_name, unique_time):
    surveys = CoachSurvey.objects.filter(bot_conversation=CoachSurvey.BASELINE)

    filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
    create_csv(filename)

    # 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 999
    q01_answers = {
        1: '"Student in elementary school (SD)"',
        2: '"Student in middle school (SMP)"',
        3: '"Student in academic high school (SMA)"',
        4: '"Student in vocational high school (SMK)"',
        5: '"Student in college or above"',
        6: '"Employee working in a job"',
        7: '"Business owner or co-owner"',
        8: '"Volunteer in church or community"',
        9: '"Care giver of family members or children"',
        10: '"Not working, studying, or volunteering"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 999
    q02_answers = {
        1: '"1st Year"',
        2: '"2nd Year"',
        3: '"3rd Year"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q05_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 4, 5, 6, 999
    q06_answers = {
        1: '"Less than 250 thousand"',
        2: '"Between 250 thousand and 500 thousand"',
        3: '"Between 500 thousand and 750 thousand"',
        4: '"Between 750 thousand and 1 million"',
        5: '"Between 1 million and 1,5 million"',
        6: '"More than 1,5 million"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 4, 5, 6, 888, 999
    q07_answers = {
        1: '"Permanent staff (signed contract with specific salary and benefits)"',
        2: '"Indefinite term employment (probation, pathway to permanent staff)"',
        3: '"Temporary/casual (working on short assignments or task, no contract)"',
        4: '"Apprenticeship (learning new skill and receiving small monetary support to cover transport cost)"',
        5: '"Daily worker (working on a day to day basis)"',
        6: '"Helping family business with pay"',
        7: '"Does not know"',
        888: '888',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q08_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 4, 5, 6, 999
    q09_answers = {
        1: '"Less than 250 thousand"',
        2: '"Between 250 thousand and 500 thousand"',
        3: '"Between 500 thousand and 750 thousand"',
        4: '"Between 750 thousand and 1 million"',
        5: '"Between 1 million and 1,5 million"',
        6: '"More than 1,5 million"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q10_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 4, 5, 6, 7, 8, 999
    q11_answers = {
        1: '"Daily"',
        2: '"Weekly"',
        3: '"Monthly"',
        4: '"Every 2 months"',
        5: '"Every 3 or 4 months"',
        6: '"Once or twice a year"',
        7: '"Do not remember"',
        8: '"Varies (different times, not a set frequency)"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 4, 5, 6, 999
    q12_answers = {
        1: '"Bank"',
        2: '"Community savings group"',
        3: '"At home (chicken bank)"',
        4: '"Send to family for safekeeping"',
        5: '"Buy gold or other valuables"',
        6: '"Other"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 4, 5, 6, 7, 8, 999
    q13_answers = {
        1: '"Less than 100 thousand"',
        2: '"Between 100 thousand and 150 thousand"',
        3: '"Between 150 thousand and 200 thousand"',
        4: '"Between 200 thousand and 250 thousand"',
        5: '"Between 250 thousand and 300 thousand"',
        6: '"Between 300 thousand and 350 thousand"',
        7: '"Between 350 thousand and 400 thousand"',
        8: '"More than 400 thousand"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q14_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q15_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q16_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q17_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q18_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q19_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q20_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q21_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q22_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 4, 5, 999
    q23_answers = {
        1: '"Never"',
        2: '"Once a month"',
        3: '"Once a week"',
        4: '"Once a day"',
        5: '"Multiple times per day"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 4, 5, 6, 999
    q24_answers = {
        1: '"Calling or texting friends"',
        2: '"Calling or texting family"',
        3: '"Accessing social media"',
        4: '"Accessing information on the internet"',
        5: '"Using apps or tools to help me manage my life, like trackers or calendars."',
        6: '"Other"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 4, 5, 6, 999
    q25_answers = {
        1: '"Calling or texting friends"',
        2: '"Calling or texting family"',
        3: '"Accessing social media"',
        4: '"Accessing information on the internet"',
        5: '"Using apps or tools to help me manage my life, like trackers or calendars."',
        6: '"Other"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 4, 5, 6, 999
    q26_answers = {
        1: '"You"',
        2: '"Mother"',
        3: '"Father"',
        4: '"Sibling"',
        5: '"Another relative"',
        6: '"Someone else"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 999
    q27_1_answers = {
        1: '"Approve"',
        2: '"Neutral"',
        3: '"Disapprove"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 999
    q27_2_answers = {
        1: '"Approve"',
        2: '"Neutral"',
        3: '"Disapprove"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 999
    q27_3_answers = {
        1: '"Approve"',
        2: '"Neutral"',
        3: '"Disapprove"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 4, 5, 6, 999
    q28_answers = {
        1: '"Less than 5 thousand rupiah"',
        2: '"Between 5 thousand and 15 thousand rupiah"',
        3: '"Between 15 thousand and 25 thousand rupiah"',
        4: '"Between 25 thousand and 35 thousand rupiah"',
        5: '"Between 35 thousand and 45 thousand rupiah"',
        6: '"More than 45 thousand rupiah"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q29_1_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q29_2_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q29_3_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q29_4_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        append_to_csv(('uuid', 'username', 'name', 'mobile', 'email', 'gender', 'age',
                       'user_type_source_medium', 'date_joined', 'city', 'younger_than_17', 'consent_given',
                       'submission_date',

                       # Survey questions
                       'q1_WhatIsYourOccupation',
                       'q2_WhatGradeAreYouIn',
                       'q3_WhatIsTheNameOfYourSMK',
                       'q4_WhatCityDoYouLiveIn',
                       'q5_HaveYouEverHadAPaidJobForLongerThanOneMonthIncludeWorkingInFamilyBusinessAndOrApprenticeshipsIfPaid',
                       'q6_WithinWhatRangeDIdYourMonthlyEarningFallForYourLastJob',
                       'q7_WhatWasYourEmploymentStatusInYourLastJob',
                       'q8_HaveYouEverOwnedOrSharedOwnershipOfABusiness',
                       'q9_WithinWhatRangeDidYourMonthlyBusinessEarningsFall',
                       'q10_DoYouEverSaveSomeOfYourMoney',
                       'q11_HowFrequentlyDoYouSaveMoney',
                       'q12_WhereDoYouKeepMostOfYourSavings',
                       'q13_InTheLast3MonthsApproximatelyHowMuchMoneyDidYouSaveInTotal',
                       'q14_HaveYouEverSavedMoneyToPayForEducationCostsLikeFeesForATrainingCourse',
                       'q15_HaveYouEverSavedMOneyToPayForTheCostOfLookingForAJobOrAttendingJobInterviews',
                       'q16_HaveYouEverSavedMoneyToHaveSomeExtraInCaseOfEmergencies',
                       'q17_HaveYouEverSavedMoneyToInvestInBusinessOpportunities',
                       'q18_HaveYouEverSavedMoneyToSupportFamilyNeeds',
                       'q19_HaveYouEverSavedMoneyToBuyPersonalItemsForEverydayUseLikeClothesOrFood',
                       'q20_HaveYouEverSavedMoneyToBuyPersonalItemsForEverydayUseLikeClothesOrFood',
                       'q21_HaveYouEverSavedMoneyToBuyItemsThatLastLongerLikeAPhoneComputerOrMotorbike',
                       'q22_HaveYouEverSavedMoneyToGoOutWithFriendsForFun', 'q23_HowOftenDoYouUseAMobilePhone',
                       'q24_WhatIsYourMobilePhoneMostUsefulFor',
                       'q25_WhatIsYourMobilePhoneLeastUsefulFor',
                       'q26_WhoOwnsTheMobilePhoneThatYouUse',
                       'q27_1_HereAreSOmePeopleYouMightInteractWithPleaseTellMeIfYouThinkTheyApproveDisapproveOrAreNeutralTowardYouOrYourFriendsUsingMobilePhones',
                       'q27_2',
                       'q27_3',
                       'q28_HowMuchCreditDoYouOrYourFamilyPutIntoYourMobilePhoneOnATypicalWeek',
                       'q29_1_DoYouHaveTheFollowingAssetsInYourHome',
                       'q29_2',
                       'q29_3',
                       'q29_4'),
                      csvfile)

        for survey in surveys:
            # All baseline survey submissions that are complete
            submissions = CoachSurveySubmission.objects.filter(user__is_staff=False,
                                                               user__is_active=True,
                                                               survey=survey)

            for submission in submissions:
                try:
                    campaign_info = CampaignInformation.objects.get(user=submission.user)
                    user_type = campaign_info.source + '/' + campaign_info.medium
                except:
                    user_type = ''
                survey_data = submission.get_data()

                data = [
                    submission.user_unique_id,
                    submission.username,
                    submission.name,
                    submission.mobile,
                    submission.email,
                    submission.gender,
                    submission.age,
                    user_type,  # user type
                    submission.user.date_joined,
                    survey_data['survey_baseline_q04_city'],
                    survey_data['survey_baseline_q1_consent'],
                    submission.consent,  # survey_data['survey_baseline_q2_consent']
                    submission.created_at,

                    # survey questions
                    q01_answers[int(survey_data['survey_baseline_q01_occupation'])],
                    q02_answers[int(survey_data['survey_baseline_q02_grade'])],
                    survey_data['survey_baseline_q03_school_name'],
                    survey_data['survey_baseline_q04_city'],
                    q05_answers[int(survey_data['survey_baseline_q05_job_month'])],
                    q06_answers[int(survey_data['survey_baseline_q06_job_earning_range'])],
                    q07_answers[int(survey_data['survey_baseline_q07_job_status'])],
                    q08_answers[int(survey_data['survey_baseline_q08_shared_ownership'])],
                    q09_answers[int(survey_data['survey_baseline_q09_business_earning_range'])],
                    q10_answers[int(survey_data['survey_baseline_q10_save'])],
                    q11_answers[int(survey_data['survey_baseline_q11_savings_frequency'])],
                    q12_answers[int(survey_data['survey_baseline_q12_savings_where'])],
                    q13_answers[int(survey_data['survey_baseline_q13_savings_3_months'])],
                    q14_answers[int(survey_data['survey_baseline_q14_saving_education'])],
                    q15_answers[int(survey_data['survey_baseline_q15_job_hunt'])],
                    q16_answers[int(survey_data['survey_baseline_q16_emergencies'])],
                    q17_answers[int(survey_data['survey_baseline_q17_invest'])],
                    q18_answers[int(survey_data['survey_baseline_q18_family'])],
                    q19_answers[int(survey_data['survey_baseline_q19_clothes_food'])],
                    '',  # Missing q20
                    q21_answers[int(survey_data['survey_baseline_q21_gadgets'])],
                    q22_answers[int(survey_data['survey_baseline_q22_friends'])],
                    q23_answers[int(survey_data['survey_baseline_q23_mobile_frequency'])],
                    q24_answers[int(survey_data['survey_baseline_q24_mobile_most_use'])],
                    q25_answers[int(survey_data['survey_baseline_q25_mobile_least_use'])],
                    q26_answers[int(survey_data['survey_baseline_q26_mobile_own'])],
                    q27_1_answers[int(survey_data['survey_baseline_q27_1_friends'])],
                    q27_2_answers[int(survey_data['survey_baseline_q27_2_family'])],
                    q27_3_answers[int(survey_data['survey_baseline_q27_3_community'])],
                    q28_answers[int(survey_data['survey_baseline_q28_mobile_credit'])],
                    q29_1_answers[int(survey_data['survey_baseline_q29_1_desktop'])],
                    q29_2_answers[int(survey_data['survey_baseline_q29_2_laptop'])],
                    q29_3_answers[int(survey_data['survey_baseline_q29_3_mobile_no_data'])],
                    q29_4_answers[int(survey_data['survey_baseline_q29_4_mobile_data'])]
                ]

                append_to_csv(data, csvfile)

    pass_zip_encrypt_email(email, export_name, unique_time)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


@task(name="export_endline_survey")
def export_endline_survey(email, export_name, unique_time):
    surveys = CoachSurvey.objects.filter(bot_conversation=CoachSurvey.ENDLINE)

    filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
    create_csv(filename)

    # 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 999
    q01_answers = {
        1: '"Student in elementary school (SD)"',
        2: '"Student in middle school (SMP)"',
        3: '"Student in academic high school (SMA)"',
        4: '"Student in vocational high school (SMK)"',
        5: '"Student in college or above"',
        6: '"Employee working in a job"',
        7: '"Business owner or co-owner"',
        8: '"Volunteer in church or community"',
        9: '"Care giver of family members or children"',
        10: '"Not working, studying, or volunteering"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 999
    q02_answers = {
        1: '"1st Year"',
        2: '"2nd Year"',
        3: '"3rd Year"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q05_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 4, 5, 6, 999
    q06_answers = {
        1: '"Less than 250 thousand"',
        2: '"Between 250 thousand and 500 thousand"',
        3: '"Between 500 thousand and 750 thousand"',
        4: '"Between 750 thousand and 1 million"',
        5: '"Between 1 million and 1,5 million"',
        6: '"More than 1,5 million"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 4, 5, 6, 888, 999
    q07_answers = {
        1: '"Permanent staff (signed contract with specific salary and benefits)"',
        2: '"Indefinite term employment (probation, pathway to permanent staff)"',
        3: '"Temporary/casual (working on short assignments or task, no contract)"',
        4: '"Apprenticeship (learning new skill and receiving small monetary support to cover transport cost)"',
        5: '"Daily worker (working on a day to day basis)"',
        6: '"Helping family business with pay"',
        7: '"Does not know"',
        888: '888',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q08_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 4, 5, 6, 999
    q09_answers = {
        1: '"Less than 250 thousand"',
        2: '"Between 250 thousand and 500 thousand"',
        3: '"Between 500 thousand and 750 thousand"',
        4: '"Between 750 thousand and 1 million"',
        5: '"Between 1 million and 1,5 million"',
        6: '"More than 1,5 million"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q10_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 4, 5, 6, 7, 8, 999
    q11_answers = {
        1: '"Daily"',
        2: '"Weekly"',
        3: '"Monthly"',
        4: '"Every 2 months"',
        5: '"Every 3 or 4 months"',
        6: '"Once or twice a year"',
        7: '"Do not remember"',
        8: '"Varies (different times, not a set frequency)"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 4, 5, 6, 999
    q12_answers = {
        1: '"Bank"',
        2: '"Community savings group"',
        3: '"At home (chicken bank)"',
        4: '"Send to family for safekeeping"',
        5: '"Buy gold or other valuables"',
        6: '"Other"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 4, 5, 6, 7, 8, 999
    q13_answers = {
        1: '"Less than 100 thousand"',
        2: '"Between 100 thousand and 150 thousand"',
        3: '"Between 150 thousand and 200 thousand"',
        4: '"Between 200 thousand and 250 thousand"',
        5: '"Between 250 thousand and 300 thousand"',
        6: '"Between 300 thousand and 350 thousand"',
        7: '"Between 350 thousand and 400 thousand"',
        8: '"More than 400 thousand"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q14_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q15_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q16_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q17_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q18_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q19_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q20_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q21_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q22_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 4, 5, 999
    q23_answers = {
        1: '"Never"',
        2: '"Once a month"',
        3: '"Once a week"',
        4: '"Once a day"',
        5: '"Multiple times per day"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 4, 5, 6, 999
    q24_answers = {
        1: '"Calling or texting friends"',
        2: '"Calling or texting family"',
        3: '"Accessing social media"',
        4: '"Accessing information on the internet"',
        5: '"Using apps or tools to help me manage my life, like trackers or calendars."',
        6: '"Other"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 4, 5, 6, 999
    q25_answers = {
        1: '"Calling or texting friends"',
        2: '"Calling or texting family"',
        3: '"Accessing social media"',
        4: '"Accessing information on the internet"',
        5: '"Using apps or tools to help me manage my life, like trackers or calendars."',
        6: '"Other"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 4, 5, 6, 999
    q26_answers = {
        1: '"You"',
        2: '"Mother"',
        3: '"Father"',
        4: '"Sibling"',
        5: '"Another relative"',
        6: '"Someone else"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 999
    q27_1_answers = {
        1: '"Approve"',
        2: '"Neutral"',
        3: '"Disapprove"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 999
    q27_2_answers = {
        1: '"Approve"',
        2: '"Neutral"',
        3: '"Disapprove"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 999
    q27_3_answers = {
        1: '"Approve"',
        2: '"Neutral"',
        3: '"Disapprove"',
        998: '998',
        999: '999',
    }

    # 1, 2, 3, 4, 5, 6, 999
    q28_answers = {
        1: '"Less than 5 thousand rupiah"',
        2: '"Between 5 thousand and 15 thousand rupiah"',
        3: '"Between 15 thousand and 25 thousand rupiah"',
        4: '"Between 25 thousand and 35 thousand rupiah"',
        5: '"Between 35 thousand and 45 thousand rupiah"',
        6: '"More than 45 thousand rupiah"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q29_1_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q29_2_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q29_3_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    # 1y, 0n, 999
    q29_4_answers = {
        0: '"No"',
        1: '"Yes"',
        998: '998',
        999: '999',
    }

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        append_to_csv(('uuid', 'username', 'name', 'mobile', 'email', 'gender', 'age',
                       'user_type_source_medium', 'date_joined', 'city', 'younger_than_17', 'consent_given',
                       'submission_date',

                       # Survey questions
                       'q1_WhatIsYourOccupation',
                       'q2_WhatGradeAreYouIn',
                       'q3_WhatIsTheNameOfYourSMK',
                       'q4_WhatCityDoYouLiveIn',
                       'q5_HaveYouEverHadAPaidJobForLongerThanOneMonthIncludeWorkingInFamilyBusinessAndOrApprenticeshipsIfPaid',
                       'q6_WithinWhatRangeDIdYourMonthlyEarningFallForYourLastJob',
                       'q7_WhatWasYourEmploymentStatusInYourLastJob',
                       'q8_HaveYouEverOwnedOrSharedOwnershipOfABusiness',
                       'q9_WithinWhatRangeDidYourMonthlyBusinessEarningsFall',
                       'q10_DoYouEverSaveSomeOfYourMoney',
                       'q11_HowFrequentlyDoYouSaveMoney',
                       'q12_WhereDoYouKeepMostOfYourSavings',
                       'q13_InTheLast3MonthsApproximatelyHowMuchMoneyDidYouSaveInTotal',
                       'q14_HaveYouEverSavedMoneyToPayForEducationCostsLikeFeesForATrainingCourse',
                       'q15_HaveYouEverSavedMOneyToPayForTheCostOfLookingForAJobOrAttendingJobInterviews',
                       'q16_HaveYouEverSavedMoneyToHaveSomeExtraInCaseOfEmergencies',
                       'q17_HaveYouEverSavedMoneyToInvestInBusinessOpportunities',
                       'q18_HaveYouEverSavedMoneyToSupportFamilyNeeds',
                       'q19_HaveYouEverSavedMoneyToBuyPersonalItemsForEverydayUseLikeClothesOrFood',
                       'q20_HaveYouEverSavedMoneyToBuyPersonalItemsForEverydayUseLikeClothesOrFood',
                       'q21_HaveYouEverSavedMoneyToBuyItemsThatLastLongerLikeAPhoneComputerOrMotorbike',
                       'q22_HaveYouEverSavedMoneyToGoOutWithFriendsForFun', 'q23_HowOftenDoYouUseAMobilePhone',
                       'q24_WhatIsYourMobilePhoneMostUsefulFor',
                       'q25_WhatIsYourMobilePhoneLeastUsefulFor',
                       'q26_WhoOwnsTheMobilePhoneThatYouUse',
                       'q27_1_HereAreSOmePeopleYouMightInteractWithPleaseTellMeIfYouThinkTheyApproveDisapproveOrAreNeutralTowardYouOrYourFriendsUsingMobilePhones',
                       'q27_2',
                       'q27_3',
                       'q28_HowMuchCreditDoYouOrYourFamilyPutIntoYourMobilePhoneOnATypicalWeek',
                       'q29_1_DoYouHaveTheFollowingAssetsInYourHome',
                       'q29_2',
                       'q29_3',
                       'q29_4'),
                      csvfile)

        for survey in surveys:
            # All baseline survey submissions that are complete
            submissions = CoachSurveySubmission.objects.filter(user__is_staff=False,
                                                               user__is_active=True,
                                                               survey=survey)

            for submission in submissions:
                try:
                    campaign_info = CampaignInformation.objects.get(user=submission.user)
                    user_type = campaign_info.source + '/' + campaign_info.medium
                except:
                    user_type = ''
                survey_data = submission.get_data()

                data = [
                    submission.user_unique_id,
                    submission.username,
                    submission.name,
                    submission.mobile,
                    submission.email,
                    submission.gender,
                    submission.age,
                    user_type,  # user type
                    submission.user.date_joined,
                    survey_data['survey_endline_q04_city'],
                    survey_data['survey_endline_q1_consent'],
                    submission.consent,  # survey_data['survey_endline_q2_consent']
                    submission.created_at,

                    # survey questions
                    q01_answers[int(survey_data['survey_endline_q01_occupation'])],
                    q02_answers[int(survey_data['survey_endline_q02_grade'])],
                    survey_data['survey_endline_q03_school_name'],
                    survey_data['survey_endline_q04_city'],
                    q05_answers[int(survey_data['survey_endline_q05_job_month'])],
                    q06_answers[int(survey_data['survey_endline_q06_job_earning_range'])],
                    q07_answers[int(survey_data['survey_endline_q07_job_status'])],
                    q08_answers[int(survey_data['survey_endline_q08_shared_ownership'])],
                    q09_answers[int(survey_data['survey_endline_q09_business_earning_range'])],
                    q10_answers[int(survey_data['survey_endline_q10_save'])],
                    q11_answers[int(survey_data['survey_endline_q11_savings_frequency'])],
                    q12_answers[int(survey_data['survey_endline_q12_savings_where'])],
                    q13_answers[int(survey_data['survey_endline_q13_savings_3_months'])],
                    q14_answers[int(survey_data['survey_endline_q14_saving_education'])],
                    q15_answers[int(survey_data['survey_endline_q15_job_hunt'])],
                    q16_answers[int(survey_data['survey_endline_q16_emergencies'])],
                    q17_answers[int(survey_data['survey_endline_q17_invest'])],
                    q18_answers[int(survey_data['survey_endline_q18_family'])],
                    q19_answers[int(survey_data['survey_endline_q19_clothes_food'])],
                    '',  # Missing q20
                    q21_answers[int(survey_data['survey_endline_q21_gadgets'])],
                    q22_answers[int(survey_data['survey_endline_q22_friends'])],
                    q23_answers[int(survey_data['survey_endline_q23_mobile_frequency'])],
                    q24_answers[int(survey_data['survey_endline_q24_mobile_most_use'])],
                    q25_answers[int(survey_data['survey_endline_q25_mobile_least_use'])],
                    q26_answers[int(survey_data['survey_endline_q26_mobile_own'])],
                    q27_1_answers[int(survey_data['survey_endline_q27_1_friends'])],
                    q27_2_answers[int(survey_data['survey_endline_q27_2_family'])],
                    q27_3_answers[int(survey_data['survey_endline_q27_3_community'])],
                    q28_answers[int(survey_data['survey_endline_q28_mobile_credit'])],
                    q29_1_answers[int(survey_data['survey_endline_q29_1_desktop'])],
                    q29_2_answers[int(survey_data['survey_endline_q29_2_laptop'])],
                    q29_3_answers[int(survey_data['survey_endline_q29_3_mobile_no_data'])],
                    q29_4_answers[int(survey_data['survey_endline_q29_4_mobile_data'])]
                ]

                append_to_csv(data, csvfile)

    pass_zip_encrypt_email(email, export_name, unique_time)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


@task(name="export_ea1tool_survey")
def export_ea1tool_survey(email, export_name, unique_time):
    surveys = CoachSurvey.objects.filter(bot_conversation=CoachSurvey.EATOOL)

    filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
    create_csv(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        append_to_csv(('uuid', 'username', 'name', 'mobile', 'email', 'gender', 'age',
                       'user_type_source_medium', 'date_joined', 'city', 'younger_than_17', 'consent_given',
                       'submission_date',

                       # Survey questions
                       'q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8', 'q9', 'q10', 'q11', 'q12',
                       'q13', 'q14', 'q15', 'q16', 'q17', 'q18', 'q19', 'q20', 'q21', 'q22', 'q23', 'q24'
                       ),
                      csvfile)

        for survey in surveys:
            submissions = CoachSurveySubmission.objects.filter(user__is_staff=False,
                                                               user__is_active=True,
                                                               survey=survey)

            for submission in submissions:
                try:
                    campaign_info = CampaignInformation.objects.get(user=submission.user)
                    user_type = campaign_info.source + '/' + campaign_info.medium
                except:
                    user_type = ''
                survey_data = submission.get_data()

                data = [
                    submission.user_unique_id,
                    submission.username,
                    submission.name,
                    submission.mobile,
                    submission.email,
                    submission.gender,
                    submission.age,
                    user_type,  # user type
                    submission.user.date_joined,
                    '',  # City
                    survey_data['survey_eatool_q1_consent'],
                    submission.consent,  # survey_data['survey_eatool_q2_consent']
                    submission.created_at,

                    survey_data['survey_eatool_q01_appreciate'],
                    survey_data['survey_eatool_q02_optimistic'],
                    survey_data['survey_eatool_q03_career'],
                    survey_data['survey_eatool_q04_adapt'],
                    survey_data['survey_eatool_q05_duties'],
                    survey_data['survey_eatool_q06_lazy'],
                    survey_data['survey_eatool_q07_proud'],
                    survey_data['survey_eatool_q08_dress'],
                    survey_data['survey_eatool_q09_along'],
                    survey_data['survey_eatool_q10_anyone'],
                    survey_data['survey_eatool_q11_input'],
                    survey_data['survey_eatool_q12_responsible'],
                    survey_data['survey_eatool_q13_express'],
                    survey_data['survey_eatool_q14_understand'],
                    survey_data['survey_eatool_q15_read'],
                    survey_data['survey_eatool_q16_learn'],
                    survey_data['survey_eatool_q17_organise'],
                    survey_data['survey_eatool_q18_sources'],
                    survey_data['survey_eatool_q19_experience'],
                    survey_data['survey_eatool_q20_adapting'],
                    survey_data['survey_eatool_q21_interview'],
                    survey_data['survey_eatool_q22_cv'],
                    survey_data['survey_eatool_q23_cover'],
                    survey_data['survey_eatool_q24_company']
                ]

                append_to_csv(data, csvfile)

    pass_zip_encrypt_email(email, export_name, unique_time)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


@task(name="export_ea2tool_survey")
def export_ea2tool_survey(email, export_name, unique_time):
    # surveys = CoachSurvey.objects.filter(bot_conversation=CoachSurvey.EATOOL2)

    filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
    create_csv(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        append_to_csv(('uuid', 'username', 'name', 'mobile', 'email', 'gender', 'age',
                       'user_type_source_medium', 'date_joined', 'city', 'younger_than_17', 'consent_given',
                       'submission_date',

                       # Survey questions
                       ),
                      csvfile)

    pass_zip_encrypt_email(email, export_name, unique_time)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


#####################
# Budgeting Reports #
#####################


@task(name="export_budget_user")
def export_budget_user(email, export_name, unique_time):

    filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
    create_csv(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:

        append_to_csv(('user',
                       'budget_created',
                       'budget_created_date',
                       'budget_last_modified',
                       'budget_modified_count',
                       'budget_income_increased_count',
                       'budget_income_decreaed_count',
                       'budget_savings_increaed_count',
                       'budget_savings_decreaed_count',
                       'budget_expense_increased_count',
                       'budget_expense_decreased_count',
                       'budget_original_expense',
                       'budget_original_income',
                       'budget_original_savings',
                       'budget_current_expense',
                       'budget_current_income',
                       'budget_current_savings'),
                      csvfile)

        users = User.objects.filter(is_staff=False, is_active=True)

        for user in users:
            budget_exists = Budget.objects.filter(user=user).exists()

            if not budget_exists:
                data = [
                    user,
                    budget_exists,
                ]
            else:
                budget = Budget.objects.get(user=user)
                data = [
                    user,
                    budget_exists,
                    budget.created_on,
                    budget.modified_on,
                    budget.modified_count,
                    budget.income_increased_count,
                    budget.income_decreased_count,
                    budget.savings_increased_count,
                    budget.savings_decreased_count,
                    budget.expense_increased_count,
                    budget.expense_decreased_count,
                    budget.original_expense,
                    budget.original_income,
                    budget.original_savings,
                    budget.expense,
                    budget.income,
                    budget.savings
                ]

            append_to_csv(data, csvfile)

    pass_zip_encrypt_email(email, export_name, unique_time)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


@task(name="export_budget_expense_category")
def export_budget_expense_category(email, export_name, unique_time):

    filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
    create_csv(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        append_to_csv(('expense_category', 'total_users'),
                      csvfile)

        expense_categories = ExpenseCategory.objects.all()
        for expense_category in expense_categories:
            num_expense_category = Expense.objects.filter(category=expense_category).count()
            data = [
                expense_category.name,
                num_expense_category
            ]

            append_to_csv(data, csvfile)

    pass_zip_encrypt_email(email, export_name, unique_time)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


@task(name="export_budget_aggregate")
def export_budget_aggregate(email, export_name, unique_time):

    filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
    create_csv(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        append_to_csv(('total_budgets_created', 'num_users_budget_edited',
                       'num_budget_income_increased', 'num_budget_income_decreased',
                       'num_budget_savings_increased', 'num_budget_savings_decreased',
                       'num_budget_expense_increased', 'num_budget_savings_decreased',
                       ),
                      csvfile)

        budgets = Budget.objects.filter(user__is_staff=False, user__is_active=True)

        num_users_edited = Budget.objects.all().exclude(user__is_staff=False,
                                                        user__is_active=True,
                                                        modified_count=0).count()
        num_budget_income_increased = Budget.objects.all().exclude(user__is_staff=False,
                                                                   user__is_active=True,
                                                                   income_increased_count=0).count()
        num_budget_income_decreased = Budget.objects.all().exclude(user__is_staff=False,
                                                                   user__is_active=True,
                                                                   income_decreased_count=0).count()
        num_budget_savings_increased = Budget.objects.all().exclude(user__is_staff=False,
                                                                    user__is_active=True,
                                                                    savings_increased_count=0).count()
        num_budget_savings_decreased = Budget.objects.all().exclude(user__is_staff=False,
                                                                    user__is_active=True,
                                                                    savings_decreased_count=0).count()
        num_budget_expense_increased = Budget.objects.all().exclude(user__is_staff=False,
                                                                    user__is_active=True,
                                                                    expense_increased_count=0).count()
        num_budget_expense_decreased = Budget.objects.all().exclude(user__is_staff=False,
                                                                    user__is_active=True,
                                                                    expense_decreased_count=0).count()

        data = [
            budgets.count(),
            num_users_edited,
            num_budget_income_increased,
            num_budget_income_decreased,
            num_budget_savings_increased,
            num_budget_savings_decreased,
            num_budget_expense_increased,
            num_budget_expense_decreased
        ]

        append_to_csv(data, csvfile)

    pass_zip_encrypt_email(email, export_name, unique_time)

    return True, SUCCESS_MESSAGE_EMAIL_SENT
