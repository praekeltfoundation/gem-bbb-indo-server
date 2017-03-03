import csv
from datetime import timedelta, datetime

from users.models import Profile
from .models import Goal, Badge, BadgeSettings, UserBadge, GoalTransaction, WeekCalc, Challenge, Participant, \
    QuizQuestion, QuestionOption, Entry


class GoalReport:
    fields = ()

    @classmethod
    def export_csv(cls, stream):
        goals = Goal.objects.all()
        writer = csv.writer(stream)
        writer.writerow(cls.fields)

        writer.writerow(('username', 'prototype_english', 'prototype_bahasa', 'goal_name', 'goal_target',
                         'goal_value', 'goal_progress', 'weekly_target', 'total_weeks', 'weeks_left',
                         'weeks_saved', 'week_saved_on_target', 'weeks_saved_below_target', 'weeks_saved_above_target',
                         'weeks_not_saved', 'withdrawals', 'times_weekly_target_edited',
                         'times_weekly_target_increased',
                         'times_weekly_target_decreased', 'original_weekly_target', 'current_weekly_target',
                         'times_goal_edited',))

        for goal in goals:
            data = [
                # Weekly savings
                cls.get_username(goal),
                # TODO: Goal prototype in Bahasa
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
                goal.is_goal_reached,
                cls.date_achieved(goal),
                goal.is_active,
                cls.date_deleted(goal)
            ]
            writer.writerow([getattr(goal, field) for field in cls.fields] + data)

    @classmethod
    def get_username(cls, obj):
        return obj.user.username

    @staticmethod
    def num_weeks_saved(obj):
        # TODO: Return number of weeks that the user has saved
        return 0

    def num_weeks_saved_on_target(obj):
        # TODO: Return the number of weeks saved on target
        return 0

    def num_weeks_saved_below(obj):
        # TODO: Return number of weeks saved below target
        return 0

    def num_weeks_saved_above(obj):
        # TODO: Return number of weeks saved above target
        return 0

    def num_weeks_not_saved(obj):
        # TODO: Return the number of weeks the user hasn't saved
        return 0

    def num_withdrawals(obj):
        """Returns the number of withdrawals made on a goal"""
        transactions = GoalTransaction.objects.filter(goal=obj)

        if not transactions:
            return 0

        withdrawals = 0

        for t in transactions:
            if t.is_withdraw:
                withdrawals += 1

        return withdrawals

    def original_goal_date(obj):
        # TODO: Return the original goal date
        return 0

    def new_goal_date(obj):
        # TODO: Return the new date of the goal
        return 0

    def original_weekly_target(obj):
        # TODO: Return the original weekly target of the goal
        return 0

    def new_weekly_target(obj):
        # TODO: Return the weekly target set during goal edit
        return 0

    def original_goal_target(obj):
        # TODO: Return the original goal target
        return 0

    def new_goal_target(obj):
        # TODO: Return the new goal target set during the goal edit
        return 0

    def date_goal_edited(obj):
        # TODO: Return the date the goal was edited
        return 0

    def num_weekly_target_edited(obj):
        # TODO: Return the number of times the user has edited their weekly target
        return 0

    def num_weekly_target_increased(obj):
        # TODO: Return the number of times weekly target increased
        return 0

    def num_weekly_target_decreased(obj):
        # TODO: Return the number of times weekly target decreased
        return 0

    def weekly_target_original(obj):
        # TODO: Return the original (first) weekly target
        return 0

    def num_goal_target_edited(obj):
        # TODO: Return the number of times the goals target was edited
        return 0

    def num_goal_target_increased(obj):
        # TODO: Return the number of times goal target increased
        return 0

    def num_goal_target_decreased(obj):
        # TODO: Return the number of times goal target decreased
        return 0

    def goal_weeks_initial(obj):
        # TODO: Return the initial number of goal weeks (When goal was set)
        return 0

    def goal_weeks_current(obj):
        # TODO: Return the current number of weeks for the goal
        # Current weeks left or total weeks of goal??
        return 0

    def date_achieved(obj):
        """Returns the date of the transaction that caused the user to achieve their goal"""
        transactions = GoalTransaction.objects.filter(goal=obj)

        amount_saved = 0
        target = obj.target

        for t in transactions:
            amount_saved += t.value

            if amount_saved >= target:
                return t.date

        return None

    def date_deleted(obj):
        # TODO: Implement date deleted field on Goal model
        return 0


class UserReport:

    fields = ()

    @classmethod
    def export_csv(cls, stream):
        profiles = Profile.objects.all()
        writer = csv.writer(stream)
        writer.writerow(cls.fields)

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
                # cls.num_6_week_on_track_badges(profile),
                cls.num_8_week_on_track_badges(profile),
                cls.num_goal_reached_badges(profile),
                cls.num_budget_created_badges(profile),
                cls.num_budget_revision_badges(profile),
                # cls.num_challenge_participation_badges(profile),
                cls.highest_streak_earned(profile),
                cls.total_streak_and_ontrack_badges(profile),
                cls.baseline_survey_complete(profile),
                cls.ea_tool1_completed(profile),
                cls.ea_tool2_completed(profile),
                cls.endline_survey_completed(profile)
                # cls.total_streaks_earned(profile),
                # cls.num_quiz_complete_badges(profile),
                # cls.num_5_challenges_completed_badge(profile),
                # cls.num_5_quizzes_badges(profile),
                # cls.num_perfect_score_badges(profile),
            ]

            writer.writerow([getattr(profile, field) for field in cls.fields] + data)

    def google_analytics_uuid(obj):
        return 0

    def number_of_goals(obj):
        user = obj.user
        return Goal.objects.filter(user=user).count()

    def total_badges_earned(obj):
        user = obj.user
        return Badge.objects.filter(user=user).count()

    def num_first_goal_created_badges(obj):
        # TODO: Count number of First Goal Created badges
        return 0

    def num_first_savings_created_badges(obj):
        # TODO: Count number of First Savings Created badges
        return 0

    def num_halfway_badges(obj):
        # TODO: Count number of Halfway badges
        return 0

    def num_one_week_left_badges(obj):
        # TODO: Count number of One Week Left badges
        return 0

    def num_2_week_streak_badges(obj):
        # TODO: Count number of 2 Week Streak badges
        return 0

    def num_4_week_streak_badges(obj):
        # TODO: Count number of 4 week streak badges
        return 0

    def num_6_week_streak_badges(obj):
        # TODO: Count number of 6 week streak badges
        return 0

    def num_2_week_on_track_badges(obj):
        # TODO: Count number of 2 Week on Track badges
        return 0

    def num_4_week_on_track_badges(obj):
        # TODO: Count number of 4 week on Track badges
        return 0

    def num_6_week_on_track_badges(obj):
        # TODO: Count number of 6 week on Track badges
        return 0

    def num_8_week_on_track_badges(obj):
        # TODO: Count number of 8 week on Track badges
        return 0

    def num_goal_reached_badges(obj):
        # TODO: Count number of goal reached badges
        return 0

    def num_challenge_participation_badges(obj):
        # TODO: Count number of Challenge Participation badges
        return 0

    def highest_streak_earned(obj):
        # TODO: Return the users highest streak
        return 0

    def total_streak_and_ontrack_badges(obj):
        # TODO: Return the total number of on-track and streak badges
        return 0

    def total_streaks_earned(obj):
        # TODO: Return the number of streaks earned
        return 0

    def num_quiz_complete_badges(obj):
        # TODO: Return the number of Quiz Completed badges (Not implemented)
        return 0

    def num_5_challenges_completed_badge(obj):
        # TODO: Return the number of 5 Challenges badges (Not implemented)
        return 0

    def num_5_quizzes_badges(obj):
        # TODO: Return the number of 5 Quizzes badges (Not implemented)
        return 0

    def num_perfect_score_badges(obj):
        # TODO: Return the number of Perfect Score badges (Not implemented)
        return 0

    def num_budget_created_badges(obj):
        # TODO: Return the number of Budget Created badges (Not implemented)
        return 0

    def num_budget_revision_badges(obj):
        # TODO: Return the number of Budget Revision badges (Not implemented)
        return 0

    def baseline_survey_complete(obj):
        # TODO: Return True/False if a user has completed the baseline survey
        return False

    def ea_tool1_completed(obj):
        # TODO: Return true/False if a user has completed the EA Tool 1 survey
        return False

    def ea_tool2_completed(obj):
        # TODO: Return true/False if a user has completed the EA Tool 2 survey (Not implemented)
        return False

    def endline_survey_completed(obj):
        # TODO: Return true/False if a user has completed the endline survey (Not implemented)
        return False


class SavingsReport:

    fields = ()

    @classmethod
    def export_csv(cls, stream):
        goals = Goal.objects.all()
        writer = csv.writer(stream)
        writer.writerow(cls.fields)

        writer.writerow(('username', 'goal_name', 'goal_target', 'goal_weekly_target', 'goal_weeks', 'goal_start_date',
                         'transaction_deposit', 'transaction_value', 'transaction_date', 'weeks_from_start',
                         'goal_balance'))

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

                writer.writerow([getattr(goal, field) for field in cls.fields] + data)

    def weekly_target_at_transaction(obj):
        return obj.goal.weekly_target


class SummaryDataPerChallenge:

    fields = ()

    @classmethod
    def export_csv(cls, stream):
        challenges = Challenge.objects.all()
        writer = csv.writer(stream)
        writer.writerow(cls.fields)

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

            writer.writerow([getattr(challenge, field) for field in cls.fields] + data)

    def total_challenge_completions(self, challenge):
        return Participant.objects.filter(challenge=challenge).count()

    def total_users_in_progress(self, challenge):
        # TODO: Return total users in progress
        return 0

    def no_response_total(self, challenge):
        # TODO: Return the number of no responses
        return 0


class SummaryDataPerQuiz:

    fields = ()

    @classmethod
    def export_csv(cls, stream):
        challenges = Challenge.objects.filter(type=Challenge.CTP_QUIZ)
        writer = csv.writer(stream)
        writer.writerow(cls.fields)

        for challenge in challenges:
            quiz_question = QuizQuestion.objects.filter(challenge=challenge)
            question_options = QuestionOption.objects.filter(question=quiz_question)
            data = [
                challenge.name,
                quiz_question.text,
                question_options.count(),
                cls.average_number_question_attempts(quiz_question, question_options)
            ]

            writer.writerow([getattr(challenge, field) for field in cls.fields] + data)

    def average_number_question_attempts(self, question, options):
        # TODO: Return the average number of attempts per question option
        return 0


class ChallengeReportPhoto:

    fields = ()

    @classmethod
    def export_csv(cls, stream):
        challenges = Challenge.objects.filter(type=Challenge.CTP_PICTURE)

        writer = csv.writer(stream)
        writer.writerow(cls.fields)

        for challenge in challenges:
            participant = Participant.objects.filter(challenge=challenge)
            profile = Profile.objects.get(user=participant.user)

            data = [
                participant.user.username,
                participant.user.first_name,
                profile.mobile,
                participant.user.email,
                profile.gender,
                profile.age,
                # user type
                participant.date_created,
                # call to action something, waiting feedback
            ]

            writer.writerow([getattr(challenge, field) for field in cls.fields] + data)

class ChallengeReportQuiz:

    fields = ()

    @classmethod
    def export_csv(cls, stream):
        challenges = Challenge.objects.filter(type=Challenge.CTP_QUIZ)

        writer = csv.writer(stream)
        writer.writerow(cls.fields)

        for challenge in challenges:
            participant = Participant.objects.filter(challenge=challenge)
            profile = Profile.objects.get(user=participant.user)

            quiz_question = QuizQuestion.objects.get(challenge=challenge)
            question_option = QuestionOption.objects.filter(question=quiz_question)

            data = [
                participant.user.username,
                participant.user.first_name,
                profile.mobile,
                participant.user.email,
                profile.gender,
                profile.age,
                # user type
                participant.date_created,
                cls.quiz_question_data(participant, quiz_question, question_option)
            ]

            writer.writerow([getattr(challenge, field) for field in cls.fields] + data)

    def quiz_question_data(self, question, option, participant):
        data = [
            question.text,
            0, # Number of attempts

        ]

        return data