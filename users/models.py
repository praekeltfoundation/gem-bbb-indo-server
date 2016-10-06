from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import RegexValidator
from django.utils.encoding import python_2_unicode_compatible


# proxy managers
class RegUserManager(models.Manager):
    def get_queryset(self):
        return super(RegUserManager, self).get_queryset().filter(is_staff=False, is_superuser=False)

    def create(self, **kwargs):
        kwargs.update({'is_staff': False, 'is_superuser': False})
        return super(RegUserManager, self).create(**kwargs)


class SysAdminUserManager(models.Manager):
    def get_queryset(self):
        return super(SysAdminUserManager, self).get_queryset().filter(is_staff=True, is_superuser=True)

    def create(self, **kwargs):
        kwargs.update({'is_staff': True, 'is_superuser': True})
        return super(SysAdminUserManager, self).create(**kwargs)


# Users registered by mobile phone
class RegUser(User):
    objects = RegUserManager()

    class Meta:
        proxy = True
        verbose_name = 'Regular user'
        verbose_name_plural = 'Regular users'


# System administrators
class SysAdminUser(User):
    objects = SysAdminUserManager()

    class Meta:
        proxy = True
        verbose_name = 'System administrator'
        verbose_name_plural = 'System administrators'


# user profile information
@python_2_unicode_compatible
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    mobile = models.CharField(validators=[mobile_regex], max_length=15, blank=True)

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return self.mobile


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()