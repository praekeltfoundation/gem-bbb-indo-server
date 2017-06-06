# -*- coding: utf-8 -*-
import os

from celery.task import task

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from content.analytics_api import get_report, connect_ga_to_user, initialize_analytics_reporting
from content.celery import app
from content.utilities import password_generator, zip_and_encrypt, send_password_email

SUCCESS_MESSAGE_EMAIL_SENT = _('Report and password has been sent in an email.')
ERROR_MESSAGE_NO_EMAIL = _('No email address associated with this account.')
ERROR_MESSAGE_DATA_CLEANUP = _('Report generation ran during data cleanup - try again')


@task(ignore_result=False, max_retries=10, default_retry_delay=10)
def just_print():
    print("Just Print")


@app.task(ignore_result=True, max_retries=10, default_retry_delay=10)
def remove_report_archives():
    print("Starting removal")
    for filename in os.listdir(settings.SENDFILE_ROOT):
        if filename.endswith('.csv') or filename.endswith('.zip'):
            try:
                os.remove(settings.SENDFILE_ROOT + '\\' + filename)
            except FileNotFoundError:
                # Do nothing as there is no file to delete, name has changed
                pass


@app.task(ignore_result=True, max_retries=10, default_retry_delay=10)
def ga_task_handler():
    print("Starting GA connection")
    analytics = initialize_analytics_reporting()
    response = get_report(analytics)
    connect_ga_to_user(response)
    print("Finished GA connection")


@task(name="pass_zip_encrypt_email_task")
def pass_zip_encrypt_email_task(request, export_name, unique_time):
    """Generate a password, zip and encrypt the report, if nothing goes wrong email the password"""

    password = password_generator()
    result, err_message = zip_and_encrypt(export_name, unique_time, password)

    if not result:
        return False, err_message

    if request.user.email is None or request.user.email is '':
        return False, ERROR_MESSAGE_NO_EMAIL

    send_password_email(request.user.email, export_name, unique_time, password)

    return True, SUCCESS_MESSAGE_EMAIL_SENT
