from failure_modes import CredentialsRetrievalFailure, GarminImportFailure, InvalidActivity
from aws_utils import retrieve_garmin_credentials, get_date_of_latest_activity
from garmin_utils import gc_authenticate, check_for_new_activities, persist_new_activities, UserCredentials

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    output = {}
    try:
        credentials: UserCredentials = retrieve_garmin_credentials()
        garmin = gc_authenticate(credentials)

        last_stored_activity = get_date_of_latest_activity(credentials.username)
        output['last_activity'] = last_stored_activity

        new_activities = check_for_new_activities(garmin, last_stored_activity)
        output['message'] = f"processing {len(new_activities)} new activities!"

        persist_new_activities(garmin, credentials, new_activities)

    except CredentialsRetrievalFailure as crf:
        output['error'] = str(crf)
    except GarminImportFailure as gif:
        output['error'] = str(gif)
    except InvalidActivity as ia:
        output['error'] = str(ia)
    except BaseException as e:
        output['unhandled_exception'] = str(e)

    return output
