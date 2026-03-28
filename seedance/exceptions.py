"""
Custom exceptions for Seedance SDK
"""


class SeedanceError(Exception):
    """Base exception for all Seedance SDK errors"""
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}


class APIError(SeedanceError):
    """Raised when API returns an error response"""
    pass


class AuthenticationError(SeedanceError):
    """Raised when authentication fails"""
    def __init__(self, message: str = "Invalid API key"):
        super().__init__(message, status_code=401)


class RateLimitError(SeedanceError):
    """Raised when rate limit is exceeded"""
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class InsufficientCreditsError(SeedanceError):
    """Raised when insufficient credits"""
    def __init__(self, message: str = "Insufficient credits", credits_needed: int = None):
        super().__init__(message, status_code=402)
        self.credits_needed = credits_needed


class ValidationError(SeedanceError):
    """Raised when request validation fails"""
    def __init__(self, message: str = "Validation failed", field: str = None):
        super().__init__(message, status_code=400)
        self.field = field


class TaskNotFoundError(SeedanceError):
    """Raised when task is not found"""
    def __init__(self, message: str = "Task not found", task_id: str = None):
        super().__init__(message, status_code=404)
        self.task_id = task_id


class TaskTimeoutError(SeedanceError):
    """Raised when task polling times out"""
    def __init__(self, message: str = "Task processing timeout", task_id: str = None):
        super().__init__(message)
        self.task_id = task_id


class TaskFailedError(SeedanceError):
    """Raised when task processing fails"""
    def __init__(self, message: str = "Task processing failed", task_id: str = None, error_details: str = None):
        super().__init__(message)
        self.task_id = task_id
        self.error_details = error_details


class NetworkError(SeedanceError):
    """Raised when network request fails"""
    pass


class WebhookSignatureError(SeedanceError):
    """Raised when webhook signature verification fails"""
    def __init__(self, message: str = "Invalid webhook signature"):
        super().__init__(message)


class ConfigurationError(SeedanceError):
    """Raised when SDK configuration is invalid"""
    pass
