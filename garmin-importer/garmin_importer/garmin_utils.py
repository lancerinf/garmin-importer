from failure_modes import GarminImportFailure
from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)

from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def gc_authenticate(username: str, password: str) -> Garmin:
    api = Garmin(username, password)
    try:
        logger.debug("authenticating to GC")
        api.login()
        logger.debug("authentication successful")

    except GarminConnectConnectionError as gcce:
        raise GarminImportFailure("garmin importer failed connecting to garmin connect") from gcce
    except GarminConnectAuthenticationError as gae:
        raise GarminImportFailure("garmin importer failed authenticating with garmin connect") from gae

    return api


def check_for_new_activities(api: Garmin, since_date: date = date(year=2016, month=1, day=1)) -> list:
    # Tries retrieving 1 month worth of activities since specified date.
    # If nothing is found, iterates until some activity is found. Retries until current day.
    gcas = []
    try:
        while len(gcas) == 0 or since_date > date.today():
            logger.debug(f"loading 1 month of activities since {since_date}")
            gcas.extend(_retrieve_activities_from_gc_since_last(api, since_date))
            since_date = since_date + timedelta(days=30)
        logger.info(f"found {len(gcas)} activities since {since_date}")

    except GarminConnectConnectionError as gcce:
        raise GarminImportFailure("garmin importer failed connecting to garmin connect") from gcce
    except GarminConnectTooManyRequestsError as gctmre:
        raise GarminImportFailure("garmin importer failed with too many requests to garmin connect") from gctmre
    except GarminConnectAuthenticationError as gae:
        raise GarminImportFailure("garmin importer failed authenticating with garmin connect") from gae

    cleaned_gcas = _clean_activities_through_model(gcas)
    return cleaned_gcas


def _retrieve_activities_from_gc_since_last(api: Garmin, last_activity_date: date) -> list:
    # retrieve older activities 1 month at a time since last stored
    month_after_last = last_activity_date + timedelta(days=30)
    if date.today() < month_after_last:
        month_after_last = date.today()

    activities = api.get_activities_by_date(last_activity_date, month_after_last)
    return activities


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


activity_model: dict[str] = {
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
    "beginTimestamp": None,
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
