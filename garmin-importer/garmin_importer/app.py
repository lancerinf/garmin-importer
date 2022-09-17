from failure_modes import CredentialsRetrievalFailure, GarminImportFailure
from aws_utils import retrieve_garmin_credentials
from garmin_utils import gc_authenticate, check_for_new_activities

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):
    output = {}
    try:
        credentials = retrieve_garmin_credentials()
        garmin = gc_authenticate(
            credentials.get('username'),
            credentials.get('password'),
        )

        activities = check_for_new_activities(garmin)
        output['message'] = f"{len(activities)} new activities found!"
        output['activities'] = activities

    except CredentialsRetrievalFailure as crf:
        output['error'] = str(crf)
    except GarminImportFailure as gif:
        output['error'] = str(gif)

    return output
