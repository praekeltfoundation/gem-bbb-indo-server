from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from import_export import fields
from import_export import resources
from import_export.admin import ExportMixin

from .models import User, Profile, SysAdminUser, RegUser


class ProfileInlineForm(admin.StackedInline):
    model = Profile
    max_num = 1
    can_delete = False


class UserResource(resources.ModelResource):
    username = fields.Field()
    full_name = fields.Field()
    mobile = fields.Field()
    email = fields.Field()
    gender = fields.Field()
    age = fields.Field()


    class Meta:
        model = Profile
        fields = ('username', 'full_name', 'mobile', 'email', 'gender', 'age',)
        export_order = ('username', 'full_name', 'mobile', 'email', 'gender', 'age',)

    def dehydrate_username(self, user):
        if user.username is not None:
            return user.username
        else:
            return ""

    def dehydrate_full_name(self, user):
        if user.last_name is not None:
            return user.get_full_name()
        else:
            return ""

    def dehydrate_mobile(self, user):
        if user.profile.mobile is not None:
            return user.profile.mobile
        else:
            return ""

    def dehydrate_email(self, user):
        if user.email is not None:
            return user.email
        else:
            return ""

    def dehydrate_gender(self, user):
        if user.profile.gender is not None:
            return user.profile.gender
        else:
            return ""

    def dehydrate_age(self, user):
        if user.profile.age is not None:
            return user.profile.age
        else:
            return ""


class UserProfileAdmin(ExportMixin, UserAdmin):
    resource_class = UserResource
    fieldsets = UserAdmin.fieldsets
    inlines = [ProfileInlineForm]


@admin.register(SysAdminUser)
class SysAdminAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets
    inlines = [ProfileInlineForm]


@admin.register(RegUser)
class RegUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets
    inlines = [ProfileInlineForm]


admin.site.unregister(User)
admin.site.register(User, UserProfileAdmin)
