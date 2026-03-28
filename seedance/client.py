"""
Main Seedance SDK client
"""
import asyncio
import hashlib
import hmac
import time
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .models import (
    GenerationRequest,
    GenerationResponse,
    TaskData,
    TaskStatus,
    TaskListResponse,
    CreditsInfo,
    WebhookPayload,
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
from .utils import validate_api_key, parse_error_response


class SeedanceClient:
    """
    Main client for Seedance API
    
    Example:
        >>> client = SeedanceClient(api_key="sk-video-xxxxx")
        >>> task = await client.generate_video(
        ...     prompt="A cat playing piano",
        ...     duration=8,
        ...     resolution="1080p"
        ... )
        >>> result = await client.wait_for_completion(task.id)
        >>> print(result.video_url)
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://vibegen.art/api/v1",
        timeout: float = 30.0,
        max_retries: int = 3,
        webhook_secret: Optional[str] = None,
    ):
        """
        Initialize the Seedance client
        
        Args:
            api_key: Your Seedance API key (starts with 'sk-video-')
            base_url: API base URL
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            webhook_secret: Secret for webhook signature verification
        """
        if not validate_api_key(api_key):
            raise ConfigurationError("Invalid API key format. API keys should start with 'sk-video-'")
        
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.webhook_secret = webhook_secret
        
        self._client: Optional[httpx.AsyncClient] = None
        self._client_sync: Optional[httpx.Client] = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "seedance-sdk-python/1.0.0"
        }
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self._get_headers()
            )
        return self._client
    
    @property
    def client_sync(self) -> httpx.Client:
        """Get or create sync HTTP client"""
        if self._client_sync is None:
            self._client_sync = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self._get_headers()
            )
        return self._client_sync
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    def __enter__(self):
        """Sync context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context manager exit"""
        self.close_sync()
    
    async def close(self):
        """Close async HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def close_sync(self):
        """Close sync HTTP client"""
        if self._client_sync:
            self._client_sync.close()
            self._client_sync = None
    
    def _handle_error(self, response: httpx.Response) -> None:
        """Handle API error responses"""
        try:
            error_data = response.json()
        except:
            error_data = {}
        
        status_code = response.status_code
        message = error_data.get("error", f"HTTP {status_code}")
        
        if status_code == 401:
            raise AuthenticationError(message)
        elif status_code == 402:
            credits_needed = error_data.get("credits_needed")
            raise InsufficientCreditsError(message, credits_needed)
        elif status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(message, int(retry_after) if retry_after else None)
        elif status_code == 404:
            raise TaskNotFoundError(message)
        elif status_code >= 400:
            raise APIError(message, status_code, error_data)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((NetworkError, RateLimitError))
    )
    async def _request_async(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """Make async HTTP request with retry logic"""
        try:
            response = await self.client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            self._handle_error(e.response)
            raise
        except httpx.RequestError as e:
            raise NetworkError(f"Network error: {e}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((NetworkError, RateLimitError))
    )
    def _request_sync(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> httpx.Response:
        """Make sync HTTP request with retry logic"""
        try:
            response = self.client_sync.request(method, endpoint, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            self._handle_error(e.response)
            raise
        except httpx.RequestError as e:
            raise NetworkError(f"Network error: {e}")
    
    async def generate_video(self, request: Union[GenerationRequest, Dict[str, Any]]) -> TaskData:
        """
        Generate a video
        
        Args:
            request: Generation request (either GenerationRequest object or dict)
            
        Returns:
            TaskData: Created task information
            
        Raises:
            ValidationError: If request is invalid
            APIError: If API request fails
        """
        if isinstance(request, dict):
            request = GenerationRequest(**request)
        
        response = await self._request_async(
            "POST",
            "/generations",
            json=request.model_dump(exclude_none=True)
        )
        
        data = response.json()
        return TaskData(**data["data"])
    
    async def get_task(self, task_id: str) -> TaskData:
        """
        Get task information
        
        Args:
            task_id: Task ID
            
        Returns:
            TaskData: Task information
            
        Raises:
            TaskNotFoundError: If task not found
        """
        response = await self._request_async("GET", f"/tasks/{task_id}")
        data = response.json()
        return TaskData(**data["data"])
    
    async def list_tasks(
        self,
        page: int = 1,
        limit: int = 20,
        status: Optional[TaskStatus] = None,
        model: Optional[str] = None
    ) -> TaskListResponse:
        """
        List tasks with pagination and filtering
        
        Args:
            page: Page number (default: 1)
            limit: Number of tasks per page (default: 20)
            status: Filter by task status
            model: Filter by model
            
        Returns:
            TaskListResponse: List of tasks with pagination info
        """
        params = {"page": page, "limit": limit}
        if status:
            params["status"] = status.value
        if model:
            params["model"] = model
        
        response = await self._request_async("GET", "/tasks", params=params)
        data = response.json()
        return TaskListResponse(**data)
    
    async def get_credits(self) -> CreditsInfo:
        """
        Get credits information
        
        Returns:
            CreditsInfo: Credits information
        """
        response = await self._request_async("GET", "/credits")
        data = response.json()
        return CreditsInfo(**data["data"])
    
    async def wait_for_completion(
        self,
        task_id: str,
        timeout: Optional[float] = None,
        poll_interval: float = 2.0,
        on_progress: Optional[Callable[[TaskData], None]] = None
    ) -> TaskData:
        """
        Wait for task completion
        
        Args:
            task_id: Task ID
            timeout: Maximum time to wait (seconds)
            poll_interval: Polling interval (seconds)
            on_progress: Callback function called with task data on each poll
            
        Returns:
            TaskData: Completed task data
            
        Raises:
            TaskTimeoutError: If task doesn't complete within timeout
            TaskFailedError: If task fails
        """
        start_time = time.time()
        
        while True:
            task = await self.get_task(task_id)
            
            if on_progress:
                on_progress(task)
            
            if task.status == TaskStatus.COMPLETED:
                return task
            elif task.status == TaskStatus.FAILED:
                raise TaskFailedError(
                    f"Task failed: {task.error}",
                    task_id=task_id,
                    error_details=task.error
                )
            elif task.status in [TaskStatus.CANCELLED]:
                raise SeedanceError(f"Task {task.status.value}: {task_id}")
            
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                raise TaskTimeoutError(f"Task timeout after {timeout}s", task_id=task_id)
            
            await asyncio.sleep(poll_interval)
    
    async def cancel_task(self, task_id: str) -> TaskData:
        """
        Cancel a task
        
        Args:
            task_id: Task ID
            
        Returns:
            TaskData: Updated task data
        """
        response = await self._request_async("POST", f"/tasks/{task_id}/cancel")
        data = response.json()
        return TaskData(**data["data"])
    
    def generate_video_sync(self, request: Union[GenerationRequest, Dict[str, Any]]) -> TaskData:
        """Synchronous version of generate_video"""
        if isinstance(request, dict):
            request = GenerationRequest(**request)
        
        response = self._request_sync(
            "POST",
            "/generations",
            json=request.model_dump(exclude_none=True)
        )
        
        data = response.json()
        return TaskData(**data["data"])
    
    def get_task_sync(self, task_id: str) -> TaskData:
        """Synchronous version of get_task"""
        response = self._request_sync("GET", f"/tasks/{task_id}")
        data = response.json()
        return TaskData(**data["data"])
    
    def wait_for_completion_sync(
        self,
        task_id: str,
        timeout: Optional[float] = None,
        poll_interval: float = 2.0,
        on_progress: Optional[Callable[[TaskData], None]] = None
    ) -> TaskData:
        """Synchronous version of wait_for_completion"""
        import time
        
        start_time = time.time()
        
        while True:
            task = self.get_task_sync(task_id)
            
            if on_progress:
                on_progress(task)
            
            if task.status == TaskStatus.COMPLETED:
                return task
            elif task.status == TaskStatus.FAILED:
                raise TaskFailedError(
                    f"Task failed: {task.error}",
                    task_id=task_id,
                    error_details=task.error
                )
            elif task.status in [TaskStatus.CANCELLED]:
                raise SeedanceError(f"Task {task.status.value}: {task_id}")
            
            if timeout and (time.time() - start_time) > timeout:
                raise TaskTimeoutError(f"Task timeout after {timeout}s", task_id=task_id)
            
            time.sleep(poll_interval)
    
    def verify_webhook_signature(self, payload: Union[str, bytes], signature: str) -> bool:
        """
        Verify webhook signature
        
        Args:
            payload: Raw webhook payload (string or bytes)
            signature: Signature from webhook header
        
        Returns:
            bool: True if signature is valid
            
        Raises:
            WebhookSignatureError: If webhook secret is not configured
        """
        if not self.webhook_secret:
            raise WebhookSignatureError("Webhook secret not configured")
        
        # Convert bytes to string if needed
        if isinstance(payload, bytes):
            payload_str = payload.decode('utf-8')
        else:
            payload_str = payload
        
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    def parse_webhook_payload(self, payload: str, signature: str) -> WebhookPayload:
        """
        Parse and verify webhook payload
        
        Args:
            payload: Raw webhook payload string
            signature: Signature from webhook header
            
        Returns:
            WebhookPayload: Parsed webhook data
            
        Raises:
            WebhookSignatureError: If signature is invalid
        """
        if not self.verify_webhook_signature(payload, signature):
            raise WebhookSignatureError("Invalid webhook signature")
        
        import json
        data = json.loads(payload)
        return WebhookPayload(**data)
