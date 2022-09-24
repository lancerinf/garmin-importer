from failure_modes import CredentialsRetrievalFailure, DynamoPersistenceFailure
from garmin_models import UserCredentials

from datetime import date
import json
import boto3
from boto3_type_annotations.dynamodb import Client as DDBClient
from boto3_type_annotations.s3 import Client as S3Client
from boto3_type_annotations.secretsmanager import Client as SMClient

GARMIN_CREDENTIALS_NAME = 'garmin-importer/garmin-credentials'
GARMIN_ACTIVITIES_TABLE = 'garmin-activities-table'
GARMIN_ACTIVITIES_BUCKET = 'garmin-importer-activities'


def retrieve_garmin_credentials() -> UserCredentials:
    """Fetches Garmin credentials from secret storage"""
    try:
        sm_client: SMClient = boto3.client('secretsmanager')
        secret: dict = sm_client.get_secret_value(SecretId=GARMIN_CREDENTIALS_NAME)
        secret_string = json.loads(secret.get('SecretString'))
        if not (secret_string.get('username') and secret_string.get('password')):
            raise CredentialsRetrievalFailure("Credential retrieval went well, but either username or password is None")

    except Exception as e:
        raise CredentialsRetrievalFailure("Something went bad during credentials retrieval") from e

    return UserCredentials(username=secret_string.get('username'), password=secret_string.get('password'))


def get_date_of_latest_activity(username: str) -> date:
    """Returns date of last activity persisted

    Args:
        username: HASH key needed for the query
    """
    # Lookup timestamp/id of last activity in dynamo, to know the date to fetch from next
    ddb_client: DDBClient = boto3.client('dynamodb')
    response = ddb_client.query(
        TableName=GARMIN_ACTIVITIES_TABLE,
        Select='SPECIFIC_ATTRIBUTES',
        ScanIndexForward=False,
        Limit=1,
        KeyConditionExpression="Username = :keyValue",
        ExpressionAttributeValues={":keyValue": {"S": username}},
        ProjectionExpression='ActivityTs',
    )

    last_stored_activity = date(year=2016, month=1, day=1)
    if len(response.get("Items")):
        last_stored_activity = date.fromtimestamp(int(response.get("Items")[0].get('ActivityTs').get('N'))/1000)

    return last_stored_activity


def activity_already_persisted(username: str, activity_ts: int) -> bool:
    """Check if an activity has already been persisted

    Args:
        username: HASH key is needed for the lookup of an entry
        activity_ts: SORT key is needed for the lookup of an entry
    """
    ddb_client: DDBClient = boto3.client('dynamodb')
    response = ddb_client.get_item(
        TableName=GARMIN_ACTIVITIES_TABLE,
        Key={
            'Username': {'S': username},
            'ActivityTs': {'N': str(activity_ts)}
        },
        ProjectionExpression='ActivityTs',
    )
    return bool(response.get("Item"))


def persist_in_s3(s3_key: str, object_bytes: bytes) -> bool:
    """Persists an object on S3

    Args:
        s3_key: the key under which to persist the object
        object_bytes: the raw bytes to persist in the object
    """
    s3_client: S3Client = boto3.client('s3')
    response = s3_client.put_object(
        Body=object_bytes,
        Bucket=GARMIN_ACTIVITIES_BUCKET,
        Key=s3_key,
        StorageClass='STANDARD',
    )
    return response.get('ResponseMetadata').get('HTTPStatusCode') == 200


def insert_activity_in_dynamo(username: str, activity: dict):
    """Inserts a new activity in DynamoDB

    Args:
        username: is needed as it's the HASH key of the table
        activity: the activity in a cleaned state (no empty fields)
    """

    ddb_client: DDBClient = boto3.client('dynamodb')
    response = ddb_client.put_item(
        TableName=GARMIN_ACTIVITIES_TABLE,
        Item=_format_activity_keys(username, activity)
    )

    if not response.get('ResponseMetadata').get('HTTPStatusCode') == 200:
        raise DynamoPersistenceFailure(f'Failed persisting activity in DynamoDB. Response: {response}')


def _format_activity_keys(username: str, activity: dict) -> dict:
    activity['Username'] = username
    activity['ActivityTs'] = activity.pop('beginTimestamp')
    return _dict_to_ddb_item(activity)


def _dict_to_ddb_item(activity_dict: dict) -> dict:
    activity_ddb_dict = {}
    for k, v in activity_dict.items():
        if type(v) is str:
            activity_ddb_dict[k] = {
                'S': v
            }
        elif type(v) is int or type(v) is float:
            activity_ddb_dict[k] = {
                'N': str(v)
            }
        elif type(v) is dict:
            activity_ddb_dict[k] = {
                'M': _dict_to_ddb_item(v)
            }
        elif type(v) is list:
            activity_ddb_dict[k] = []
            for i in v:
                activity_ddb_dict[k].append(_dict_to_ddb_item(i))
    return activity_ddb_dict
