from aws_utils import retrieve_garmin_credentials, get_date_of_latest_activity
from garmin_utils import check_for_new_activities, persist_new_activities, get_garmin_session, save_garmin_session
from garmin_models import UserCredentials
from failure_modes import GarminConnectSessionException

from garminconnect import Garmin

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    output = {}
    garmin: Garmin

    try:
        credentials: UserCredentials = retrieve_garmin_credentials()
        logger.info('Authenticating with Garmin Connect..')
        garmin = get_garmin_session(credentials)

        logging.info('Checking last activity persisted..')
        last_stored_activity = get_date_of_latest_activity(credentials.username)
        output['last_activity'] = str(last_stored_activity)

        logging.info(f'Looking for new activities since: {str(last_stored_activity)}')
        new_activities = check_for_new_activities(garmin, last_stored_activity)

        logging.info(f'Found {len(new_activities)} activities since last. Processing..')
        persisted_activities = persist_new_activities(garmin, credentials, new_activities)
        if persisted_activities:
            logging.info(f'Persisted {len(persisted_activities)} new activities.')
            output['persisted_activities'] = str(persisted_activities)
        else:
            logging.info('No new activity found.')

        save_garmin_session(credentials, garmin)

    except GarminConnectSessionException as e:
        logger.critical(e, exc_info=True)

    except Exception as e:
        logger.critical(e, exc_info=True)
        save_garmin_session(credentials, garmin)

    return output
