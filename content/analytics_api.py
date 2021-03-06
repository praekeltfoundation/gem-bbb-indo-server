from os import environ

from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

import httplib2

from users.models import CampaignInformation, UserUUID

SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
DISCOVERY_URI = ('https://analyticsreporting.googleapis.com/$discovery/rest')
VIEW_ID = environ.get('VIEW_ID', '')


def initialize_analytics_reporting():
    """Initializes an analyticsreporting service object.

    Returns:
      analytics an authorized analyticsreporting service object.
    """

    api_auth = dict([
        ("type", "service_account"),
        ("project_id", environ.get('PROJECT_ID', '')),
        ("private_key_id", environ.get('PRIVATE_KEY_ID', '')),
        ("private_key", environ.get('PRIVATE_KEY', '').replace('\\n', '\n')),
        ("client_email", environ.get('CLIENT_EMAIL', '')),
        ("client_id", environ.get('CLIENT_ID', '')),
        ("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
        ("token_uri", "https://accounts.google.com/o/oauth2/token"),
        ("auth_provider_x509_cert_url", "https://www.googleapis.com/oauth2/v1/certs"),
        ("client_x509_cert_url",
         "https://www.googleapis.com/robot/v1/metadata/x509/backend%40firebase-dooit-staging.iam.gserviceaccount.com"),
    ])

    try:
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(api_auth, scopes=SCOPES)
    except ValueError:
        print('Value error!')
        return

    http = credentials.authorize(httplib2.Http())

    # Build the service object.
    analytics = build('analytics', 'v4', http=http, discoveryServiceUrl=DISCOVERY_URI)

    return analytics


def get_report(analytics):
    # Use the Analytics Service Object to query the Analytics Reporting API V4.

    if analytics is None:
        print('Unable to initiate analytics')
        return

    return analytics.reports().batchGet(
        body={
            'reportRequests': [
                {
                    'viewId': VIEW_ID,
                    'dateRanges': [{'startDate': '90daysAgo', 'endDate': 'today'}],
                    'metrics': [{'expression': 'ga:newUsers'}],
                    'dimensions': [
                        {'name': 'ga:dimension1'},
                        {'name': 'ga:campaign'},
                        {'name': 'ga:source'},
                        {'name': 'ga:medium'},
                    ],
                }]
        }
    ).execute()


def connect_ga_to_user(response):
    """Reads the data return from the Analytics API
    Collects the campaign, source and medium information and creates a CampaignInformation
    linking to the user.
    """

    if response is None:
        return

    for report in response.get('reports', []):
        column_header = report.get('columnHeader', {})
        dimension_headers = column_header.get('dimensions', [])
        rows = report.get('data', {}).get('rows', [])

        for row in rows:
            dimensions = row.get('dimensions', [])

            user_uuid = None
            campaign = ''
            source = ''
            medium = ''

            try:
                user_uuid = UserUUID.objects.get(gaid=dimensions[0])
            except UserUUID.DoesNotExist:
                # No user with that GAID exists
                continue

            try:
                campaign = dimensions[1]
                source = dimensions[2]
                medium = dimensions[3]
            except IndexError:
                # GA returned incomplete data
                continue

            # print("C: " + campaign + "  S: " + source + "  M: " + medium)

            if CampaignInformation.objects.filter(user_uuid=user_uuid).exists():
                # If user's campaign information is not set, set to what GA has returned
                ci = CampaignInformation.objects.get(user_uuid=user_uuid)
                if ci.campaign == '':
                    ci.campaign = campaign
                if ci.source == '':
                    ci.source = source
                if ci.medium == '':
                    ci.medium = medium
                ci.save()
            else:
                # Setting campaign info for the first time for user
                CampaignInformation.objects.create(user=user_uuid.user,
                                                   user_uuid=user_uuid,
                                                   campaign=campaign,
                                                   source=source,
                                                   medium=medium)


def main():
    analytics = initialize_analytics_reporting()
    response = get_report(analytics)
    connect_ga_to_user(response)


if __name__ == '__main__':
    main()
