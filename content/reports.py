import json

from django.contrib.auth.models import User
from django.db.models import Count
from django.conf import settings
from django.utils.translation import ugettext as _

from content.utilities import zip_and_encrypt, append_to_csv, create_csv, password_generator, send_password_email
from survey.models import CoachSurveySubmission, CoachSurvey, CoachSurveySubmissionDraft
from users.models import Profile
from .models import Goal, Badge, UserBadge, GoalTransaction, Challenge, Participant, QuizQuestion, QuestionOption, \
    ParticipantAnswer, ParticipantFreeText, GoalPrototype


SUCCESS_MESSAGE_EMAIL_SENT = _('Password has been sent in an email.')
ERROR_MESSAGE_NO_EMAIL = _('No email address associated with this account.')
ERROR_MESSAGE_DATA_CLEANUP = _('Report generation ran during data cleanup - try again')

STORAGE_DIRECTORY = settings.SENDFILE_ROOT + '\\'


def pass_zip_encrypt_email(request, export_name, unique_time):
    """Generate a password, zip and encrypt the report, if nothing goes wrong email the password"""

    password = password_generator()
    result, err_message = zip_and_encrypt(export_name, unique_time, password)

    if not result:
        return False, err_message

    if request.user.email is None or request.user.email is '':
        return False, ERROR_MESSAGE_NO_EMAIL

    send_password_email(request, export_name, unique_time, password)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


#####################
# Goal Data Reports #
#####################


class GoalReport:

    fields = ()

    @classmethod
    def export_csv(cls, request, stream, export_name, unique_time):
        goals = Goal.objects.all()

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
                    cls.get_username(goal),
                    '',  # TODO: Goal prototype in Bahasa (Not implemented)
                    goal.prototype,
                    goal.name,
                    goal.target,
                    goal.value,
                    goal.progress,
                    goal.weekly_target,
                    goal.weeks,
                    goal.weeks_left,
                    cls.num_weeks_saved(goal),
                    cls.num_weeks_saved_on_target(goal),
                    cls.num_weeks_saved_below(goal),
                    cls.num_weeks_saved_above(goal),
                    cls.num_weeks_not_saved(goal),
                    cls.num_withdrawals(goal),

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
                    cls.date_achieved(goal),
                    not goal.is_active,
                    goal.date_deleted
                ]

                append_to_csv(data, csvfile)

        success, message = pass_zip_encrypt_email(request, export_name, unique_time)

        if not success:
            return False, message

        try:
            fsock = open(STORAGE_DIRECTORY + export_name + unique_time + '.zip', "rb")
        except FileNotFoundError:
            return False, ERROR_MESSAGE_DATA_CLEANUP

        stream.streaming_content = fsock

        return True, SUCCESS_MESSAGE_EMAIL_SENT

    @classmethod
    def get_username(cls, goal):
        """Returns the user whom the goal belongs too"""
        return goal.user.username

    @classmethod
    def num_weeks_saved(cls, goal):
        """Returns the number of weeks that the user has saved"""

        weekly_aggregates = goal.get_weekly_aggregates()

        weeks_saved = 0
        for weekly_savings in weekly_aggregates:
            if weekly_savings is not 0:
                weeks_saved += 1

        return weeks_saved

    @classmethod
    def num_weeks_saved_on_target(cls, goal):
        """Returns the number of weeks the user saved the same as their weekly target"""

        weekly_aggregates = goal.get_weekly_aggregates()

        weeks_saved_on_target = 0
        for weekly_savings in weekly_aggregates:
            if weekly_savings == goal.weekly_target:
                weeks_saved_on_target += 1

        return weeks_saved_on_target

    @classmethod
    def num_weeks_saved_below(cls, goal):
        """Returns the number of weeks, that when the user saved, they saved below their weekly target"""

        weekly_aggregates = goal.get_weekly_aggregates()

        weeks_saved_below_target = 0
        for weekly_savings in weekly_aggregates:
            if 0 < weekly_savings < goal.weekly_target:
                weeks_saved_below_target += 1

        return weeks_saved_below_target

    @classmethod
    def num_weeks_saved_above(cls, goal):
        """Returns the number of weeks the user saved above their weekly target"""

        weekly_aggregates = goal.get_weekly_aggregates()

        weeks_saved_above_target = 0
        for weekly_savings in weekly_aggregates:
            if weekly_savings > goal.weekly_target:
                weeks_saved_above_target += 1

        return weeks_saved_above_target

    @classmethod
    def num_weeks_not_saved(cls, goal):
        """Returns the number of weeks the user did not save"""

        weekly_aggregates = goal.get_weekly_aggregates()

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

    # Goal dates

    @classmethod
    def date_achieved(cls, goal):
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


class UserReport:

    fields = ()

    @classmethod
    def export_csv(cls, request, stream, export_name, unique_time):
        profiles = Profile.objects.all()

        filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
        create_csv(filename)

        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            append_to_csv(('username', 'name', 'mobile', 'email', 'gender', 'age', 'user_type', 'date_joined',
                           'number_of_goals', 'total_badges_earned', 'first_goal_created_badges',
                           'first_savings_created_badges', 'halfway_badges', 'one_week_left_badges',
                           '2_week_streak_badges', '4_week_streak_badges', '6_week_streak_badges',
                           '2_week_on_track_badges', '4_week_on_track_badges', '8_week_on_track_badges',
                           'goal_reached_badges', 'budget_created_badges', 'budget_revision_badges',
                           'highest_streak_earned', 'total_streak_and_ontrack_badges', 'baseline_survey_complete',
                           'ea_tool1_completed', 'ea_tool2_completed', 'endline_survey_completed'),
                          csvfile)

            for profile in profiles:
                data = [
                    profile.user.username,
                    profile.user.first_name + " " + profile.user.last_name,
                    profile.mobile,
                    profile.user.email,
                    profile.gender,
                    profile.age,
                    cls.user_type(profile),
                    profile.user.date_joined,
                    cls.number_of_goals(profile),
                    cls.total_badges_earned(profile),
                    cls.num_first_goal_created_badges(profile),
                    cls.num_first_savings_created_badges(profile),
                    cls.num_halfway_badges(profile),
                    cls.num_one_week_left_badges(profile),
                    cls.num_2_week_streak_badges(profile),
                    cls.num_4_week_streak_badges(profile),
                    cls.num_6_week_streak_badges(profile),
                    cls.num_2_week_on_track_badges(profile),
                    cls.num_4_week_on_track_badges(profile),
                    cls.num_8_week_on_track_badges(profile),
                    cls.num_goal_reached_badges(profile),
                    cls.num_budget_created_badges(profile),
                    cls.num_budget_revision_badges(profile),
                    cls.highest_streak_earned(profile),
                    cls.total_streaks_earned(profile),
                    cls.total_streak_and_ontrack_badges(profile),
                    cls.baseline_survey_complete(profile),
                    cls.ea_tool1_completed(profile),
                    cls.ea_tool2_completed(profile),
                    cls.endline_survey_completed(profile)
                ]

                append_to_csv(data, csvfile)

        success, message = pass_zip_encrypt_email(request, export_name, unique_time)

        if not success:
            return False, message

        try:
            fsock = open(STORAGE_DIRECTORY + export_name + unique_time + '.zip', "rb")
        except FileNotFoundError:
            return False, ERROR_MESSAGE_DATA_CLEANUP

        stream.streaming_content = fsock

        return True, SUCCESS_MESSAGE_EMAIL_SENT

    @classmethod
    def user_type(cls, profile):
        return 0

    @classmethod
    def number_of_goals(cls, profile):
        """Returns the number of goals the user has"""
        user = profile.user
        return Goal.objects.filter(user=user).count()

    @classmethod
    def total_badges_earned(cls, profile):
        """Returns the total number of badges earned by the user"""
        user = profile.user
        return Badge.objects.filter(user=user).count()

    # Badge totals

    @classmethod
    def num_first_goal_created_badges(cls, profile):
        return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.GOAL_FIRST_CREATED).count()

    @classmethod
    def num_first_savings_created_badges(cls, profile):
        return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.TRANSACTION_FIRST).count()

    @classmethod
    def num_halfway_badges(cls, profile):
        return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.GOAL_HALFWAY).count()

    @classmethod
    def num_one_week_left_badges(cls, profile):
        return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.GOAL_WEEK_LEFT).count()

    @classmethod
    def num_2_week_streak_badges(cls, profile):
        return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.STREAK_2).count()

    @classmethod
    def num_4_week_streak_badges(cls, profile):
        return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.STREAK_4).count()

    @classmethod
    def num_6_week_streak_badges(cls, profile):
        return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.STREAK_6).count()

    @classmethod
    def num_2_week_on_track_badges(cls, profile):
        return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.WEEKLY_TARGET_2).count()

    @classmethod
    def num_4_week_on_track_badges(cls, profile):
        return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.WEEKLY_TARGET_4).count()

    @classmethod
    def num_6_week_on_track_badges(cls, profile):
        return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.WEEKLY_TARGET_6).count()

    @classmethod
    def num_8_week_on_track_badges(cls, profile):
        # TODO: Count number of 8 week on Track badges (Not implemented)
        return 0

    @classmethod
    def num_goal_reached_badges(cls, profile):
        # TODO: Count number of goal reached badges (Not implemented)
        return 0

    @classmethod
    def num_challenge_participation_badges(cls, profile):
        return UserBadge.objects.filter(user=profile.user, badge__badge_type=Badge.CHALLENGE_ENTRY).count()

    @classmethod
    def highest_streak_earned(cls, profile):
        goals = Goal.objects.filter(user=profile.user)
        highest_streak = 0
        current_count = 0

        for goal in goals:
            transactions = goal.get_weekly_aggregates()
            for trans in transactions:
                if trans != 0:
                    current_count += 1
                    if current_count > highest_streak:
                        highest_streak = current_count
                else:
                    current_count = 0
        return highest_streak

    @classmethod
    def total_streak_and_ontrack_badges(cls, profile):
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

    @classmethod
    def total_streaks_earned(cls, profile):
        goals = Goal.objects.filter(user=profile.user)
        total_streaks = 0
        current_count = 0

        for goal in goals:
            transactions = goal.get_weekly_aggregates()
            for trans in transactions:
                if trans != 0:
                    current_count += 1
                    if current_count > 1:
                        total_streaks += 1
                else:
                    current_count = 0

        return total_streaks

    @classmethod
    def num_quiz_complete_badges(cls, profile):
        # TODO: Return the number of Quiz Completed badges (Not implemented)
        return 0

    @classmethod
    def num_5_challenges_completed_badge(cls, profile):
        # TODO: Return the number of 5 Challenges badges (Not implemented)
        return 0

    @classmethod
    def num_5_quizzes_badges(cls, profile):
        # TODO: Return the number of 5 Quizzes badges (Not implemented)
        return 0

    @classmethod
    def num_perfect_score_badges(cls, profile):
        # TODO: Return the number of Perfect Score badges (Not implemented)
        return 0

    @classmethod
    def num_budget_created_badges(cls, profile):
        # TODO: Return the number of Budget Created badges (Not implemented)
        return 0

    @classmethod
    def num_budget_revision_badges(cls, profile):
        # TODO: Return the number of Budget Revision badges (Not implemented)
        return 0

    # Survey data

    @classmethod
    def baseline_survey_complete(cls, profile):
        """Return True/False if a user has completed the baseline survey"""
        try:
            CoachSurveySubmission.objects.get(user=profile.user, survey__bot_conversation=CoachSurvey.BASELINE)
            return True
        except:
            return False

    @classmethod
    def ea_tool1_completed(cls, profile):
        try:
            CoachSurveySubmission.objects.get(user=profile.user, survey__bot_conversation=CoachSurvey.EATOOL)
            return True
        except:
            return False

    @classmethod
    def ea_tool2_completed(cls, profile):
        # TODO: Return true/False if a user has completed the EA Tool 2 survey (Not implemented)
        return False

    @classmethod
    def endline_survey_completed(cls, profile):
        # TODO: Return true/False if a user has completed the endline survey (Not implemented)
        return False


class SavingsReport:

    fields = ()

    @classmethod
    def export_csv(cls, request, stream, export_name, unique_time):
        goals = Goal.objects.all()

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

        success, message = pass_zip_encrypt_email(request, export_name, unique_time)

        if not success:
            return False, message

        try:
            fsock = open(STORAGE_DIRECTORY + export_name + unique_time + '.zip', "rb")
        except FileNotFoundError:
            return False, ERROR_MESSAGE_DATA_CLEANUP

        stream.streaming_content = fsock

        return True, SUCCESS_MESSAGE_EMAIL_SENT


##########################
# Challenge Data Reports #
##########################


class SummaryDataPerChallenge:

    fields = ()

    @classmethod
    def export_csv(cls, request, stream, export_name, unique_time, date_from, date_to):
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
                    cls.total_challenge_completions(challenge),
                    cls.total_users_in_progress(challenge),
                    cls.total_no_response(challenge)
                ]

                append_to_csv(data, csvfile)

        success, message = pass_zip_encrypt_email(request, export_name, unique_time)

        if not success:
            return False, message

        try:
            fsock = open(STORAGE_DIRECTORY + export_name + unique_time + '.zip', "rb")
        except FileNotFoundError:
            return False, ERROR_MESSAGE_DATA_CLEANUP

        stream.streaming_content = fsock

        return True, SUCCESS_MESSAGE_EMAIL_SENT

    @classmethod
    def total_challenge_completions(cls, challenge):
        """Returns the number of participants who have completed a challenge"""
        return Participant.objects.filter(challenge=challenge, date_completed__isnull=False).count()

    @classmethod
    def total_users_in_progress(cls, challenge):
        """Returns the total number of participants who have started the challenge but not completed it"""
        return Participant.objects.filter(challenge=challenge, date_completed__isnull=True).count()

    @classmethod
    def total_no_response(cls, challenge):
        """Checks to see which users don't have a participant for the given challenge"""

        total_amount_of_users = User.objects.all().count()
        total_amount_of_participants = Participant.objects.filter(challenge=challenge).count()

        num_no_responses = total_amount_of_users - total_amount_of_participants

        return num_no_responses


class SummaryDataPerQuiz:

    fields = ()

    @classmethod
    def export_csv(cls, request, stream, export_name, unique_time):
        challenges = Challenge.objects.filter(type=Challenge.CTP_QUIZ)

        filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
        create_csv(filename)

        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            append_to_csv(('quiz_name', 'quiz_question', 'number_of_options', 'attempts'), csvfile)

            for challenge in challenges:
                quiz_questions = QuizQuestion.objects.filter(challenge=challenge)

                for quiz_question in quiz_questions:
                    question_options = QuestionOption.objects.filter(question=quiz_question)

                    attempts = ParticipantAnswer.objects.filter(question=quiz_question).count()

                    data = [
                        challenge.name,
                        quiz_question.text,
                        question_options.count(),
                        attempts
                    ]

                    append_to_csv(data, csvfile)

        success, message = pass_zip_encrypt_email(request, export_name, unique_time)

        if not success:
            return False, message

        try:
            fsock = open(STORAGE_DIRECTORY + export_name + unique_time + '.zip', "rb")
        except FileNotFoundError:
            return False, ERROR_MESSAGE_DATA_CLEANUP

        stream.streaming_content = fsock

        return True, SUCCESS_MESSAGE_EMAIL_SENT


class ChallengeExportPicture:

    fields = ()

    @classmethod
    def export_csv(cls, request, stream, export_name, unique_time, challenge_name):
        challenges = Challenge.objects.filter(type=Challenge.CTP_PICTURE, name=challenge_name)

        filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
        create_csv(filename)

        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            append_to_csv(('username', 'name', 'mobile', 'email', 'gender', 'age',
                           'user_type', 'date_joined', 'call_to_action'),
                          csvfile)

            for challenge in challenges:
                participants = Participant.objects.filter(challenge=challenge)

                for participant in participants:
                    profile = Profile.objects.get(user=participant.user)
                    data = [
                        participant.user.username,
                        participant.user.first_name,
                        profile.mobile,
                        participant.user.email,
                        profile.gender,
                        profile.age,
                        '',  # user type
                        profile.user.date_joined,
                        challenge.call_to_action
                    ]

                    append_to_csv(data, csvfile)

        success, message = pass_zip_encrypt_email(request, export_name, unique_time)

        if not success:
            return False, message

        try:
            fsock = open(STORAGE_DIRECTORY + export_name + unique_time + '.zip', "rb")
        except FileNotFoundError:
            return False, ERROR_MESSAGE_DATA_CLEANUP

        stream.streaming_content = fsock

        return True, SUCCESS_MESSAGE_EMAIL_SENT


class ChallengeExportQuiz:
    fields = ()

    @classmethod
    def export_csv(cls, request, stream, export_name, unique_time, challenge_name):
        challenges = Challenge.objects.filter(type=Challenge.CTP_QUIZ, name=challenge_name)

        filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
        create_csv(filename)

        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            append_to_csv(('username', 'name', 'mobile', 'email', 'gender', 'age', 'user_type', 'date_joined',
                           'submission_date', 'question', 'number_of_attempts'),
                          csvfile)

            for challenge in challenges:
                participants = Participant.objects.filter(challenge=challenge)
                quiz_questions = QuizQuestion.objects.filter(challenge=challenge)

                for participant in participants:
                    profile = Profile.objects.get(user=participant.user)
                    attempts = quiz_questions.annotate(num_attempts=Count('answers__id')) \
                        .values('id', 'text', 'num_attempts') \
                        .order_by('order')

                    data = [
                        participant.user.username,
                        participant.user.first_name,
                        profile.mobile,
                        participant.user.email,
                        profile.gender,
                        profile.age,
                        '',  # user type
                        participant.user.date_joined,
                        participant.date_completed,
                    ]

                    question_data = []
                    for attempt in attempts:
                        question_data = [attempt['text'], (attempt['num_attempts'])]
                        data.extend(question_data)

                    append_to_csv(data, csvfile)

        success, message = pass_zip_encrypt_email(request, export_name, unique_time)

        if not success:
            return False, message

        try:
            fsock = open(STORAGE_DIRECTORY + export_name + unique_time + '.zip', "rb")
        except FileNotFoundError:
            return False, ERROR_MESSAGE_DATA_CLEANUP

        stream.streaming_content = fsock

        return True, SUCCESS_MESSAGE_EMAIL_SENT


class ChallengeExportFreetext:

    fields = ()

    @classmethod
    def export_csv(cls, request, stream, export_name, unique_time, challenge_name):
        challenges = Challenge.objects.filter(type=Challenge.CTP_FREEFORM, name=challenge_name)

        filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
        create_csv(filename)

        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            append_to_csv(('username', 'name', 'mobile', 'email', 'gender', 'age', 'user_type', 'date_registered',
                           'submission', 'submission_date'),
                          csvfile)

            for challenge in challenges:
                participants = Participant.objects.filter(challenge=challenge)

                for participant in participants:
                    participant_free_text = ParticipantFreeText.objects.get(participant=participant)
                    profile = Profile.objects.get(user=participant.user)

                    data = [
                        participant.user.username,
                        participant.user.first_name,
                        profile.mobile,
                        participant.user.email,
                        profile.gender,
                        profile.age,
                        '',  # user type
                        participant.date_created,
                        participant_free_text.text,
                        participant_free_text.date_answered
                    ]

                    append_to_csv(data, csvfile)

        success, message = pass_zip_encrypt_email(request, export_name, unique_time)

        if not success:
            return False, message

        try:
            fsock = open(STORAGE_DIRECTORY + export_name + unique_time + '.zip', "rb")
        except FileNotFoundError:
            return False, ERROR_MESSAGE_DATA_CLEANUP

        stream.streaming_content = fsock

        return True, SUCCESS_MESSAGE_EMAIL_SENT


##########################
# Aggregate Data Reports #
##########################


class SummaryGoalData:

    fields = ()

    @classmethod
    def export_csv(cls, request, stream, export_name, unique_time):

        filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
        create_csv(filename)

        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            append_to_csv(('total_users_set_at_least_one_goal', 'total_users_achieved_at_least_one_goal',
                           'total_achieved_goals', 'percentage_of_weeks_saved_out_of_total_weeks'),
                          csvfile)

            data = [
                cls.num_users_set_at_least_one_goal(),
                cls.num_users_achieved_one_goal(),
                cls.num_achieved_goals(),
                cls.percentage_weeks_saved()
            ]

            append_to_csv(data, csvfile)

        success, message = pass_zip_encrypt_email(request, export_name, unique_time)

        if not success:
            return False, message

        try:
            fsock = open(STORAGE_DIRECTORY + export_name + unique_time + '.zip', "rb")
        except FileNotFoundError:
            return False, ERROR_MESSAGE_DATA_CLEANUP

        stream.streaming_content = fsock

        return True, SUCCESS_MESSAGE_EMAIL_SENT

    @classmethod
    def num_users_set_at_least_one_goal(cls):
        """Number of users with at least one goal set"""
        return Goal.objects.all().values('user_id').distinct().count()

    @classmethod
    def num_users_achieved_one_goal(cls):
        """Total amount of users who have achieved at least one goal"""
        num_users_achieved_one_goal = 0
        array_of_users = Goal.objects.all().values('user_id').distinct()

        for user in array_of_users:
            goals = Goal.objects.filter(user_id=user['user_id'])
            for goal in goals:
                if goal.progress >= 100:
                    num_users_achieved_one_goal += 1
                    break

        return num_users_achieved_one_goal

    @classmethod
    def num_achieved_goals(cls):
        """Number of achieved goals"""
        goals = Goal.objects.filter()
        num_achieved_goals = 0
        for goal in goals:
            if goal.progress >= 100:
                num_achieved_goals += 1

        return num_achieved_goals

    @classmethod
    def percentage_weeks_saved(cls):
        """Percentage weeks saved out of total weeks"""
        percentage_weeks_saved = 0
        goals = Goal.objects.filter()
        total_weeks = 0
        total_weeks_saved = 0

        for goal in goals:
            weekly_savings = goal.get_weekly_aggregates()
            total_weeks += goal.weeks
            for amount_saved_in_week in weekly_savings:
                if amount_saved_in_week != 0:
                    total_weeks_saved += 1

        if total_weeks is not 0 and total_weeks_saved is not 0:
            percentage_weeks_saved = (total_weeks_saved / total_weeks) * 100

        return percentage_weeks_saved


class GoalDataPerCategory:

    fields = ()

    @classmethod
    def export_csv(cls, request, stream, export_name, unique_time):

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
                    cls.total_users_achieved_at_least_one_goal(goal_prototype),
                    cls.average_total_goal_amount(goal_prototype),
                    cls.average_percentage_of_goal_reached(goal_prototype),
                    cls.total_users_50_percent_achieved(goal_prototype),
                    cls.total_users_100_percent_achieved(goal_prototype),
                    cls.percentage_of_weeks_saved_out_of_total_weeks(goal_prototype)
                ]

                append_to_csv(data, csvfile)

        success, message = pass_zip_encrypt_email(request, export_name, unique_time)

        if not success:
            return False, message

        try:
            fsock = open(STORAGE_DIRECTORY + export_name + unique_time + '.zip', "rb")
        except FileNotFoundError:
            return False, ERROR_MESSAGE_DATA_CLEANUP

        stream.streaming_content = fsock

        return True, SUCCESS_MESSAGE_EMAIL_SENT

    @classmethod
    def total_users_achieved_at_least_one_goal(cls, goal_prototype):
        """
        Returns the number of users that have achieved the goal prototype
        unique users
        """
        users_with_goals = Goal.objects.filter(prototype=goal_prototype).values('user_id').distinct()

        num_achieved_one_goal = 0
        for user in users_with_goals:
            users_goals = Goal.objects.filter(prototype=goal_prototype, user_id=user['user_id'])

            for goal in users_goals:
                if goal.progress >= 100:
                    num_achieved_one_goal += 1
                    break

        return num_achieved_one_goal

    @classmethod
    def average_total_goal_amount(cls, goal_prototype):
        """Returns the average goal amount for the given goal prototype"""
        goals = Goal.objects.filter(prototype=goal_prototype)

        total_amount_of_goals_count = goals.count()

        total_goals_value = 0
        for goal in goals:
            total_goals_value += goal.value

        if total_goals_value is not 0 and total_amount_of_goals_count is not 0:
            return total_goals_value / total_amount_of_goals_count
        else:
            return 0

    @classmethod
    def average_percentage_of_goal_reached(cls, goal_prototype):
        """Returns the average percentage of completions for the given goal prototype"""

        goals = Goal.objects.filter(prototype=goal_prototype)

        total_amount_of_goals = goals.count()

        num_achieved_goals = 0
        for goal in goals:
            if goal.progress >= 100:
                num_achieved_goals += 1

        if num_achieved_goals is not 0 and total_amount_of_goals is not 0:
            return (num_achieved_goals / total_amount_of_goals) * 100
        else:
            return 0

    @classmethod
    def total_users_50_percent_achieved(cls, goal_prototype):
        """Returns the total amount of users who have achieved 50% of the given goal prototype"""
        users_with_goals = Goal.objects.filter(prototype=goal_prototype).values('user_id').distinct()

        num_50_percent_achieved = 0
        for user in users_with_goals:
            users_goals = Goal.objects.filter(prototype=goal_prototype, user_id=user['user_id'])

            for goal in users_goals:
                if goal.progress >= 50:
                    num_50_percent_achieved += 1
                    break

        return num_50_percent_achieved

    @classmethod
    def total_users_100_percent_achieved(cls, goal_prototype):
        """
        Returns the total amount of users who have achieved 100% of the given goal prototype
        not unique users
        """
        goals = Goal.objects.filter(prototype=goal_prototype)

        num_100_percent_achieved = 0
        for goal in goals:
            users_goals = Goal.objects.filter(prototype=goal_prototype, user_id=goal.user_id)

            for user_goal in users_goals:
                if user_goal.progress >= 100:
                    num_100_percent_achieved += 1
                    break

        return num_100_percent_achieved

    @classmethod
    def percentage_of_weeks_saved_out_of_total_weeks(cls, goal_prototype):
        """Percentage of weeks saved for given goal prototype"""
        goals = Goal.objects.filter(prototype=goal_prototype)
        total_weeks = 0
        total_weeks_saved = 0

        for goal in goals:
            agg = goal.get_weekly_aggregates()
            total_weeks += goal.weeks
            for aggCount in agg:
                if aggCount != 0:
                    total_weeks_saved += 1

        return (total_weeks_saved/total_weeks)*100


class RewardsData:

    fields = ()

    @classmethod
    def export_csv(cls, request, stream, export_name, unique_time):

        filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
        create_csv(filename)

        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            append_to_csv(('total_badges_earned_by_all_users', 'total_users_at_least_one_streak',
                           'average_percentage_weeks_saved_weekly_target_met', 'average_percentage_weeks_saved'),
                          csvfile)

            data = [
                UserBadge.objects.all().count(),
                cls.total_users_at_least_one_streak(),
                cls.average_percentage_weeks_saved_weekly_target_met(),
                cls.average_percentage_weeks_saved()
            ]

            append_to_csv(data, csvfile)

        success, message = pass_zip_encrypt_email(request, export_name, unique_time)

        if not success:
            return False, message

        try:
            fsock = open(STORAGE_DIRECTORY + export_name + unique_time + '.zip', "rb")
        except FileNotFoundError:
            return False, ERROR_MESSAGE_DATA_CLEANUP

        stream.streaming_content = fsock

        return True, SUCCESS_MESSAGE_EMAIL_SENT

    @classmethod
    def total_users_at_least_one_streak(cls):
        """Returns the total number of users that have at least one streak"""
        users_with_streaks = 0
        users = User.objects.all()

        for user in users:
            goals = Goal.objects.filter(user=user)
            current_count = 0

            user_has_streak = False

            goal_generator = (goal for goal in goals if user_has_streak is False)

            for goal in goal_generator:
                transactions = goal.get_weekly_aggregates()

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

    @classmethod
    def average_percentage_weeks_saved_weekly_target_met(cls):
        """Average % of weeks saved where users reached their weekly target savings amount"""
        total_weeks_saved = 0
        total_weeks = 0

        users = User.objects.all()

        for user in users:
            goals = Goal.objects.filter(user=user)

            for goal in goals:
                weekly_aggregates = goal.get_weekly_aggregates()

                for week in weekly_aggregates:
                    if week >= goal.weekly_target:
                        total_weeks_saved += 1

                    total_weeks += 1

        if total_weeks_saved is not 0 and total_weeks is not 0:
            return (total_weeks_saved / total_weeks) * 100
        else:
            return 0

    @classmethod
    def average_percentage_weeks_saved(cls):
        """Average % of weeks saved - regardless of savings amount"""
        total_weeks_saved = 0
        total_weeks = 0

        users = User.objects.all()

        for user in users:
            goals = Goal.objects.filter(user=user)

            for goal in goals:
                weekly_aggregates = goal.get_weekly_aggregates()

                for week in weekly_aggregates:
                    if week > 0:
                        total_weeks_saved += 1

                    total_weeks += 1

        if total_weeks_saved is not 0 and total_weeks is not 0:
            return (total_weeks_saved / total_weeks) * 100
        else:
            return 0


class RewardsDataPerBadge:

    fields = ()

    @classmethod
    def export_csv(cls, request, stream, export_name, unique_time):

        filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
        create_csv(filename)

        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            append_to_csv(('badge_name', 'total_earned_by_all_users', 'total_earned_at_least_once'),
                          csvfile)

            badges = Badge.objects.all()

            for badge in badges:
                data = [
                    badge.name,
                    cls.total_earned_by_all_users(badge),
                    cls.total_earned_at_least_once(badge)
                ]

                append_to_csv(data, csvfile)

        success, message = pass_zip_encrypt_email(request, export_name, unique_time)

        if not success:
            return False, message

        try:
            fsock = open(STORAGE_DIRECTORY + export_name + unique_time + '.zip', "rb")
        except FileNotFoundError:
            return False, ERROR_MESSAGE_DATA_CLEANUP

        stream.streaming_content = fsock

        return True, SUCCESS_MESSAGE_EMAIL_SENT

    @classmethod
    def total_earned_by_all_users(cls, badge):
        """Returns the total number of badges won for the given badge for all users"""
        return Badge.objects.filter(badge_type=badge.badge_type).values('user').count()

    @classmethod
    def total_earned_at_least_once(cls, badge):
        """Return the total number of users that have earned the given badge at least once"""
        return Badge.objects.filter(badge_type=badge.badge_type).values('user').distinct().count()


class RewardsDataPerStreak:

    fields = ()

    @classmethod
    def export_csv(cls, request, stream, export_name, unique_time):

        filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
        create_csv(filename)

        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:

            append_to_csv(('streak_type', 'total_streaks_by_all_users', 'total_users_at_least_one_streak',
                           'total_users_reached_weekly_savings_amount', 'total_users_not_reached_weekly_savings_amount'),
                          csvfile)

            badges = Badge.objects.all()

            badge_generator = (badge for badge in badges
                               if (badge.badge_type is Badge.STREAK_2
                                   or badge.badge_type is Badge.STREAK_4
                                   or badge.badge_type is Badge.STREAK_6
                                   or badge.badge_type is Badge.WEEKLY_TARGET_2
                                   or badge.badge_type is Badge.WEEKLY_TARGET_4
                                   or badge.badge_type is Badge.WEEKLY_TARGET_6))

            for badge in badge_generator:
                data = [
                    badge.name,
                    cls.total_streak_badges(badge),
                    cls.total_streak_badges_at_least_one_user(badge),
                    cls.total_on_track_badges(badge),
                    cls.total_on_track_badges_at_least_one_user(badge)
                ]

                append_to_csv(data, csvfile)

        success, message = pass_zip_encrypt_email(request, export_name, unique_time)

        if not success:
            return False, message

        try:
            fsock = open(STORAGE_DIRECTORY + export_name + unique_time + '.zip', "rb")
        except FileNotFoundError:
            return False, ERROR_MESSAGE_DATA_CLEANUP

        stream.streaming_content = fsock

        return True, SUCCESS_MESSAGE_EMAIL_SENT

    @classmethod
    def total_streak_badges(cls, badge):
        """Returns the number of given streak badges awarded to all users"""
        badge_type = badge.badge_type
        if badge_type is Badge.STREAK_2 or badge_type is Badge.STREAK_4 or badge_type is Badge.STREAK_6:
            return UserBadge.objects.filter(badge=badge).count()
        else:
            return 0

    @classmethod
    def total_streak_badges_at_least_one_user(cls, badge):
        """"Returns the number given streak badges by earned by at least one user"""
        badge_type = badge.badge_type
        if badge_type is Badge.STREAK_2 \
                or badge_type is Badge.STREAK_4 \
                or badge_type is Badge.STREAK_6:
            return UserBadge.objects.filter(badge=badge).values('user').distinct().count()
        else:
            return 0

    @classmethod
    def total_on_track_badges(cls, badge):
        """Return the number of given 'on track' badges for given badge, else 0, awarded to all users"""
        badge_type = badge.badge_type
        if badge_type is Badge.WEEKLY_TARGET_2 \
            or badge_type is Badge.WEEKLY_TARGET_4 \
            or badge_type is Badge.WEEKLY_TARGET_6:
            return UserBadge.objects.filter(badge=badge).count()
        else:
            return 0

    @classmethod
    def total_on_track_badges_at_least_one_user(cls, badge):
        """Return the number of given 'on track' badges for given badge, else 0, earned by at least one user"""
        badge_type = badge.badge_type
        if badge_type is Badge.WEEKLY_TARGET_2 \
                or badge_type is Badge.WEEKLY_TARGET_4 \
                or badge_type is Badge.WEEKLY_TARGET_6:
            return UserBadge.objects.filter(badge=badge).values('user').distinct().count()
        else:
            return 0


class UserTypeData:

    fields = ()

    @classmethod
    def export_csv(cls, request, stream, export_name, unique_time):

        filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
        create_csv(filename)

        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            append_to_csv(('total_classroom_users', 'total_marketing_users'),
                          csvfile)

            # TODO: Return the total number of each type of user (Not implemented)

            data = [
                0,
                0
            ]

            append_to_csv(data, csvfile)

        success, message = pass_zip_encrypt_email(request, export_name, unique_time)

        if not success:
            return False, message

        try:
            fsock = open(STORAGE_DIRECTORY + export_name + unique_time + '.zip', "rb")
        except FileNotFoundError:
            return False, ERROR_MESSAGE_DATA_CLEANUP

        stream.streaming_content = fsock

        return True, SUCCESS_MESSAGE_EMAIL_SENT


##################
# Survey Reports #
##################


class SummarySurveyData:
    # TODO: Refactor this report to remove code repetition
    fields = ()

    @classmethod
    def export_csv(cls, request, stream, export_name, unique_time):

        filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
        create_csv(filename)

        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            append_to_csv(('survey_name', 'total_users_completed', 'total_users_in_progress', 'total_users_no_consent',
                           'total_users_claim_over_17', 'total_no_engagement', 'total_no_first_conversation'),
                          csvfile)

            # Baseline Survey

            num_completed_users = CoachSurveySubmissionDraft.objects.filter(
                survey__bot_conversation=CoachSurvey.BASELINE,
                complete=True).count()

            num_in_progress_users = 0
            num_first_convo_no = 0
            num_no_consent = 0
            num_claim_over_17_users = 0

            submitted_surveys = CoachSurveySubmissionDraft.objects.filter(survey__bot_conversation=CoachSurvey.BASELINE,
                                                                          consent=False)

            # Counts number of first conversation no responses, others checks to see if they have no consent
            for survey in submitted_surveys:
                submission_data = json.loads(survey.submission_data)
                if submission_data['survey_baseline_intro'] == '0':
                    num_first_convo_no += 1
                elif survey.consent is False:
                    num_no_consent += 1
                elif survey.complete is False:
                    num_in_progress_users += 1

            submitted_surveys = CoachSurveySubmissionDraft.objects.filter(survey__bot_conversation=CoachSurvey.BASELINE)

            for survey in submitted_surveys:
                if survey.submission is not None:
                    survey_data = survey.submission.get_data()
                    if survey_data['survey_baseline_q1_consent'] == 1:
                        num_claim_over_17_users += 1

            num_total_users = User.objects.all().count()
            num_participated_survey = CoachSurveySubmissionDraft.objects\
                .filter(survey__bot_conversation=CoachSurvey.BASELINE)\
                .values('user')\
                .distinct()\
                .count()

            num_no_engagement = num_total_users - num_participated_survey

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

            num_completed_users = CoachSurveySubmissionDraft.objects.filter(
                survey__bot_conversation=CoachSurvey.EATOOL,
                complete=True).count()

            num_in_progress_users = 0
            num_first_convo_no = 0
            num_no_consent = 0
            num_claim_over_17_users = 0

            submitted_surveys = CoachSurveySubmissionDraft.objects.filter(survey__bot_conversation=CoachSurvey.EATOOL,
                                                                          consent=False)

            # Counts number of first conversation no responses, others checks to see if they have no consent
            for survey in submitted_surveys:
                submission_data = json.loads(survey.submission_data)
                if submission_data['survey_eatool_intro'] == '0':
                    num_first_convo_no += 1
                elif survey.consent is False:
                    num_no_consent += 1
                elif survey.complete is False:
                    num_in_progress_users += 1

            submitted_surveys = CoachSurveySubmissionDraft.objects.filter(survey__bot_conversation=CoachSurvey.EATOOL)

            for survey in submitted_surveys:
                if survey.submission is not None:
                    survey_data = survey.submission.get_data()
                    if survey_data['survey_eatool_q1_consent'] == 1:
                        num_claim_over_17_users += 1

            num_total_users = User.objects.all().count()
            num_participated_survey = CoachSurveySubmissionDraft.objects \
                .filter(survey__bot_conversation=CoachSurvey.EATOOL) \
                .values('user') \
                .distinct() \
                .count()

            num_no_engagement = num_total_users - num_participated_survey

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

        success, message = pass_zip_encrypt_email(request, export_name, unique_time)

        if not success:
            return False, message

        try:
            fsock = open(STORAGE_DIRECTORY + export_name + unique_time + '.zip', "rb")
        except FileNotFoundError:
            return False, ERROR_MESSAGE_DATA_CLEANUP

        stream.streaming_content = fsock

        return True, SUCCESS_MESSAGE_EMAIL_SENT


class BaselineSurveyData:
    fields = ()

    @classmethod
    def export_csv(cls, request, stream, export_name, unique_time):
        surveys = CoachSurvey.objects.filter(bot_conversation=CoachSurvey.BASELINE)

        filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
        create_csv(filename)

        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            append_to_csv(('uuid', 'username', 'name', 'mobile', 'email', 'gender', 'age',
                           'user_type', 'date_joined', 'city', 'younger_than_17', 'consent_given',
                           'submission_date',

                           # Survey questions
                           'q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8', 'q9', 'q10', 'q11',
                           'q12', 'q13', 'q14', 'q15', 'q16', 'q17', 'q18', 'q19', 'q20', 'q21', 'q22', 'q23',
                           'q24', 'q25', 'q26', 'q27_1', 'q27_2', '27_3', 'q28', 'q29_1', 'q29_2', 'q29_3', 'q29_4'),
                          csvfile)

            for survey in surveys:
                # All baseline survey submissions that are complete
                submissions = CoachSurveySubmissionDraft.objects.filter(survey=survey, complete=True)

                for submission in submissions:
                    survey_data = submission.submission.get_data()

                    data = [
                        submission.submission.user_unique_id,
                        submission.submission.username,
                        submission.submission.name,
                        submission.submission.mobile,
                        submission.submission.email,
                        submission.submission.gender,
                        submission.submission.age,
                        '',  # user type
                        submission.user.date_joined,
                        survey_data['survey_baseline_q04_city'],
                        survey_data['survey_baseline_q1_consent'],
                        submission.consent,  # survey_data['survey_baseline_q2_consent']
                        submission.modified_at,

                        # survey questions
                        survey_data['survey_baseline_q01_occupation'],
                        survey_data['survey_baseline_q02_grade'],
                        survey_data['survey_baseline_q03_school_name'],
                        survey_data['survey_baseline_q04_city'],
                        survey_data['survey_baseline_q05_job_month'],
                        survey_data['survey_baseline_q06_job_earning_range'],
                        survey_data['survey_baseline_q07_job_status'],
                        survey_data['survey_baseline_q08_shared_ownership'],
                        survey_data['survey_baseline_q09_business_earning_range'],
                        survey_data['survey_baseline_q10_save'],
                        survey_data['survey_baseline_q11_savings_frequency'],
                        survey_data['survey_baseline_q12_savings_where'],
                        survey_data['survey_baseline_q13_savings_3_months'],
                        survey_data['survey_baseline_q14_saving_education'],
                        survey_data['survey_baseline_q15_job_hunt'],
                        survey_data['survey_baseline_q16_emergencies'],
                        survey_data['survey_baseline_q17_invest'],
                        survey_data['survey_baseline_q18_family'],
                        survey_data['survey_baseline_q19_clothes_food'],
                        '',  # Missing q20
                        survey_data['survey_baseline_q21_gadgets'],
                        survey_data['survey_baseline_q22_friends'],
                        survey_data['survey_baseline_q23_mobile_frequency'],
                        survey_data['survey_baseline_q24_mobile_most_use'],
                        survey_data['survey_baseline_q25_mobile_least_use'],
                        survey_data['survey_baseline_q26_mobile_own'],
                        survey_data['survey_baseline_q27_1_friends'],
                        survey_data['survey_baseline_q27_2_family'],
                        survey_data['survey_baseline_q27_3_community'],
                        survey_data['survey_baseline_q28_mobile_credit'],
                        survey_data['survey_baseline_q29_1_desktop'],
                        survey_data['survey_baseline_q29_2_laptop'],
                        survey_data['survey_baseline_q29_3_mobile_no_data'],
                        survey_data['survey_baseline_q29_4_mobile_data']
                    ]

                    append_to_csv(data, csvfile)

        success, message = pass_zip_encrypt_email(request, export_name, unique_time)

        if not success:
            return False, message

        try:
            fsock = open(STORAGE_DIRECTORY + export_name + unique_time + '.zip', "rb")
        except FileNotFoundError:
            return False, ERROR_MESSAGE_DATA_CLEANUP

        stream.streaming_content = fsock

        return True, SUCCESS_MESSAGE_EMAIL_SENT


class EaTool1SurveyData:
    fields = ()

    @classmethod
    def export_csv(cls, request, stream, export_name, unique_time):
        surveys = CoachSurvey.objects.filter(bot_conversation=CoachSurvey.EATOOL)

        filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
        create_csv(filename)

        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            append_to_csv(('uuid', 'username', 'name', 'mobile', 'email', 'gender', 'age',
                           'user_type', 'date_joined', 'city', 'younger_than_17', 'consent_given',
                           'submission_date',

                           # Survey questions
                           'q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8', 'q9', 'q10', 'q11', 'q12',
                           'q13', 'q14', 'q15', 'q16', 'q17', 'q18', 'q19', 'q20', 'q21', 'q22', 'q23', 'q24'
                           ),
                          csvfile)

            for survey in surveys:
                submissions = CoachSurveySubmissionDraft.objects.filter(survey=survey, complete=True)

                for submission in submissions:
                    survey_data = submission.submission.get_data()

                    data = [
                        submission.submission.user_unique_id,
                        submission.submission.username,
                        submission.submission.name,
                        submission.submission.mobile,
                        submission.submission.email,
                        submission.submission.gender,
                        submission.submission.age,
                        '',  # user type
                        submission.user.date_joined,
                        '',  # City
                        survey_data['survey_eatool_q1_consent'],
                        submission.consent,  # survey_data['survey_eatool_q2_consent']
                        submission.modified_at,

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

        success, message = pass_zip_encrypt_email(request, export_name, unique_time)

        if not success:
            return False, message

        try:
            fsock = open(STORAGE_DIRECTORY + export_name + unique_time + '.zip', "rb")
        except FileNotFoundError:
            return False, ERROR_MESSAGE_DATA_CLEANUP

        stream.streaming_content = fsock

        return True, SUCCESS_MESSAGE_EMAIL_SENT


class EaTool2SurveyData:
    fields = ()

    @classmethod
    def export_csv(cls, request, stream, export_name, unique_time):
        # surveys = CoachSurvey.objects.filter(bot_conversation=CoachSurvey.EATOOL2)

        filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
        create_csv(filename)

        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
            append_to_csv(('uuid', 'username', 'name', 'mobile', 'email', 'gender', 'age',
                           'user_type', 'date_joined', 'city', 'younger_than_17', 'consent_given',
                           'submission_date',

                           # Survey questions
                           ),
                          csvfile)

        success, message = pass_zip_encrypt_email(request, export_name, unique_time)

        if not success:
            return False, message

        try:
            fsock = open(STORAGE_DIRECTORY + export_name + unique_time + '.zip', "rb")
        except FileNotFoundError:
            return False, ERROR_MESSAGE_DATA_CLEANUP

        stream.streaming_content = fsock

        return True, SUCCESS_MESSAGE_EMAIL_SENT


class EndlineSurveyData:
    fields = ()

    @classmethod
    def export_csv(cls, request, stream, export_name, unique_time):
        # surveys = CoachSurvey.objects.filter(bot_conversation=CoachSurvey.ENDLINE)

        filename = STORAGE_DIRECTORY + export_name + unique_time + '.csv'
        create_csv(filename)

        with open(filename, 'a', newline='', encoding='utf-8') as csvfile:

            append_to_csv(('uuid', 'username', 'name', 'mobile', 'email', 'gender', 'age',
                           'user_type', 'date_joined', 'city', 'younger_than_17', 'consent_given',
                           'submission_date',

                           # Survey questions
                           ),
                          csvfile)

        success, message = pass_zip_encrypt_email(request, export_name, unique_time)

        if not success:
            return False, message

        try:
            fsock = open(STORAGE_DIRECTORY + export_name + unique_time + '.zip', "rb")
        except FileNotFoundError:
            return False, ERROR_MESSAGE_DATA_CLEANUP

        stream.streaming_content = fsock

        return True, SUCCESS_MESSAGE_EMAIL_SENT
