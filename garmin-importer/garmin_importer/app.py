from failure_modes import CredentialsRetrievalFailure, GarminImportFailure
from aws_utils import retrieve_garmin_credentials, get_date_of_latest_activity
from garmin_utils import gc_authenticate, check_for_new_activities, UserCredentials

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):
    output = {}
    try:
        credentials: UserCredentials = retrieve_garmin_credentials()
        # garmin = gc_authenticate(credentials)

        last_stored_activity = get_date_of_latest_activity(credentials.username)
        output['last_activity'] = last_stored_activity

        # activities = check_for_new_activities(garmin)
        # output['message'] = f"{len(activities)} new activities found!"
        # output['activities'] = activities

    except CredentialsRetrievalFailure as crf:
        output['error'] = str(crf)
    except GarminImportFailure as gif:
        output['error'] = str(gif)
    except Exception as e:
        output['unhandled_exception'] = str(e)

    return output
