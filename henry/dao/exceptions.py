from henry.base.serialization import SerializableMixin


class BaseServiceException(SerializableMixin, Exception):
    _name = ('message', )

    def __init__(self, msg):
        self.message = msg


class ItemNotFound(BaseServiceException):
    """Exception raised when something is not found in the DB or filesystem"""


class ItemAlreadyExists(BaseServiceException):
    """Exception raised when intending to create something that already exists"""
