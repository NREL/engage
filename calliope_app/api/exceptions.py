
class ModelAccessException(Exception):
    """Raise when user has no access to the model"""


class ModelNotExistException(Exception):
    """Raise when model is None"""


class AuthenticationFailedException(Exception):
    """Raise when authentication failed."""
