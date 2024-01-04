from failure_modes import InvalidActivity, GarminConnectRetrieveActivitiesException, GarminConnectSessionException
from aws_utils import activity_already_persisted, persist_in_s3, insert_activity_in_dynamo
from garmin_models import UserCredentials, GarminActivityModel

from garminconnect import Garmin

from datetime import date, timedelta
import logging

MAX_GARMIN_CONNECT_API_RETRIES = 1

logger = logging.getLogger(__name__)


def _retry_api_on_failure(api_call, *args, max_retries=MAX_GARMIN_CONNECT_API_RETRIES):
    retries = 0

    while retries < max_retries:
        try:
            if args:
                results = api_call(*args)
            else:
                results = api_call()
            break

        except Exception as e:
            if (retries + 1) < max_retries:
                logger.error(f"Error occurred when calling {api_call.__name__} - Try {retries} - Retrying..")
                retries += 1
            else:
                raise e

    return results


def get_garmin_session(credentials: UserCredentials) -> Garmin:
    api: Garmin = Garmin(credentials.username, credentials.password)

    try:
        _retry_api_on_failure(api.login)
    except Exception as e:
        raise GarminConnectSessionException('Trouble establishing/renewing a valid session with Garmin Connect.') from e

    return api


def check_for_new_activities(api: Garmin, since_date: date) -> list:
    # Tries retrieving 1 month worth of activities since specified date.
    # If nothing is found, iterates until some activity is found. Retries until current day.
    gcas = []
    while len(gcas) <= 5 and since_date < (date.today() + timedelta(days=1)):
        logger.debug(f"Loading 1 month of activities since {since_date}")
        gcas.extend(_retrieve_activities_from_gc_since_last(api, since_date))
        since_date = since_date + timedelta(days=30)

    return _clean_activities_through_model(gcas)


def persist_new_activities(api: Garmin, credentials: UserCredentials, activities: list[dict]) -> list[tuple[int, str]]:
    persisted_activities: list[tuple[int, str]] = []
    for activity in activities:
        if not _valid_activity(activity):
            logger.error('Activity cannot be persisted because it lacks either beginTimestamp or activityId.')
            raise InvalidActivity(f'This activity cannot be persisted: {activity}')
        if not activity_already_persisted(credentials.username, activity.get("beginTimestamp")):
            logger.info(f'Activity {activity.get("beginTimestamp")} not persisted yet. Proceeding..')
            _persist_activity(api, credentials.username, activity)
            persisted_activities.append((activity.get("ActivityTs"), activity.get("startTimeLocal")))
    return persisted_activities


def _persist_activity(api: Garmin, username: str, activity: dict):
    # retrieves GPX and FIT files from Garmin Connect and saves them to s3.
    logger.debug(f"Retrieving zip and gpx for activity: {activity.get('beginTimestamp')}")
    zip_buffer = api.download_activity(activity.get("activityId"), Garmin.ActivityDownloadFormat.ORIGINAL)
    gpx_buffer = api.download_activity(activity.get("activityId"), Garmin.ActivityDownloadFormat.GPX)

    # persist them to s3
    logger.debug(f"Persisting zip, gpx for activity: {activity.get('beginTimestamp')}")
    zip_upload_success = persist_in_s3(f'{username}/{activity.get("beginTimestamp")}/{activity.get("activityId")}.zip', zip_buffer)
    gpx_upload_success = persist_in_s3(f'{username}/{activity.get("beginTimestamp")}/{activity.get("activityId")}.gpx', gpx_buffer)

    # write activity details to dynamo
    if zip_upload_success and gpx_upload_success:
        logger.debug(f"Storing dynamo entry for activity: {activity.get('beginTimestamp')}")
        insert_activity_in_dynamo(username, activity)
        logger.info(f"Correctly stored zip, gpx and dynamo entry for new activity: {activity.get('ActivityTs')}")


def _retrieve_activities_from_gc_since_last(api: Garmin, last_activity_date: date) -> list:
    # retrieve older activities 1 month at a time since last stored
    month_after_last = last_activity_date + timedelta(days=30)
    if date.today() < month_after_last:
        month_after_last = date.today()

    activities = []
    try:
        activities = _retry_api_on_failure(api.get_activities_by_date, last_activity_date, month_after_last, max_retries=3)
    except Exception as e:
        raise GarminConnectRetrieveActivitiesException('Trouble establishing/renewing a valid session with Garmin Connect.') from e

    return activities


def _clean_activities_through_model(activities: list) -> list:
    cleaned_activities = []
    for a in activities:
        cleaned_activities.append(_clean_activity(a))
    return cleaned_activities


def _clean_activity(activity: dict) -> dict:
    logger.debug(activity)
    cleaned_activity = {}
    for k, v in activity.items():
        if k in GarminActivityModel and v is not None:
            logger.debug(k)
            if isinstance(v, dict):
                for kk, vv in v.items():
                    if kk in GarminActivityModel.get(k):
                        cleaned_activity[f"{k}{kk.capitalize()}"] = vv
            elif isinstance(v, list):
                pass
            else:
                cleaned_activity[k] = v
    return cleaned_activity


def _valid_activity(activity: dict) -> bool:
    return bool(activity.get("beginTimestamp")) and bool(activity.get('activityId'))
