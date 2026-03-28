"""
Seedance SDK - Python client for Seedance AI Video Generation API

Example usage:
    >>> import seedance
    >>> 
    >>> # Async usage
    >>> async with seedance.SeedanceClient("sk-video-xxxxx") as client:
    >>>     task = await client.generate_video(
    >>>         prompt="A cat playing piano",
    >>>         duration=8,
    >>>         resolution="1080p"
    >>>     )
    >>>     result = await client.wait_for_completion(task.id)
    >>>     print(f"Video ready: {result.result.video_url}")
    >>> 
    >>> # Sync usage
    >>> with seedance.SeedanceClient("sk-video-xxxxx") as client:
    >>>     task = client.generate_video_sync(
    >>>         prompt="A cat playing piano",
    >>>         duration=8,
    >>>         resolution="1080p"
    >>>     )
    >>>     result = client.wait_for_completion_sync(task.id)
    >>>     print(f"Video ready: {result.result.video_url}")
"""

from .client import SeedanceClient
from .models import (
    Model,
    Resolution,
    Duration,
    AspectRatio,
    TaskStatus,
    TaskType,
    GenerationRequest,
    GenerationResponse,
    TaskData,
    TaskResult,
    TaskListResponse,
    PaginationInfo,
    WebhookPayload,
    CreditsInfo,
)
from .exceptions import (
    SeedanceError,
    APIError,
    AuthenticationError,
    RateLimitError,
    InsufficientCreditsError,
    ValidationError,
    TaskNotFoundError,
    TaskTimeoutError,
    TaskFailedError,
    NetworkError,
    WebhookSignatureError,
    ConfigurationError,
)
from .webhook import WebhookHandler, WebhookServer, create_webhook_server
from .utils import (
    validate_api_key,
    format_duration,
    format_file_size,
    calculate_estimated_cost,
    sanitize_prompt,
    create_progress_callback,
)

__version__ = "1.0.0"
__author__ = "Seedance Team"
__email__ = "support@vibegen.art"
__url__ = "https://vibegen.art"

__all__ = [
    # Main client
    "SeedanceClient",
    
    # Models
    "Model",
    "Resolution", 
    "Duration",
    "AspectRatio",
    "TaskStatus",
    "TaskType",
    "GenerationRequest",
    "GenerationResponse",
    "TaskData",
    "TaskResult",
    "TaskListResponse",
    "PaginationInfo",
    "WebhookPayload",
    "CreditsInfo",
    
    # Exceptions
    "SeedanceError",
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "InsufficientCreditsError",
    "ValidationError",
    "TaskNotFoundError",
    "TaskTimeoutError",
    "TaskFailedError",
    "NetworkError",
    "WebhookSignatureError",
    "ConfigurationError",
    
    # Webhook
    "WebhookHandler",
    "WebhookServer", 
    "create_webhook_server",
    
    # Utils
    "validate_api_key",
    "format_duration",
    "format_file_size",
    "calculate_estimated_cost",
    "sanitize_prompt",
    "create_progress_callback",
]
