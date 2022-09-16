from failure_modes import CredentialsRetrievalFailure, GarminImportFailure
from aws_utils import retrieve_garmin_credentials
from garmin_utils import gc_authenticate, retrieve_activities


def lambda_handler(event, context):
    output = {}
    try:
        credentials = retrieve_garmin_credentials()
        garmin = gc_authenticate(
            credentials.get('username'),
            credentials.get('password'),
        )

        activities = retrieve_activities(garmin)
        output['activities'] = activities

    except CredentialsRetrievalFailure as crf:
        output['error'] = str(crf)

    return output
