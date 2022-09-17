from failure_modes import CredentialsRetrievalFailure
from garmin_utils import UserCredentials

from datetime import date
import json
import boto3

GARMIN_CREDENTIALS_NAME = 'garmin-importer/garmin-credentials'
GARMIN_ACTIVITIES_TABLE = 'garmin-activities-table'
GARMIN_ACTIVITIES_BUCKET = 'garmin-importer-activities'


def retrieve_garmin_credentials() -> UserCredentials:
    try:
        sm_client = boto3.client('secretsmanager')
        secret: dict = sm_client.get_secret_value(SecretId=GARMIN_CREDENTIALS_NAME)
        secret_string = json.loads(secret.get('SecretString'))
        if not (secret_string.get('username') and secret_string.get('password')):
            raise CredentialsRetrievalFailure("Credential retrieval went well, but either username or password is None")
        credentials = UserCredentials(username=secret_string.get('username'), password=secret_string.get('password'))

    except Exception as e:
        raise CredentialsRetrievalFailure("Something went bad during credentials retrieval") from e

    return credentials


def get_date_of_latest_activity(username: str) -> date:
    # Lookup timestamp/id of last activity in dynamo, to know the date to fetch from next
    ddb_client = boto3.client('dynamodb')
    response = ddb_client.query(
        TableName=GARMIN_ACTIVITIES_TABLE,
        Select='SPECIFIC_ATTRIBUTES',
        ScanIndexForward=False,
        Limit=1,
        KeyConditionExpression="Username = :keyValue",
        ExpressionAttributeValues={":keyValue": {"S": username}},
        ProjectionExpression='ActivityTs',
    )

    return date.fromtimestamp(int(response.get("Items")[0].get('ActivityTs').get('N'))/1000)


def check_if_activity_already_persisted(username: str, activity_ts: str) -> bool:
    ddb_client = boto3.client('dynamodb')
    response = ddb_client.get_item(
        TableName=GARMIN_ACTIVITIES_TABLE,
        Key={
            'Username': {'S': username},
            'ActivityTs': {'N': activity_ts}
        },
        ProjectionExpression='ActivityTs',
    )

    return bool(response.get("Item"))


def insert_activity_in_dynamo():
    pass


def save_to_s3(path: str, ):
    pass

