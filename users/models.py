from django.db import models

from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    mobile = models.CharField(verbose_name='Mobile Number', blank=False, unique=True)
    email = models.CharField(verbose_name='E-mail Address', blank=True, null=True)
    join_date = models.DateTimeField(verbose_name='Date Joined', blank=False)
    country = models.CharField(verbose_name="Country", max_length=50, blank=False)
    area = models.CharField(verbose_name="Local Area", max_length=50, blank=True)
    city = models.CharField(verbose_name="City", max_length=50, blank=True)

    unique_token_expiry = models.DateTimeField(
        verbose_name="Unique Login Token Expiry",
        null=True,
        blank=True
    )

    pass_reset_token = models.CharField(
        verbose_name="Password Reset Token",
        max_length=500,
        blank=True,
        null=True
    )

    pass_reset_token_expiry = models.DateTimeField(
        verbose_name="Password Reset Token Expiry",
        null=True,
        blank=True
    )


# System administrator with access to the admin console
class SystemAdministrator(CustomUser):
    class Meta:
        verbose_name = "System Administrator"
        verbose_name_plural = "System Administrators"

    def save(self, *args, **kwargs):
        self.is_staff = True
        self.is_superuser = True
        super(SystemAdministrator, self).save(*args, **kwargs)


# Users registered by mobile phone
class RegUser(CustomUser):
    class Meta:
        verbose_name = 'Regular User'
        verbose_name_plural = 'Regular Users'

    name = models.CharField('Name', blank=False)
    last_active_date = models.DateField('Last Active', null=True, blank=True)