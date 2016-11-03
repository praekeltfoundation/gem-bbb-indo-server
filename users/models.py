from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from rest_framework.authtoken.models import Token

from .storage import ProfileImgStorage


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
        verbose_name = _('regular user')
        verbose_name_plural = _('regular users')


# System administrators
class SysAdminUser(User):
    objects = SysAdminUserManager()

    class Meta:
        proxy = True
        verbose_name = _('system administrator')
        verbose_name_plural = _('system administrators')


def get_profile_image_filename(instance, filename):
    return '/'.join(('profile', '{}-{}'.format(instance.user.pk, filename)))


# user profile information
@python_2_unicode_compatible
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."))
    mobile = models.CharField(validators=[mobile_regex], max_length=15, blank=True)
    profile_image = models.ImageField(upload_to=get_profile_image_filename,
                                      storage=ProfileImgStorage(),
                                      null=True,
                                      blank=True)

    class Meta:
        verbose_name = _('profile')
        verbose_name_plural = _('profiles')

    def __str__(self):
        return self.mobile


def reset_token(sender, instance, **kwargs):
    """Invalidates a token when a user's password is changed."""
    new_password = instance.password

    try:
        old_password = User.objects.get(pk=instance.pk).password
    except User.DoesNotExist:
        old_password = None

    if new_password != old_password:
        Token.objects.filter(user=instance).delete()


# Django signals do not consider subclasses of the sender. When connected using User, RegUser will not trigger the
# handler. Each model is registered separately.
MODEL_CLASSES = (User, RegUser, SysAdminUser)
for model in MODEL_CLASSES:
    pre_save.connect(reset_token, model)


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()
