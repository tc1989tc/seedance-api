"""
Tests for Seedance client
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from seedance import SeedanceClient, GenerationRequest, Model, Resolution, TaskStatus
from seedance.exceptions import (
    AuthenticationError,
    InsufficientCreditsError,
    RateLimitError,
    TaskNotFoundError,
    ValidationError
)


class TestSeedanceClient:
    """Test cases for SeedanceClient"""
    
    def test_init_with_valid_api_key(self):
        """Test client initialization with valid API key"""
        client = SeedanceClient("sk-video-1234567890abcdef")
        assert client.api_key == "sk-video-1234567890abcdef"
        assert client.base_url == "https://vibegen.art/api/v1"
        assert client.timeout == 30.0
        assert client.max_retries == 3
    
    def test_init_with_invalid_api_key(self):
        """Test client initialization with invalid API key"""
        with pytest.raises(Exception):  # ConfigurationError
            SeedanceClient("invalid-key")
    
    def test_init_with_custom_options(self):
        """Test client initialization with custom options"""
        client = SeedanceClient(
            api_key="sk-video-1234567890abcdef",
            base_url="https://api.example.com",
            timeout=60.0,
            max_retries=5,
            webhook_secret="secret"
        )
        assert client.base_url == "https://api.example.com"
        assert client.timeout == 60.0
        assert client.max_retries == 5
        assert client.webhook_secret == "secret"
    
    @pytest.mark.asyncio
    async def test_generate_video_success(self):
        """Test successful video generation"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "id": "task_123",
                "status": "pending",
                "model": "seedance-2.0",
                "task_type": "text_to_video",
                "created_at": "2025-01-01T12:00:00Z",
                "updated_at": "2025-01-01T12:00:00Z",
                "estimated_time": 30
            }
        }
        
        with patch.object(SeedanceClient, '_request_async', return_value=mock_response):
            client = SeedanceClient("sk-video-1234567890abcdef")
            
            request = GenerationRequest(
                prompt="A cat playing piano",
                model=Model.SEEDANCE_2_0,
                duration=8,
                resolution=Resolution.P1080
            )
            
            task = await client.generate_video(request)
            
            assert task.id == "task_123"
            assert task.status == TaskStatus.PENDING
            assert task.model == Model.SEEDANCE_2_0
    
    @pytest.mark.asyncio
    async def test_generate_video_with_dict(self):
        """Test video generation with dict request"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "id": "task_456",
                "status": "pending",
                "model": "seedance-2.0",
                "task_type": "text_to_video",
                "created_at": "2025-01-01T12:00:00Z",
                "updated_at": "2025-01-01T12:00:00Z"
            }
        }
        
        with patch.object(SeedanceClient, '_request_async', return_value=mock_response):
            client = SeedanceClient("sk-video-1234567890abcdef")
            
            task = await client.generate_video({
                "prompt": "A cat playing piano",
                "model": "seedance-2.0",
                "duration": 8,
                "resolution": "1080p"
            })
            
            assert task.id == "task_456"
    
    @pytest.mark.asyncio
    async def test_generate_video_authentication_error(self):
        """Test authentication error during generation"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Invalid API key"}
        
        with patch.object(SeedanceClient, '_request_async') as mock_request:
            mock_request.side_effect = AuthenticationError("Invalid API key")
            
            client = SeedanceClient("sk-video-1234567890abcdef")
            
            with pytest.raises(AuthenticationError):
                await client.generate_video(prompt="test")
    
    @pytest.mark.asyncio
    async def test_get_task_success(self):
        """Test successful task retrieval"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "id": "task_123",
                "status": "completed",
                "model": "seedance-2.0",
                "task_type": "text_to_video",
                "created_at": "2025-01-01T12:00:00Z",
                "updated_at": "2025-01-01T12:01:00Z",
                "result": {
                    "video_url": "https://cdn.example.com/video.mp4",
                    "duration": 8,
                    "resolution": "1080p",
                    "has_audio": True
                }
            }
        }
        
        with patch.object(SeedanceClient, '_request_async', return_value=mock_response):
            client = SeedanceClient("sk-video-1234567890abcdef")
            
            task = await client.get_task("task_123")
            
            assert task.id == "task_123"
            assert task.status == TaskStatus.COMPLETED
            assert str(task.result.video_url) == "https://cdn.example.com/video.mp4"
    
    @pytest.mark.asyncio
    async def test_get_task_not_found(self):
        """Test task not found error"""
        with patch.object(SeedanceClient, '_request_async') as mock_request:
            mock_request.side_effect = TaskNotFoundError("Task not found", 404)
            
            client = SeedanceClient("sk-video-1234567890abcdef")
            
            with pytest.raises(TaskNotFoundError):
                await client.get_task("nonexistent_task")
    
    @pytest.mark.asyncio
    async def test_list_tasks_success(self):
        """Test successful task listing"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "tasks": [
                    {
                        "id": "task_1",
                        "status": "completed",
                        "model": "seedance-2.0",
                        "task_type": "text_to_video",
                        "created_at": "2025-01-01T12:00:00Z",
                        "updated_at": "2025-01-01T12:01:00Z"
                    },
                    {
                        "id": "task_2", 
                        "status": "pending",
                        "model": "kling-v2-6",
                        "task_type": "image_to_video",
                        "created_at": "2025-01-01T12:02:00Z",
                        "updated_at": "2025-01-01T12:02:00Z"
                    }
                ],
                "pagination": {
                    "page": 1,
                    "limit": 20,
                    "total": 2,
                    "total_pages": 1
                }
            }
        }
        
        with patch.object(SeedanceClient, '_request_async', return_value=mock_response):
            client = SeedanceClient("sk-video-1234567890abcdef")
            
            response = await client.list_tasks(page=1, limit=20)
            
            assert len(response.data.tasks) == 2
            assert response.data.pagination.page == 1
            assert response.data.pagination.total == 2
    
    @pytest.mark.asyncio
    async def test_get_credits_success(self):
        """Test successful credits retrieval"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "total": 1000,
                "used": 250,
                "remaining": 750,
                "last_updated": "2025-01-01T12:00:00Z"
            }
        }
        
        with patch.object(SeedanceClient, '_request_async', return_value=mock_response):
            client = SeedanceClient("sk-video-1234567890abcdef")
            
            credits = await client.get_credits()
            
            assert credits.total == 1000
            assert credits.used == 250
            assert credits.remaining == 750
    
    @pytest.mark.asyncio
    async def test_wait_for_completion_success(self):
        """Test successful wait for completion"""
        # Mock get_task to return pending then completed
        pending_task = MagicMock()
        pending_task.status = TaskStatus.PENDING
        pending_task.id = "task_123"
        
        completed_task = MagicMock()
        completed_task.status = TaskStatus.COMPLETED
        completed_task.id = "task_123"
        completed_task.result.video_url = "https://cdn.example.com/video.mp4"
        
        with patch.object(SeedanceClient, 'get_task', side_effect=[pending_task, completed_task]):
            client = SeedanceClient("sk-video-1234567890abcdef")
            
            with patch('asyncio.sleep', return_value=None):  # Speed up test
                result = await client.wait_for_completion("task_123", poll_interval=0.1)
                
                assert result.status == TaskStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_wait_for_completion_timeout(self):
        """Test wait for completion timeout"""
        # Mock get_task to always return pending
        pending_task = MagicMock()
        pending_task.status = TaskStatus.PENDING
        pending_task.id = "task_123"
        
        with patch.object(SeedanceClient, 'get_task', return_value=pending_task):
            client = SeedanceClient("sk-video-1234567890abcdef")
            
            with patch('asyncio.sleep', return_value=None):
                with patch('time.time', side_effect=[0, 10]):  # Simulate 10 seconds passing
                    with pytest.raises(Exception):  # TaskTimeoutError
                        await client.wait_for_completion("task_123", timeout=5)
    
    @pytest.mark.asyncio
    async def test_wait_for_completion_failed(self):
        """Test wait for completion when task fails"""
        failed_task = MagicMock()
        failed_task.status = TaskStatus.FAILED
        failed_task.id = "task_123"
        failed_task.error = "Processing failed"
        
        with patch.object(SeedanceClient, 'get_task', return_value=failed_task):
            client = SeedanceClient("sk-video-1234567890abcdef")
            
            with pytest.raises(Exception):  # TaskFailedError
                await client.wait_for_completion("task_123")
    
    @pytest.mark.asyncio
    async def test_cancel_task_success(self):
        """Test successful task cancellation"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "id": "task_123",
                "status": "cancelled",
                "model": "seedance-2.0",
                "task_type": "text_to_video",
                "created_at": "2025-01-01T12:00:00Z",
                "updated_at": "2025-01-01T12:05:00Z"
            }
        }
        
        with patch.object(SeedanceClient, '_request_async', return_value=mock_response):
            client = SeedanceClient("sk-video-1234567890abcdef")
            
            task = await client.cancel_task("task_123")
            
            assert task.status == TaskStatus.CANCELLED
    
    def test_generate_video_sync(self):
        """Test synchronous video generation"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "id": "task_sync",
                "status": "pending",
                "model": "seedance-2.0",
                "task_type": "text_to_video",
                "created_at": "2025-01-01T12:00:00Z",
                "updated_at": "2025-01-01T12:00:00Z"
            }
        }
        
        with patch.object(SeedanceClient, '_request_sync', return_value=mock_response):
            client = SeedanceClient("sk-video-1234567890abcdef")
            
            task = client.generate_video_sync(GenerationRequest(prompt="test sync"))
            
            assert task.id == "task_sync"
            assert task.status == TaskStatus.PENDING
    
    def test_webhook_signature_verification(self):
        """Test webhook signature verification"""
        client = SeedanceClient(
            api_key="sk-video-1234567890abcdef",
            webhook_secret="test-secret"
        )
        
        payload = b'{"event": "test"}'
        signature = client.verify_webhook_signature(payload, "invalid")
        
        assert signature is False
    
    def test_context_managers(self):
        """Test async and sync context managers"""
        client = SeedanceClient("sk-video-1234567890abcdef")
        
        # Test that context managers don't raise errors
        async def test_async_context():
            async with client:
                pass
        
        def test_sync_context():
            with client:
                pass
        
        # These should not raise exceptions
        import asyncio
        asyncio.run(test_async_context())
        test_sync_context()


if __name__ == "__main__":
    pytest.main([__file__])
