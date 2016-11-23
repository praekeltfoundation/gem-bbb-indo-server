
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from .models import Challenge


class ChallengeAdmin(ModelAdmin):
    model = Challenge
    add_to_settings_menu = False
    inspect_view_fields = ('name',)
    list_display = ('name', 'type', 'state', 'activation_date', 'deactivation_date')
    list_filter = ('name', 'type', 'state')
    search_fields = ('name',)


modeladmin_register(ChallengeAdmin)
