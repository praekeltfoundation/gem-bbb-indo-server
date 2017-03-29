"""Hello Analytics Reporting API V4."""

from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

import httplib2

SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
DISCOVERY_URI = ('https://analyticsreporting.googleapis.com/$discovery/rest')
KEY_FILE_LOCATION = './dooit-staging-google-services-private-key.json'
SERVICE_ACCOUNT_EMAIL = 'backend@firebase-dooit-staging.iam.gserviceaccount.com'
VIEW_ID = '137570988'


def initialize_analytics_reporting():
    """Initializes an analyticsreporting service object.

    Returns:
      analytics an authorized analyticsreporting service object.
    """

    credentials = ServiceAccountCredentials.from_json_keyfile_name(KEY_FILE_LOCATION, scopes=SCOPES)

    http = credentials.authorize(httplib2.Http())

    # Build the service object.
    analytics = build('analytics', 'v4', http=http, discoveryServiceUrl=DISCOVERY_URI)

    return analytics


def get_report(analytics):
    # Use the Analytics Service Object to query the Analytics Reporting API V4.
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


def print_response(response):
    """Parses and prints the Analytics Reporting API V4 response"""

    for report in response.get('reports', []):
        column_header = report.get('columnHeader', {})
        dimension_headers = column_header.get('dimensions', [])
        metrics_headers = column_header.get('metricHeader', {}).get('metricHeaderEntries', [])
        rows = report.get('data', {}).get('rows', [])

        for row in rows:
            dimensions = row.get('dimensions', [])
            date_range_values = row.get('metrics', [])

            for header, dimension in zip(dimension_headers, dimensions):
                print('Header:' + header + " : " + dimension)

            for i, values in enumerate(date_range_values):
                print('Date range (' + str(i) + ')')
                for metric_header, value in zip(metrics_headers, values.get('values')):
                    print('Metric header: ' + metric_header.get('name') + " : " + value)

        print('\n')

    # for report in response.get('reports', []):
    #     columnHeader = report.get('columnHeader', {})
    #     dimensionHeaders = columnHeader.get('dimensions', [])
    #     metricHeaders = columnHeader.get('metricHeader', {}).get('metricHeaderEntries', [])
    #     rows = report.get('data', {}).get('rows', [])
    #
    #     for row in rows:
    #         dimensions = row.get('dimensions', [])
    #         dateRangeValues = row.get('metrics', [])
    #
    #         for header, dimension in zip(dimensionHeaders, dimensions):
    #             print(header + ': ' + dimension)
    #
    #         for i, values in enumerate(dateRangeValues):
    #             print('Date range (' + str(i) + ')')
    #             for metricHeader, value in zip(metricHeaders, values.get('values')):
    #                 print(metricHeader.get('name') + ': ' + value)
    #
    #         print('\n\n')


def main():
    analytics = initialize_analytics_reporting()
    response = get_report(analytics)
    print_response(response)


if __name__ == '__main__':
    main()
