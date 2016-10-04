from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from .models import User, Profile


class ProfileInlineForm(admin.StackedInline):
    model = Profile
    max_num = 1
    can_delete = False


class UserProfileAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets
    inlines = [ProfileInlineForm]


admin.site.unregister(User)
admin.site.register(User, UserProfileAdmin)
