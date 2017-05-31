import os
import subprocess
import shutil
import random
import csv

from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.utils import timezone

from content.celery import app

REPORT_GENERATION_TIMEOUT = 60


def create_csv(filename):
    """Remove old CSV for the impending export"""

    if os.path.isfile(filename):
        os.remove(filename)


def append_to_csv(data, csvfile):
    """Append new records for the current export"""

    writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(data)


def zip_and_encrypt(export_name, unique_time, password):

    exe = shutil.which('7z')

    output_name = settings.SENDFILE_ROOT + '\\' + export_name + unique_time + '.zip'

    filename = settings.SENDFILE_ROOT + '\\' + export_name + unique_time + '.csv'

    command = [
        exe,
        'a',
        output_name,
        '-tzip',  # Type Zipfile
        '-mem=AES256',  # Required because Zip file format
        '-mx9',  # Ultra compression
        '-p' + password,
        filename,
    ]

    try:
        subprocess.call(command, stderr=subprocess.PIPE, timeout=REPORT_GENERATION_TIMEOUT)
    # except TimeoutError:
    except subprocess.TimeoutExpired:
        return False, 'Timeout'

    return True, "Report created and archived successfully."

    # with subprocess.Popen(command, stderr=subprocess.PIPE, timeout=REPORT_GENERATION_TIMEOUT) as proc:
    #     print(proc.stderr.read())


def password_generator():
    sequence = "abcdefghijklmnopqrstuvwxyz01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()?"
    password_length = 8
    password = "".join(random.sample(sequence, password_length))

    return password


@app.task()
def send_password_email(request, export_name, unique_time, password):
    subject = 'Dooit Date Export: ' + str(timezone.now().date())

    send_to = request.user.email
    file_name = export_name + unique_time + '.zip'

    send_mail(
        subject=subject,
        message='Password for ' + file_name + ': ' + password,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[send_to],

        fail_silently=False
    )

    if os.path.isfile(settings.SENDFILE_ROOT + '\\' + file_name):
        email = EmailMessage(
            subject,
            'Attached report: ' + file_name,
            settings.DEFAULT_FROM_EMAIL,
            [send_to],
        )

        email.attach_file(settings.SENDFILE_ROOT + '\\' + file_name, 'application/zip')

        email.send()
    else:
        pass
