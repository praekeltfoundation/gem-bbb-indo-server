import csv
from datetime import timedelta, datetime

from django.contrib.auth.models import User
from django.db.models import Count, Avg

from survey.models import CoachSurveySubmission, CoachSurvey
from users.models import Profile
from .models import Goal, Badge, BadgeSettings, UserBadge, GoalTransaction, WeekCalc, Challenge, Participant, \
    QuizQuestion, QuestionOption, Entry, ParticipantAnswer, ParticipantFreeText, GoalPrototype


#####################
# Goal Data Reports #
#####################


class GoalReport:

    fields = ()

    @classmethod
    def export_csv(cls, stream):
        goals = Goal.objects.all()
        writer = csv.writer(stream)

        writer.writerow(('username', 'prototype_bahasa', 'prototype_english', 'goal_name', 'goal_target',
                         'goal_value', 'goal_progress', 'weekly_target', 'total_weeks', 'weeks_left',
                         'weeks_saved', 'week_saved_on_target', 'weeks_saved_below_target', 'weeks_saved_above_target',
                         'weeks_not_saved', 'withdrawals',

                         # Goal edit history
                         'original_goal_date', 'new_goal_date', 'original_weekly_target', 'new_weekly_target',
                         'original_goal_target', 'new_goal_target', 'date_edited',

                         'date_created', 'goal_achieved', 'goal_deleted', 'date_deleted'))

        for goal in goals:
            data = [
                # Weekly savings
                cls.get_username(goal),
                '',  # TODO: Goal prototype in Bahasa
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
                cls.original_goal_date(goal),
                cls.new_goal_date(goal),
                cls.original_weekly_target(goal),
                cls.new_weekly_target(goal),
                cls.original_goal_target(goal),
                cls.new_goal_target(goal),
                cls.date_goal_edited(goal),

                # Goal dates
                goal.start_date,
                cls.date_achieved(goal),
                not goal.is_active,
                cls.date_deleted(goal)
            ]
            writer.writerow(data)

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
        """Returns the number of weeks the user saved below their weekly target"""

        weekly_aggregates = goal.get_weekly_aggregates()

        weeks_saved_below_target = 0
        for weekly_savings in weekly_aggregates:
            if weekly_savings < goal.weekly_target:
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

    # Goal edit history

    @classmethod
    def original_goal_date(cls, goal):
        # TODO: Return the original goal date
        return 0

    @classmethod
    def new_goal_date(cls, goal):
        # TODO: Return the new date of the goal
        return 0

    @classmethod
    def original_weekly_target(cls, goal):
        # TODO: Return the original weekly target of the goal
        return 0

    @classmethod
    def new_weekly_target(cls, goal):
        # TODO: Return the weekly target set during goal edit
        return 0

    @classmethod
    def original_goal_target(cls, goal):
        # TODO: Return the original goal target
        return 0

    @classmethod
    def new_goal_target(cls, goal):
        # TODO: Return the new goal target set during the goal edit
        return 0

    @classmethod
    def date_goal_edited(cls, goal):
        # TODO: Return the date the goal was edited
        return 0

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

    @classmethod
    def date_deleted(cls, goal):
        # TODO: Implement date deleted field on Goal model
        return 0


class UserReport:

    fields = ()

    @classmethod
    def export_csv(cls, stream):
        profiles = Profile.objects.all()
        writer = csv.writer(stream)

        writer.writerow(('username', 'name', 'mobile', 'email', 'gender', 'age', 'user_type', 'date_joined',
                         'number_of_goals', 'total_badges_earned', 'first_goal_created_badges',
                         'first_savings_created_badges', 'halfway_badges', 'one_week_left_badges',
                         '2_week_streak_badges', '4_week_streak_badges', '6_week_streak_badges',
                         '2_week_on_track_badges', '4_week_on_track_badges', '8_week_on_track_badges',
                         'goal_reached_badges', 'budget_created_badges', 'budget_revision_badges',
                         'highest_streak_earned', 'total_streak_and_ontrack_badges', 'baseline_survey_complete',
                         'ea_tool1_completed', 'ea_tool2_completed', 'endline_survey_completed'))

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
                cls.total_streak_and_ontrack_badges(profile),
                cls.baseline_survey_complete(profile),
                cls.ea_tool1_completed(profile),
                cls.ea_tool2_completed(profile),
                cls.endline_survey_completed(profile)
            ]

            writer.writerow(data)

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
        # TODO: Count number of First Goal Created badges
        return 0

    @classmethod
    def num_first_savings_created_badges(cls, profile):
        # TODO: Count number of First Savings Created badges
        return 0

    @classmethod
    def num_halfway_badges(cls, profile):
        # TODO: Count number of Halfway badges
        return 0

    @classmethod
    def num_one_week_left_badges(cls, profile):
        # TODO: Count number of One Week Left badges
        return 0

    @classmethod
    def num_2_week_streak_badges(cls, profile):
        # TODO: Count number of 2 Week Streak badges
        return 0

    @classmethod
    def num_4_week_streak_badges(cls, profile):
        # TODO: Count number of 4 week streak badges
        return 0

    @classmethod
    def num_6_week_streak_badges(cls, profile):
        # TODO: Count number of 6 week streak badges
        return 0

    @classmethod
    def num_2_week_on_track_badges(cls, profile):
        # TODO: Count number of 2 Week on Track badges
        return 0

    @classmethod
    def num_4_week_on_track_badges(cls, profile):
        # TODO: Count number of 4 week on Track badges
        return 0

    @classmethod
    def num_6_week_on_track_badges(cls, profile):
        # TODO: Count number of 6 week on Track badges
        return 0

    @classmethod
    def num_8_week_on_track_badges(cls, profile):
        # TODO: Count number of 8 week on Track badges
        return 0

    @classmethod
    def num_goal_reached_badges(cls, profile):
        # TODO: Count number of goal reached badges
        return 0

    @classmethod
    def num_challenge_participation_badges(cls, profile):
        # TODO: Count number of Challenge Participation badges
        return 0

    @classmethod
    def highest_streak_earned(cls, profile):
        # TODO: Return the users highest streak
        return 0

    @classmethod
    def total_streak_and_ontrack_badges(cls, profile):
        # TODO: Return the total number of on-track and streak badges
        return 0

    @classmethod
    def total_streaks_earned(cls, profile):
        # TODO: Return the number of streaks earned
        return 0

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
    def export_csv(cls, stream):
        goals = Goal.objects.all()
        writer = csv.writer(stream)

        writer.writerow(('username', 'goal_name', 'goal_weekly_target', 'transaction_type', 'transaction_value',
                         'transaction_date', 'amount_saved'))

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

                writer.writerow(data)


##########################
# Challenge Data Reports #
##########################


class SummaryDataPerChallenge:

    fields = ()

    @classmethod
    def export_csv(cls, stream, date_from, date_to):
        if date_from is not None and date_to is not None:
            challenges = Challenge.objects.filter(activation_date__gte=date_from, deactivation_date__lte=date_to)
        else:
            challenges = Challenge.objects.all()

        writer = csv.writer(stream)

        writer.writerow(('challenge_name', 'challenge_type', 'call_to_action', 'activation_date', 'deactivation_date',
                        'total_challenge_completions', 'total_users_in_progress', 'total_no_responses'))

        for challenge in challenges:
            data = [
                challenge.name,
                challenge.get_type_display(),
                challenge.call_to_action,
                challenge.activation_date,
                challenge.deactivation_date,
                cls.total_challenge_completions(challenge),
                cls.total_users_in_progress(challenge),
                cls.no_response_total(challenge)
            ]

            writer.writerow(data)

    @classmethod
    def total_challenge_completions(cls, challenge):
        """Returns the number of participants who have completed a challenge"""
        return Participant.objects.filter(challenge=challenge, date_completed__isnull=False).count()

    @classmethod
    def total_users_in_progress(cls, challenge):
        """Returns the total number of participants who have started the challenge but not completed it"""
        return Participant.objects.filter(challenge=challenge, date_completed__isnull=True).count()

    @classmethod
    def no_response_total(cls, challenge):
        """Checks to see which users don't have a participant for the given challenge"""
        # TODO: Not returning correct values
        total_amount_of_users = User.objects.all().count()

        # total_users_responded = User.objects.filter(participants__challenge=challenge).count()
        #
        # temp = User.objects.all().annotate(no_responses=Count('participants'))

        total_users_responded = User.objects.filter(
            participants__challenge=challenge).annotate(no_responses=Count('participants')).count()

        return total_amount_of_users - total_users_responded


class SummaryDataPerQuiz:

    fields = ()

    @classmethod
    def export_csv(cls, stream):
        challenges = Challenge.objects.filter(type=Challenge.CTP_QUIZ)
        writer = csv.writer(stream)

        writer.writerow(('quiz_name', 'quiz_question', 'number_of_options', 'average_attempts'))

        for challenge in challenges:
            quiz_questions = QuizQuestion.objects.filter(challenge=challenge)

            for quiz_question in quiz_questions:
                question_options = QuestionOption.objects.filter(question=quiz_question)

                # attempts = quiz_questions.annotate(num_attempts=Count('answers__id')) \
                #     .values('id', 'text', 'num_attempts') \
                #     .order_by('order')

                data = [
                    challenge.name,
                    quiz_question.text,
                    question_options.count(),
                    cls.average_number_question_attempts(quiz_question, question_options)
                ]

                writer.writerow(data)

    @classmethod
    def average_number_question_attempts(cls, question, options):
        # TODO: Return the average number of user attempts per question option
        average_attempts = 0
        return average_attempts


class ChallengeExportPicture:

    fields = ()

    @classmethod
    def export_csv(cls, stream, challenge_name):
        challenges = Challenge.objects.filter(type=Challenge.CTP_PICTURE, name=challenge_name)

        writer = csv.writer(stream)

        writer.writerow(('username', 'name', 'mobile', 'email', 'gender', 'age',
                         'user_type', 'date_joined', 'call_to_action'))

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

                writer.writerow(data)


class ChallengeExportQuiz:

    fields = ()

    @classmethod
    def export_csv(cls, stream, challenge_name):
        challenges = Challenge.objects.filter(type=Challenge.CTP_QUIZ, name=challenge_name)

        writer = csv.writer(stream)

        writer.writerow(('username', 'name', 'mobile', 'email', 'gender', 'age', 'user_type', 'date_joined',
                         'submission_date', 'question', 'number_of_attempts'))

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

                writer.writerow(data)


class ChallengeExportFreetext:

    fields = ()

    @classmethod
    def export_csv(cls, stream, challenge_name):
        challenges = Challenge.objects.filter(type=Challenge.CTP_FREEFORM, name=challenge_name)

        writer = csv.writer(stream)

        writer.writerow(('username', 'name', 'mobile', 'email', 'gender', 'age', 'user_type', 'date_registered',
                         'submission', 'submission_date'))

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

                writer.writerow(data)


##########################
# Aggregate Data Reports #
##########################


class SummaryGoalData:

    fields = ()

    @classmethod
    def export_csv(cls, stream):
        writer = csv.writer(stream)
        writer.writerow(('total_users_set_at_least_one_goal', 'total_users_achieved_at_least_one_goal',
                         'total_achieved_goals', 'percentage_of_weeks_saved_out_of_total_weeks'))

        # Number of users with at least one goal set
        num_users_at_least_one_goal = Goal.objects.all().values('user_id').distinct().count()

        # TODO: Total amount of users who have achieved at least one goal
        num_users_achieved_one_goal = 0
        array_of_users = Goal.objects.all().values('user_id').distinct()

        for user in array_of_users:
            goals = Goal.objects.filter(user_id=user['user_id'])
            for goal in goals:
                if goal.progress >= 100:
                    num_users_achieved_one_goal += 1
                break

        goals = Goal.objects.all()

        # Number of achieved goals
        num_achieved_goals = 0
        for goal in goals:
            if goal.progress >= 100:
                num_achieved_goals += 1

        # Percentage weeks saved out of total weeks
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

        data = [
            num_users_at_least_one_goal,
            num_users_achieved_one_goal,
            num_achieved_goals,
            percentage_weeks_saved
        ]

        writer.writerow(data)


class GoalDataPerCategory:

    fields = ()

    @classmethod
    def export_csv(cls, stream):
        writer = csv.writer(stream)
        writer.writerow(('category', 'total_users_at_least_one_goal', 'total_goals_set',
                         'total_users_achieved_one_goal', 'average_goal_amount', 'average_percentage_goal_reached',
                         'total_users_50_percent_achieved', 'total_users_100_percent_achieved',
                         'percentage_of_weeks_saved_out_of_total_weeks'))

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

            writer.writerow(data)

    @classmethod
    def total_users_achieved_at_least_one_goal(cls, goal_prototype):
        users_with_goals = Goal.objects.filter(prototype=goal_prototype).values('user_id').distinct()

        num_achieved_one_goal = 0

        for user in users_with_goals:
            users_goals = Goal.objects.filter(user_id=user['user_id'])

            for goal in users_goals:
                if goal.progress >= 100:
                    num_achieved_one_goal += 1
                    break

        return num_achieved_one_goal

    @classmethod
    def average_total_goal_amount(cls, goal_prototype):

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
        # return Goal.objects.all().aggregate(Avg('progress'))

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
        users_with_goals = Goal.objects.filter(prototype=goal_prototype).values('user_id').distinct()

        num_100_percent_achieved = 0
        for user in users_with_goals:
            users_goals = Goal.objects.filter(prototype=goal_prototype, user_id=user['user_id'])

            for goal in users_goals:
                if goal.progress >= 100:
                    num_100_percent_achieved += 1
                    break

        return num_100_percent_achieved

    @classmethod
    def percentage_of_weeks_saved_out_of_total_weeks(cls, goal_prototype):
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
    def export_csv(cls, stream):
        writer = csv.writer(stream)
        writer.writerow(('total_badges_earned_by_all_users', 'total_users_at_least_one_streak',
                         'average_percentage_weeks_saved_weekly_target_met', 'average_percentage_weeks_saved'))

        data = [
            UserBadge.objects.all().count(),
            cls.total_users_at_least_one_streak(),
            cls.average_percentage_weeks_saved_weekly_target_met(),
            cls.average_percentage_weeks_saved()
        ]

        writer.writerow(data)

    @classmethod
    def total_users_at_least_one_streak(cls):
        return 0

    @classmethod
    def average_percentage_weeks_saved_weekly_target_met(cls):
        return 0

    @classmethod
    def average_percentage_weeks_saved(cls):
        return 0


class RewardsDataPerBadge:

    fields = ()

    @classmethod
    def export_csv(cls, stream):
        writer = csv.writer(stream)
        writer.writerow(('badge_name', 'total_earned_by_all_users', 'total_users_who_have_earned_a_badge'))


class RewardsDataPerStreak:

    fields = ()

    @classmethod
    def export_csv(cls, stream):
        writer = csv.writer(stream)
        writer.writerow(('streak_type', 'total_streaks_by_all_users', 'total_users_at_least_one_streak',
                         'total_users_reached_weekly_savings_amount', 'total_users_not_reached_weekly_savings_amount'))


class UserTypeData:

    fields = ()

    @classmethod
    def export_csv(cls, stream):
        writer = csv.writer(stream)
        writer.writerow(('total_classroom_users', 'total_marketing_users'))



