class CaptureRuntimeError(Exception):
    """Base runtime error."""

class AuthorizationError(CaptureRuntimeError):
    pass

class ConsentRequiredError(AuthorizationError):
    pass

class ValidationError(CaptureRuntimeError):
    pass

class NotFoundError(CaptureRuntimeError):
    pass

class ConflictError(CaptureRuntimeError):
    pass

class CapabilityUnavailableError(CaptureRuntimeError):
    pass

class PayloadTooLargeError(CaptureRuntimeError):
    pass
