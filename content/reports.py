import csv
from .models import Goal


class GoalReport:

    fields = ('name', 'target', 'value', 'weekly_target',)

    @classmethod
    def export_csv(cls, stream):
        goals = Goal.objects.all()
        writer = csv.writer(stream)
        writer.writerow(cls.fields)

        for goal in goals:
            writer.writerow([getattr(goal, field) for field in cls.fields])