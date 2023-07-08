class CredentialsRetrievalFailure(Exception):
    pass


class GarminConnectSessionException(BaseException):
    pass


class GarminConnectRetrieveActivitiesException(BaseException):
    pass


class GarminImporterFailure(Exception):
    pass


class InvalidActivity(Exception):
    pass


class DynamoPersistenceFailure(Exception):
    pass
