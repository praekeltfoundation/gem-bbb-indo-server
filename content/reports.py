import csv

from users.models import Profile
from .models import Goal, Badge, BadgeSettings, UserBadge, GoalTransaction


class GoalReport:

    fields = ()

    @classmethod
    def export_csv(cls, stream):
        goals = Goal.objects.all()
        writer = csv.writer(stream)
        writer.writerow(cls.fields)

        for goal in goals:

            data = [cls.get_username(goal),
                    goal.prototype,
                    goal.name,
                    goal.target,
                    goal.value,
                    goal.progress,
                    goal.weekly_average,
                    goal.weeks,
                    goal.weeks_left,
                    cls.num_weeks_saved(goal),
                    cls.num_weeks_saved_below(goal),
                    cls.num_weeks_saved_above(goal),
                    cls.num_weeks_not_saved(goal),
                    cls.num_withdrawals(goal),
                    cls.num_weekly_target_edited(goal),
                    cls.num_weekly_target_increased(goal),
                    cls.num_goal_target_decreased(goal),
                    cls.weekly_target_original(goal),
                    goal.weekly_target,
                    cls.num_goal_target_edited(goal),
                    cls.num_goal_target_increased(goal),
                    cls.num_goal_target_decreased(goal),
                    cls.goal_weeks_initial(goal),
                    cls.goal_weeks_current(goal),
                    goal.start_date,
                    goal.is_goal_reached,
                    cls.date_achieved(goal),
                    goal.is_active,
                    cls.date_deleted(goal)]
            writer.writerow([getattr(goal, field) for field in cls.fields] + data)

    @classmethod
    def get_username(cls, obj):
        return obj.user.username

    @staticmethod
    def num_weeks_saved(obj):
        # TODO: Return number of weeks that the user has saved
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
        # TODO: Return the number of times the user has withdrawn
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
        # TODO: Return the date the goal was achieved
        return 0

    def date_deleted(obj):
        # TODO: Implement date deleted field on Goal model
        return 0


class UserReport():

    fields= ()

    @classmethod
    def export_csv(cls, stream):
        profiles = Profile.objects.all()
        writer = csv.writer(stream)
        writer.writerow(cls.fields)

        for profile in profiles:
            data = [
                cls.google_analytics_uuid(profile),
                profile.user.username,
                profile.user.first_name,
                profile.mobile,
                profile.user.email,
                profile.gender,
                profile.age,
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
                cls.num_6_week_on_track_badges(profile),
                cls.num_8_week_on_track_badges(profile),
                cls.num_goal_reached_badges(profile),
                cls.num_challenge_participation_badges(profile),
                cls.highest_streak_earned(profile),
                cls.total_streaks_earned(profile),
                cls.num_quiz_complete_badges(profile),
                cls.num_5_challenges_completed_badge(profile),
                cls.num_5_quizzes_badges(profile),
                cls.num_perfect_score_badges(profile),
                cls.num_budget_created_badges(profile),
                cls.num_budget_revision_badges(profile),
                cls.baseline_survey_complete(profile),
                cls.ea_tool1_completed(profile),
                cls.ea_tool2_completed(profile),
                cls.endline_survey_completed(profile)
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

        for goal in goals:
            data = [
                goal.user.username,
                goal.name,
                goal.target,
                goal.weekly_target,
                goal.weeks,
                goal.start_date,
                [t.value for t in GoalTransaction.objects.filter(goal=goal)],

            ]

            writer.writerow([getattr(goal, field) for field in cls.fields] + data)