import os
import subprocess
import shutil
import random
import csv

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from django.utils.translation import ugettext as _

REPORT_GENERATION_TIMEOUT = 60

SUCCESS_MESSAGE_EMAIL_SENT = _('Report and password has been sent in an email.')
ERROR_MESSAGE_NO_EMAIL = _('No email address associated with this account.')
ERROR_MESSAGE_DATA_CLEANUP = _('Report generation ran during data cleanup - try again')


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


def pass_zip_encrypt_email(user_email, export_name, unique_time):
    """Generate a password, zip and encrypt the report, if nothing goes wrong email the password"""

    password = password_generator()
    result, err_message = zip_and_encrypt(export_name, unique_time, password)

    if not result:
        return False, err_message

    if user_email is None or user_email is '':
        return False, ERROR_MESSAGE_NO_EMAIL

    send_password_email(user_email, export_name, unique_time, password)

    return True, SUCCESS_MESSAGE_EMAIL_SENT


def send_password_email(email, export_name, unique_time, password):
    subject = 'Dooit Date Export: ' + str(timezone.now().date())

    send_to = email

    file_name = export_name + unique_time + '.zip'

    if os.path.isfile(settings.SENDFILE_ROOT + '\\' + file_name):
        email = EmailMessage(
            subject,
            'Attached report: ' + file_name + '\nPassword: ' + password,
            settings.DEFAULT_FROM_EMAIL,
            [send_to],
        )

        email.attach_file(settings.SENDFILE_ROOT + '\\' + file_name, 'application/zip')

        email.send()
