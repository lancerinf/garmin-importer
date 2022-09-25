from failure_modes import InvalidActivity, GarminConnectSessionException
from aws_utils import activity_already_persisted, persist_in_s3, insert_activity_in_dynamo, save_session_in_secret_store
from garmin_models import UserCredentials

from garminconnect import Garmin

from datetime import date, timedelta
import json
import logging

logger = logging.getLogger(__name__)


def get_garmin_session(credentials: UserCredentials) -> Garmin:
    api: Garmin
    if credentials.session:
        api = Garmin(credentials.username, credentials.password, session_data=credentials.session)
    else:
        api = Garmin(credentials.username, credentials.password)

    try:
        api.login()
    except Exception as e:
        logger.info('Trouble establishing/renewing a valid session with Garmin Connect.')
        raise GarminConnectSessionException('Trouble establishing/renewing a valid session with Garmin Connect.') from e

    return api


def save_garmin_session(credentials: UserCredentials, api: Garmin):
    session_to_save = api.session_data
    text_to_save = json.dumps(session_to_save)

    save_session_in_secret_store(credentials, text_to_save)


def check_for_new_activities(api: Garmin, since_date: date) -> list:
    # Tries retrieving 1 month worth of activities since specified date.
    # If nothing is found, iterates until some activity is found. Retries until current day.
    gcas = []
    while len(gcas) == 0 or since_date > date.today():
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
    zip_upload_success = persist_in_s3(f'{activity.get("beginTimestamp")}/{activity.get("activityId")}.zip', zip_buffer)
    gpx_upload_success = persist_in_s3(f'{activity.get("beginTimestamp")}/{activity.get("activityId")}.gpx', gpx_buffer)

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

    return api.get_activities_by_date(last_activity_date, month_after_last)


def _clean_activities_through_model(activities: list) -> list:
    cleaned_activities = []
    for a in activities:
        cleaned_activities.append(_clean_activity(a))
    return cleaned_activities


def _clean_activity(activity: dict) -> dict:
    cleaned_activity = {}
    for k, v in activity.items():
        if k in activity_model and v is not None:
            if isinstance(v, dict):
                for kk, vv in v.items():
                    if kk in activity_model.get(k):
                        cleaned_activity[f"{k}{kk.capitalize()}"] = vv
            elif isinstance(v, list):
                pass
            else:
                cleaned_activity[k] = v
    return cleaned_activity


def _valid_activity(activity: dict) -> bool:
    return bool(activity.get("beginTimestamp")) and bool(activity.get('activityId'))


activity_model: dict[str] = {
    "beginTimestamp": None,
    "activityId": None,
    "startTimeLocal": None,
    "activityType": {
        "typeId": None,
        "typeKey": None,
        "parentTypeId": None
    },
    "startTimeGMT": None,
    "distance": None,
    "duration": None,
    "elapsedDuration": None,
    "movingDuration": None,
    "elevationGain": None,
    "elevationLoss": None,
    "averageSpeed": None,
    "maxSpeed": None,
    "startLatitude": None,
    "startLongitude": None,
    "ownerId": None,
    "ownerFullName": None,
    "calories": None,
    "averageHR": None,
    "maxHR": None,
    "averageRunningCadenceInStepsPerMinute": None,
    "maxRunningCadenceInStepsPerMinute": None,
    "averageBikingCadenceInRevPerMinute": None,
    "maxBikingCadenceInRevPerMinute": None,
    "averageSwimCadenceInStrokesPerMinute": None,
    "maxSwimCadenceInStrokesPerMinute": None,
    "steps": None,
    "poolLength": None,
    "unitOfPoolLength": None,
    "timeZoneId": None,
    "sportTypeId": None,
    "avgPower": None,
    "maxPower": None,
    "aerobicTrainingEffect": None,
    "anaerobicTrainingEffect": None,
    "strokes": None,
    "normPower": None,
    "leftBalance": None,
    "rightBalance": None,
    "avgLeftBalance": None,
    "max20MinPower": None,
    "avgVerticalOscillation": None,
    "avgGroundContactTime": None,
    "avgStrideLength": None,
    "avgFractionalCadence": None,
    "maxFractionalCadence": None,
    "trainingStressScore": None,
    "intensityFactor": None,
    "vO2MaxValue": None,
    "avgVerticalRatio": None,
    "avgGroundContactBalance": None,
    "lactateThresholdBpm": None,
    "lactateThresholdSpeed": None,
    "maxFtp": None,
    "avgStrokeDistance": None,
    "avgStrokeCadence": None,
    "maxStrokeCadence": None,
    "workoutId": None,
    "avgStrokes": None,
    "minStrokes": None,
    "deviceId": None,
    "minTemperature": None,
    "maxTemperature": None,
    "minElevation": None,
    "maxElevation": None,
    "avgVerticalSpeed": None,
    "maxVerticalSpeed": None,
    "floorsClimbed": None,
    "floorsDescended": None,
    "locationName": None,
    "lapCount": None,
    "endLatitude": None,
    "endLongitude": None,
    "maxAvgPower_1": None,
    "maxAvgPower_2": None,
    "maxAvgPower_5": None,
    "maxAvgPower_10": None,
    "maxAvgPower_20": None,
    "maxAvgPower_30": None,
    "maxAvgPower_60": None,
    "maxAvgPower_120": None,
    "maxAvgPower_300": None,
    "maxAvgPower_600": None,
    "maxAvgPower_1200": None,
    "maxAvgPower_1800": None,
    "maxAvgPower_3600": None,
    "maxAvgPower_7200": None,
    "maxAvgPower_18000": None,
    "minActivityLapDuration": None
}
