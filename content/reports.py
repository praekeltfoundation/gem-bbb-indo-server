import csv
from datetime import timedelta, datetime
from django.db.models import Count

from users.models import Profile
from .models import Goal, Badge, BadgeSettings, UserBadge, GoalTransaction, WeekCalc, Challenge, Participant, \
    QuizQuestion, QuestionOption, Entry, ParticipantAnswer, ParticipantFreeText


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
        return goal.user.username

    @classmethod
    def num_weeks_saved(cls, goal):
        # TODO: Return number of weeks that the user has saved

        goal_transactions = GoalTransaction.objects.filter(goal=goal).order_by('date')



        return 0

    @classmethod
    def num_weeks_saved_on_target(cls, goal):
        # TODO: Return the number of weeks saved on target
        return 0

    @classmethod
    def num_weeks_saved_below(cls, goal):
        # TODO: Return number of weeks saved below target
        return 0

    @classmethod
    def num_weeks_saved_above(cls, goal):
        # TODO: Return number of weeks saved above target
        return 0

    @classmethod
    def num_weeks_not_saved(cls, goal):
        # TODO: Return the number of weeks the user hasn't saved
        return 0

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

    #Goal edit history

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

    @classmethod
    def num_weekly_target_edited(cls, goal):
        # TODO: Return the number of times the user has edited their weekly target
        return 0

    @classmethod
    def num_weekly_target_increased(cls, goal):
        # TODO: Return the number of times weekly target increased
        return 0

    @classmethod
    def num_weekly_target_decreased(cls, goal):
        # TODO: Return the number of times weekly target decreased
        return 0

    @classmethod
    def weekly_target_original(cls, goal):
        # TODO: Return the original (first) weekly target
        return 0

    @classmethod
    def num_goal_target_edited(cls, goal):
        # TODO: Return the number of times the goals target was edited
        return 0

    @classmethod
    def num_goal_target_increased(cls, goal):
        # TODO: Return the number of times goal target increased
        return 0

    @classmethod
    def num_goal_target_decreased(cls, goal):
        # TODO: Return the number of times goal target decreased
        return 0

    @classmethod
    def goal_weeks_initial(cls, goal):
        # TODO: Return the initial number of goal weeks (When goal was set)
        return 0

    @classmethod
    def goal_weeks_current(cls, goal):
        # TODO: Return the current number of weeks for the goal
        # Current weeks left or total weeks of goal??
        return 0

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
        user = profile.user
        return Goal.objects.filter(user=user).count()

    @classmethod
    def total_badges_earned(cls, profile):
        user = profile.user
        return Badge.objects.filter(user=user).count()

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

    @classmethod
    def baseline_survey_complete(cls, profile):
        # TODO: Return True/False if a user has completed the baseline survey
        return False

    @classmethod
    def ea_tool1_completed(cls, profile):
        # TODO: Return true/False if a user has completed the EA Tool 1 survey
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
                    cls.weekly_target_at_transaction(transaction),

                    # Deposit/Withdrawal details
                    transaction.is_deposit,
                    transaction.value,
                    transaction.date,
                    amount_saved
                ]

                writer.writerow(data)

    @classmethod
    def weekly_target_at_transaction(cls, obj):
        return obj.goal.weekly_target


class SummaryDataPerChallenge:

    fields = ()

    @classmethod
    def export_csv(cls, stream, date_from, date_to):
        if date_from is not None and date_to is not None:
            challenges = Challenge.objects.filter(activation_date__gte=date_from, deactivation_date__lte=date_to)
        else:
            challenges = Challenge.objects.all()

        writer = csv.writer(stream)

        for challenge in challenges:
            data = [
                challenge.name,
                challenge.type,
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
        return Participant.objects.filter(challenge=challenge).count()

    @classmethod
    def total_users_in_progress(cls, challenge):
        # TODO: Return total users in progress
        return 0

    @classmethod
    def no_response_total(cls, challenge):
        # TODO: Return the number of no responses
        return 0


class SummaryDataPerQuiz:

    fields = ()

    @classmethod
    def export_csv(cls, stream):
        challenges = Challenge.objects.filter(type=Challenge.CTP_QUIZ)
        writer = csv.writer(stream)

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
        return 0


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
            quiz_questions = QuizQuestion.objects.filter(challenge=challenge)

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
