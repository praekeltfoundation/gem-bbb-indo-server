import csv

from .models import Goal


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

    def get_username(obj):
        return obj.user.username

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
