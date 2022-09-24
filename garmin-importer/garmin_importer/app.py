from aws_utils import retrieve_garmin_credentials, get_date_of_latest_activity
from garmin_utils import gc_authenticate, check_for_new_activities, persist_new_activities, UserCredentials

from garminconnect import Garmin

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    output = {}
    garmin: Garmin

    try:
        credentials: UserCredentials = retrieve_garmin_credentials()
        garmin = gc_authenticate(credentials)

        last_stored_activity = get_date_of_latest_activity(credentials.username)
        output['last_activity'] = last_stored_activity

        new_activities = check_for_new_activities(garmin, last_stored_activity)
        output['message'] = f"processing {len(new_activities)} new activities!"

        persisted_activities = persist_new_activities(garmin, credentials, new_activities)
        if persisted_activities:
            output['persisted_activities'] = persisted_activities

    except BaseException as e:
        logger.critical(e, exc_info=True)

    finally:
        garmin.logout()

    return output
