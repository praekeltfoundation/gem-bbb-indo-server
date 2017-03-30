from os import environ

from django.contrib.auth.models import User
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

import httplib2

from users.models import CampaignInformation, UserUUID

SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
DISCOVERY_URI = ('https://analyticsreporting.googleapis.com/$discovery/rest')
# KEY_FILE_LOCATION = './dooit-staging-google-services-private-key.json'
# SERVICE_ACCOUNT_EMAIL = 'backend@firebase-dooit-staging.iam.gserviceaccount.com'
# VIEW_ID = '137570988'
VIEW_ID = environ.get('VIEW_ID', '')

def initialize_analytics_reporting():
    """Initializes an analyticsreporting service object.

    Returns:
      analytics an authorized analyticsreporting service object.
    """

    # print("project_id: " + environ.get('PROJECT_ID', ''))
    # print("private_key_id: " + environ.get('PRIVATE_KEY_ID', ''))
    # print("private_key: " + environ.get('PRIVATE_KEY', ''))
    # print("client_email: " + environ.get('CLIENT_EMAIL', ''))
    # print("client_id: " + environ.get('CLIENT_ID', ''))
    # print("view_id: "+ environ.get('VIEW_ID', ''))
    # print()

    # credentials = ServiceAccountCredentials.from_json_keyfile_name(KEY_FILE_LOCATION, scopes=SCOPES)

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
        ("client_x509_cert_url", "https://www.googleapis.com/robot/v1/metadata/x509/backend%40firebase-dooit-staging.iam.gserviceaccount.com"),
    ])

    # api_auth = dict([
    #     ("type", "service_account"),
    #     ("project_id", "firebase-dooit-staging"),
    #     ("private_key_id", "9a7aa71fe7886d49792733fe93cedb6b329a544e"),
    #     ("private_key", "-----BEGIN PRIVATE KEY-----\nMIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQC/jzkWYl+Zii/d\nZalMAU1wbFN+ACElE3VObMk0cinXjiA2yeVpXBF5bmIGXmVdHlZLqWcGsuV64lUt\ncKSA5Vk+bcRqqE97ZINzn+G8qDwsvGO7jasmz856EPZRI4UAixNesvHAri9CGAHD\nC4+WMslNKXN+mFxLduygO9IlXk3DfnM0VFKGJ3f+BdjlX31YbfpP4R1LiA5PiUBJ\nv+ECUMMhJfYews5qbQ+907XSIkhOa3Qlm4hRWnIol2dYaEY+LNzgorhyVwc4lEDz\n1HUe852RfcX8L+3h81yXvO58mMAO1Dv6kdxnciAB8dDaYREaGwr+qcmd6zoq1UjA\nmksGA0XnAgMBAAECggEBAK26yi6H52YL0p87bRA2ejIEvLAgk+7ZN+F5ff1nsJUD\nHCo0bzBfxKVZu+NExy9trRwPthV4N/F7xX5hk4AnAQpCaQnGPdeN8D3z+bms5m44\nKUdXE6suendwXMR3r08v0tBnACQclVWfCjIHkSDKTJEDj/B3Y/U5FR+5QTyMy4AI\n4+VN2G57R9zL3zIExfAoYw0apifR4qITX415SQO9PjIhKPgadSvEDLUjbwvs5otE\nfyb86ZKR9MCmLFqLN/1w7NDh6gPgFc5S8iImGRIaFW5iTi/yOkSAvQA1vnIttmx5\nMQ7xjhSmUkGR8wHZ1/G1+Q3YDfxhlFIlQQn121VZ1iECgYEA381PsWpfCrgd0y4u\ndZbMXtA0DwNxPI+JzINFW9rqZyJ9dB/zG3mFwO6yXb5JJtQdCLltV0nIrV5hSjrx\nmPEZQpoN4CK9wyvlSXbAyvP7FxneFuaYrt3CLh5OsM9EsfNNImjbgdcoL4qj/FXw\nAfEk1Vpsb4uB945LZmI9/fNxH1cCgYEA2x5pETqj3NAvs2hhdHr2rhPOco2Ae6bP\nXYM9z0mLlw1GYikb/ThRfQByGveUvaxgP8bevIMnjxqT2UaFQQ6V4u2qzYtMeNBX\nomf1TIFU2GLN8Z56B8H3Zl4YPRVA02EySW7mXEJ+GlBpAnhwPeOzLwoi2MeytuZJ\nSkfDAaeXQ/ECgYEAl2R+jWiEhG7KFio+WWM6OsUjAij099+tesAuMhXjzQKi1OQs\nAyDwnvOZixqGx5JjVZyB37NU4hpfO+SlvC0URl6KFl3J+nX+M/T2NBRZfWYNO3ag\nQGJY0fPEjYyYTrxkKGvAWZPfZlGl3rOPmPC0VvNFOSupLnp+fPLmNpzwoB8CgYEA\njlEUINKbd2HoeXhEQ+lRqwLGRfTODIHtkWkajjXQak1+92aH/VHE65GMiyNfAkqh\nQQsjxADTgsjaWnbJOdYFWBzRoSrmglmfcaZf1k7yEpEp/dLWo49B5sUarSHOtvwc\nM0HKcQXm7aRob+hVznzD9rt4oqAh3VV5KLuvVrXJM6ECgYAOQzemgdtSPtZM3G3N\nR2cmH1IA+SQlMcip4QWEUFc9IjPU95tzZJb/9IbBN1d7FnxArRhs2oOJaTsv8x2E\nYCm5vguqoMXAOed5/keiqs2dJxBMICyeWQ69ZqnGspkVTOf2BGEB28GvdemprC9j\ncXkx/ThXY/qE1y+7XYs0YwAKPg==\n-----END PRIVATE KEY-----\n"),
    #     ("client_email", "backend@firebase-dooit-staging.iam.gserviceaccount.com"),
    #     ("client_id", "104947281573094014313"),
    #     ("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
    #     ("token_uri", "https://accounts.google.com/o/oauth2/token"),
    #     ("auth_provider_x509_cert_url", "https://www.googleapis.com/oauth2/v1/certs"),
    #     ("client_x509_cert_url", "https://www.googleapis.com/robot/v1/metadata/x509/backend%40firebase-dooit-staging.iam.gserviceaccount.com"),
    # ])

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
                    'dateRanges': [{'startDate': '30daysAgo', 'endDate': 'today'}],
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
    """Parses and prints the Analytics Reporting API V4 response"""

    if response is None:
        return

    for report in response.get('reports', []):
        column_header = report.get('columnHeader', {})
        dimension_headers = column_header.get('dimensions', [])
        # metrics_headers = column_header.get('metricHeader', {}).get('metricHeaderEntries', [])
        rows = report.get('data', {}).get('rows', [])

        for row in rows:
            dimensions = row.get('dimensions', [])
            # date_range_values = row.get('metrics', [])

            campaign_info = CampaignInformation()

            for header, dimension in zip(dimension_headers, dimensions):
                # print('Header:' + header + " - Dimension: " + dimension)

                if header == 'ga:dimension1':
                    try:
                        user = UserUUID.objects.get(gaid=dimension)
                    except:
                        return

                    campaign_info.user = user
                    print('Dimension1: ' + dimension)

                if header == 'ga:campaign':
                    campaign_info.campaign = dimension
                    print('Campaign: ' + dimension)

                if header == 'ga:source':
                    campaign_info.source = dimension
                    print('Source: ' + dimension)

                if header == 'ga:medium':
                    campaign_info.medium = dimension
                    print('Medium: ' + dimension)

            # campaign_info.save()

            # for i, values in enumerate(date_range_values):
            #     print('Date range (' + str(i) + ')')
            #     for metric_header, value in zip(metrics_headers, values.get('values')):
            #         print('Metric header: ' + metric_header.get('name') + " : " + value)

        print('\n')


def main():
    analytics = initialize_analytics_reporting()
    response = get_report(analytics)
    connect_ga_to_user(response)


if __name__ == '__main__':
    main()
