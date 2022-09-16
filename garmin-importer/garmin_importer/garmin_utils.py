from failure_modes import GarminImportFailure
from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)

import datetime


def gc_authenticate(username: str, password: str) -> Garmin:
    api = Garmin(username, password)
    try:
        api.login()

    except GarminConnectConnectionError as gcce:
        raise GarminImportFailure("garmin importer failed connecting to garmin connect") from gcce
    except GarminConnectAuthenticationError as gae:
        raise GarminImportFailure("garmin importer failed authenticating with garmin connect") from gae

    return api


def retrieve_activities(api: Garmin) -> list:
    activities = []
    today = datetime.date.today()
    last_week = today - datetime.timedelta(days=7)

    try:
        activities = api.get_activities_by_date(last_week, today)

    except GarminConnectConnectionError as gcce:
        raise GarminImportFailure("garmin importer failed connecting to garmin connect") from gcce
    except GarminConnectTooManyRequestsError as gctmre:
        raise GarminImportFailure("garmin importer failed with too many requests to garmin connect") from gctmre

    return activities
