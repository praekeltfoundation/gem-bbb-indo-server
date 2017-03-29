# -*- coding: utf-8 -*-
import os

from celery.task import task

from django.conf import settings

from content.analytics_api import get_report, print_response, initialize_analytics_reporting
from content.celery import app


@task(ignore_result=False, max_retries=10, default_retry_delay=10)
def just_print():
    print("Just Print")


@app.task(ignore_result=True, max_retries=10, default_retry_delay=10)
def remove_report_archives():
    print("Starting removal")
    for filename in os.listdir(settings.SENDFILE_ROOT):
        if filename.endswith('.csv') or filename.endswith('.zip'):
            print("Removing: " + settings.SENDFILE_ROOT + '\\' + filename)
            os.remove(settings.SENDFILE_ROOT + '\\' + filename)


@app.task(ignore_result=True, max_retries=10, default_retry_delay=10)
def ga_task_handler():
    print("Starting GA connection")
    analytics = initialize_analytics_reporting()
    response = get_report(analytics)
    print_response(response)
    print("Finished GA connection")
