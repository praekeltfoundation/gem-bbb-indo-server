
from django.contrib import admin
from django.utils.translation import ugettext as _
from django import forms
import wagtail.contrib.modeladmin.options as wagadmin
from import_export import fields
from import_export import resources
from import_export.admin import ExportMixin

from users.models import Profile
from .models import Challenge, FreeTextQuestion, Participant, PictureQuestion, QuestionOption, QuizQuestion, Badge, \
    BadgeSettings, UserBadge
from .models import Goal, GoalTransaction
from .models import Tip, TipFavourite


# class UserResource(resources.ModelResource):
#     email = fields.Field()
#     username = fields.Field()
#     full_name = fields.Field()
#
#     class Meta:
#         model = Profile
#         fields = ('mobile', 'gender', 'age',)
#         export_order = ('username', 'full_name', 'mobile', 'email', 'gender', 'age',)
#
#     def dehydrate_username(self, user_profile):
#         if user_profile.user.username is not None:
#             return user_profile.user.username
#         else:
#             return ""
#
#     def dehydrate_email(self, user_profile):
#         if user_profile.user.email is not None:
#             return user_profile.user.email
#         else:
#             return ""
#
#     def dehydrate_full_name(self, user_profile):
#         if user_profile.user.last_name is not None:
#             return user_profile.user.get_full_name()
#         else:
#             return ""
#
#
# @admin.register(Profile)
# class UserAdmin(ExportMixin, admin.ModelAdmin):
#     resource_class = UserResource


class QuestionOptionInline(admin.StackedInline):
    model = QuestionOption
    max_num = 5
    extra = 0
    fk_name = 'question'


class QuestionInline(admin.StackedInline):
    model = QuizQuestion
    max_num = 10
    extra = 0

class ParticipantResource(resources.ModelResource):
    user_id = fields.Field()
    challenge_name = fields.Field()
    free_text_question = fields.Field()
    free_text_answers = fields.Field()
    photo_upload = fields.Field()
    date_completed = fields.Field()

    class Meta:
        model = Participant

        fields = ('user_id',
                  'challenge_name',
                 # 'free_text_question',
                 # 'free_text_answers',
                 # 'photo_upload',
                 'date_completed'
                 )
        export_order = ('user_id',
                        'challenge_name',
                        # 'free_text_question',
                        # 'free_text_answers',
                        # 'photo_upload',
                        'date_completed'
                        )

    def dehydrate_user_id(self, participant):
        return participant.user.id

    def dehydrate_challenge_name(self, participant):
        return participant.challenge.name

    def dehydrate_free_text_question(self, participant):
        pass

    def dehydrate_free_text_answers(self, participant):
        pass

    def dehydrate_photo_upload(self, participant):
        pass

    def dehydrate_date_completed(self, participant):
        if participant.date_completed is not None:
            return participant.date_completed
        else:
            return ""

@admin.register(Participant)
class ParticipantAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = ParticipantResource


class ChallengeAdminForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super(ChallengeAdminForm, self).clean()
        if self.instance is not None:
            challenge = self.instance
            if challenge.state == Challenge.CST_PUBLISHED and \
                    Participant.objects.filter(challenge_id=challenge.id).count() > 0:
                raise forms.ValidationError(
                    # Translators: Error message on CMS
                    _('Editing of challenges is disallowed when participants have already answered.'),
                    code='challenge_active_error'
                )
        return cleaned_data


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    form = ChallengeAdminForm
    fieldsets = [
        (None,
         {'fields': ['name', 'type', 'state', 'end_processed']}),
        ('Dates',
         {'fields': ['activation_date', 'deactivation_date']}),
        ('Images',
         {'fields': ['picture']}),
    ]
    list_display = ('name', 'type', 'state', 'activation_date', 'deactivation_date')
    list_filter = ('name', 'type', 'state')
    inlines = [QuestionInline]


@admin.register(FreeTextQuestion)
class QuestionFreeTextAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,
         {'fields': ['challenge', 'text']})
    ]
    list_display = ('challenge', 'text')
    list_filter = ('challenge', 'text')


class QuestionAdminForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super(QuestionAdminForm, self).clean()
        if self.instance is not None and self.instance.challenge is not None:
            challenge = self.instance.challenge
            if challenge.state == Challenge.CST_PUBLISHED and \
                    Participant.objects.filter(challenge_id=challenge.id).count() > 0:
                raise forms.ValidationError(
                    _('Editing of challenges is disallowed when participants have already answered.'),
                    code='challenge_active_error'
                )
        return cleaned_data


@admin.register(QuizQuestion)
class QuestionAdmin(admin.ModelAdmin):
    form = QuestionAdminForm
    fieldsets = [
        (None,
         {'fields': ['challenge', 'text', 'hint']})
    ]
    list_display = ('challenge', 'text')
    list_filter = ('challenge', 'text')
    inlines = [QuestionOptionInline]


class QuestionOptionAdminForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super(QuestionOptionAdminForm, self).clean()
        if self.instance is not None and self.instance.question is not None and \
                self.instance.question.challenge is not None:
            challenge = self.instance.question.challenge
            if challenge.state == Challenge.CST_PUBLISHED and \
                    Participant.objects.filter(challenge_id=challenge.id).count() > 0:
                print(challenge.id)
                raise forms.ValidationError(
                    _('Editing of challenges is disallowed when participants have already answered.'),
                    code='challenge_active_error'
                )
        return cleaned_data


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    form = QuestionOptionAdminForm
    fieldsets = [
        (None,
         {'fields': ['question', 'picture', 'text', 'correct']})
    ]
    list_display = ('question', 'text', 'correct')
    list_filter = ('question', 'text', 'correct')


@admin.register(PictureQuestion)
class QuestionPictureAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,
         {'fields': ['challenge', 'text']})
    ]
    list_display = ('challenge', 'text')
    list_filter = ('challenge', 'text')


class TipAdmin(wagadmin.ModelAdmin):
    model = Tip
    menu_order = 200
    list_display = ('title', 'live', 'owner', 'first_published_at')
    list_filter = ('title', 'live', 'owner', 'first_published_at')


@admin.register(TipFavourite)
class TipFavouriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'tip', 'state')
    list_filter = ('user', 'tip', 'state')


class GoalTransactionInline(admin.StackedInline):
    model = GoalTransaction
    max_num = 15
    extra = 0


class GoalResource(resources.ModelResource):
    user_id = fields.Field()
    number_of_goals = fields.Field()
    name_of_goal = fields.Field()
    goal_total_amount = fields.Field()
    amount_saved_to_date = fields.Field()
    goal_transactions = fields.Field()
    weekly_savings_amount = fields.Field()
    total_weeks_until_goal = fields.Field()
    # number_of_times_edited = fields.Field()
    # TODO 1: Each edits data (Amount and weeks left until goal)
    goal_deleted = fields.Field()
    # date_deleted = fields.Field()
    percentage_achieved = fields.Field()
    goal_achieved = fields.Field()
    # date_achieved = fields.Field()
    goal_created_date = fields.Field()
    # num_weeks_saved = fields.Field()
    # num_weeks_saved_on_target = fields.Field()
    # num_weeks_saved_below_target = fields.Field()
    # num_weeks_not_saved = fields.Field()

    class Meta:
        model = Goal
        fields = ('user_id',
                  'number_of_goals',
                  'name_of_goal',
                  'goal_total_amount',
                  'amount_saved_to_date',
                  'goal_transactions',
                  'weekly_savings_amount',
                  'total_weeks_until_goal',
                  # 'number_of_times_edited',
                  # todo1
                  'goal_deleted',
                  # 'date_deleted',
                  'percentage_achieved',
                  'goal_achieved',
                  # 'date_achieved',
                  'goal_created_date',
                  # 'num_weeks_saved',
                  # 'num_weeks_saved_on_target',
                  # 'num_weeks_saved_below_target',
                  # 'num_weeks_not_saved',
                  )
        export_order = ('user_id',
                        'number_of_goals',
                        'name_of_goal',
                        'goal_total_amount',
                        'amount_saved_to_date',
                        'goal_transactions',
                        'weekly_savings_amount',
                        'total_weeks_until_goal',
                        # 'number_of_times_edited',
                        # todo1
                        'goal_deleted',
                        # 'date_deleted',
                        'percentage_achieved',
                        'goal_achieved',
                        # 'date_achieved',
                        'goal_created_date',
                        # 'num_weeks_saved',
                        # 'num_weeks_saved_on_target',
                        # 'num_weeks_saved_below_target',
                        # 'num_weeks_not_saved',
                        )

    def dehydrate_user_id(self, goal):
        return goal.user.id

    def dehydrate_number_of_goals(self, goal):
        return goal.number_of_goals_per_user(goal.user)

    def dehydrate_name_of_goal(self, goal):
        return goal.name

    def dehydrate_goal_total_amount(self, goal):
        return goal.target

    def dehydrate_amount_saved_to_date(self, goal):
        return goal.progress

    def dehydrate_goal_transactions(self, goal):
        users_goal_transactions = GoalTransaction.objects.filter(goal=goal)
        all_transactions = ""
        for transaction in users_goal_transactions:
            all_transactions += "{" + str(transaction) + "}"

        return all_transactions

    def dehydrate_weekly_savings_amount(self, goal):
        return goal.weekly_target

    def dehydrate_total_weeks_until_goal(self, goal):
        return goal.weeks_left

    # def dehydrate_number_of_times_edited(self, goal):
    #     return goal.number_of_times_edited

    # dehydrate for 2 - each edits data

    def dehydrate_goal_deleted(self, goal):
        return goal.is_active

    # def dehydrate_date_deleted(self, goal):
    #     return goal.deleted_date

    def dehydrate_percentage_achieved(self, goal):
        return goal.progress

    def dehydrate_is_goal_achieved(self, goal):
        return goal.is_goal_reached

    # def dehydrate_date_achieved(self, goal):
    #     return goal.date_achieved

    def dehydrate_goal_created_date(self, goal):
        return goal.start_date

    # def dehydrate_num_weeks_saved(self, goal):
    #     pass
    #
    # def dehydrate_num_weeks_saved_on_target(self, goal):
    #     pass
    #
    # def dehydrate_num_weeks_saved_below_target(self, goal):
    #     pass
    #
    # def dehydrate_num_weels_not_saved(self, goal):
    #     pass


@admin.register(Goal)
class GoalAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = GoalResource
    readonly_fields = ('value', 'week_count', 'week_count_to_now', 'weeks_left', 'days_left', 'weekly_target',
                       'weekly_average',)
    fieldsets = (
        (None, {
            'fields': ('name', 'state', 'start_date', 'end_date', 'target', 'image', 'user')
        }),
        ('Calculated', {
            'fields': ('value', 'week_count', 'week_count_to_now', 'weeks_left', 'days_left', 'weekly_target',
                       'weekly_average',)
        })
    )
    list_display = ('name', 'user', 'target', 'value')
    list_filter = ('user',)
    inlines = (GoalTransactionInline,)


class UserBadgeResource(resources.ModelResource):
    user_id = fields.Field()
    total_badges_earned = fields.Field()
    total_badges_earned_by_type = fields.Field()
    highest_streak_earned = fields.Field()
    # total_streaks_earned = fields.Field()

    class Meta:
        model = UserBadge
        fields = ('user_id',
                  'total_badges_earned',
                  'total_badges_earned_by_type',
                  'highest_streak_earned',
                  # 'total_streaks_earned',
                  )
        export_order = ('user_id',
                        'total_badges_earned',
                        'total_badges_earned_by_type',
                        'highest_streak_earned',
                        # 'total_streaks_earned',
                        )

    def dehydrate_user_id(self, badge):
        return badge.user_id

    def dehydrate_total_badges_earned(self, badge):
        return badge.number_of_badges_per_user(badge.user)

    def dehydrate_total_badges_earned_by_type(self, badge):
        all_badges = UserBadge.objects.filter(user=badge.user)
        badge_types = ""
        for b in all_badges:
            # TODO: Find a better way to export this variable length data - Create a JSON object for it?
            badge_types += "[" + b.badge.name + ", " + str(all_badges.count()) + "]"

        return badge_types

    def dehydrate_highest_streak_earned(self, badge):
        all_badges = UserBadge.objects.filter(user=badge.user)

        # TODO: Something like this to see the highest streak badge?
        for b in all_badges:
            if b.badge.name.endswith('!'):
                return "Two week streak badge"
            elif b.badge.name.endswith('4'):
                return "Four week streak badge"
            elif b.badge.name.endswith("6"):
                return "6 week streak badge"

    def dehydrate_total_streaks_earned(self, badge):
        pass


@admin.register(UserBadge)
class UserBadgeAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = UserBadgeResource
