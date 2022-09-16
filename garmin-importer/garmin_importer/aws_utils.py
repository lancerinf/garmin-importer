from failure_modes import CredentialsRetrievalFailure

import boto3
import json

GARMIN_CREDENTIALS_NAME = 'garmin-importer/garmin-credentials'


def retrieve_garmin_credentials() -> dict:
    credentials = {}

    try:
        sm_client = boto3.client('secretsmanager')
        secret: dict = sm_client.get_secret_value(SecretId=GARMIN_CREDENTIALS_NAME)
        secret_string = json.loads(secret.get('SecretString'))
        if not (secret_string.get('username') and secret_string.get('password')):
            raise CredentialsRetrievalFailure("Credential retrieval went well, but either username or password is None")
        credentials.update(secret_string)

    except Exception as e:
        raise CredentialsRetrievalFailure("Something went bad during credentials retrieval") from e

    return credentials
