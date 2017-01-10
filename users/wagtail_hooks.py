
from django.utils.translation import ugettext_lazy as _
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from .models import Profile

# ============ #
# User Profile #
# ============ #

class Profile(ModelAdmin):
    model = Profile
    # Translators: CMS menu name
    menu_label = _('Profile')
    menu_icon = 'folder-open-inverse'
    menu_order = 300
    list_display = ('age', 'mobile', 'gender')
    add_to_settings_menu = False

modeladmin_register(Profile)

