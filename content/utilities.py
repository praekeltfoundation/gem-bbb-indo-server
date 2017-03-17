import os
import secrets
import subprocess
import shutil
import random
import csv

from django.core.mail import send_mail
from django.utils import timezone

REPORT_GENERATION_TIMEOUT = 60


def create_csv(filename):
    """Remove old CSV for the impending export"""

    if os.path.isfile(filename):
        os.remove(filename)


def append_to_csv(data, csvfile):
    """Append new records for the current export"""

    writer = csv.writer(csvfile, delimiter=',', quotechar=',', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(data)

    # with open(filename, 'a', newline='') as csvfile:
    #     writer = csv.writer(csvfile, delimiter=',', quotechar=',', quoting=csv.QUOTE_MINIMAL)
    #     writer.writerow(data)


def zip_and_encrypt(request, filename):

    exe = shutil.which('7z')

    password = password_generator(request)
    output_name = filename + '.zip'
    filename = './' + filename

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
        subprocess.call(command, stderr=subprocess.PIPE)
    except subprocess.TimeoutExpired:
        pass

    # with subprocess.Popen(command, stderr=subprocess.PIPE, timeout=REPORT_GENERATION_TIMEOUT) as proc:
    #     print(proc.stderr.read())


def password_generator(request):
    sequence = "abcdefghijklmnopqrstuvwxyz01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()?"
    password_length = 8
    password = "".join(random.sample(sequence, password_length))
    # print('Password: %s' % password)
    send_password_email(request, password)
    return password


def send_password_email(request, password):
    subject = 'Dooit Date Export: ' + str(timezone.now().date())

    send_to = request.user.email

    if send_to is None or send_to is '':
        return

    send_mail(
        # Subject:
        subject,

        # Message:
        'Here is the password in plaintext:' + password,

        # From:
        'chdgrrtt@yahoo.com',

        # To:
        [send_to],

        fail_silently=False
    )
