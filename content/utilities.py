import subprocess
import shutil
import random
import csv
import datetime


def zip_and_encrypt(data):
    filename = str(datetime.datetime.now().date())
    with open(filename + '.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar=',', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(data)

    exe = shutil.which('7z')

    password = password_generator()
    output_name = filename
    filename = './' + filename + '.csv'

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
    with subprocess.Popen(command, stderr=subprocess.PIPE) as proc:
        print(proc.stderr.read())


def password_generator():
    s = "abcdefghijklmnopqrstuvwxyz01234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()?"
    password_length = 8
    p = "".join(random.sample(s, password_length))
    print('Password: %s' % p)
    return p

# import subprocess
# import shutil
#
#
# def zip_and_encrypt():
#     exe = shutil.which('7z')
#
#     command = [
#         exe,
#         'a', 'test.zip',
#         '-tzip',  # Type Zipfile
#         '-mem=AES256',  # Required because Zip file format
#         '-mx9',  # Ultra compression
#         '-pSECRET',
#         'eggs.csv',
#     ]
#     with subprocess.Popen(command, stderr=subprocess.PIPE) as proc:
#         print(proc.stderr.read())
