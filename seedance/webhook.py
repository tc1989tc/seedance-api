"""
Webhook handling utilities for Seedance SDK
"""
import asyncio
from typing import Callable, Optional, Any
from datetime import datetime

from .models import WebhookPayload, TaskData, TaskStatus
from .exceptions import WebhookSignatureError


class WebhookHandler:
    """
    Webhook handler for processing Seedance webhook events
    
    Example:
        >>> handler = WebhookHandler(secret="your-webhook-secret")
        >>> 
        >>> @handler.on_task_completed
        >>> async def handle_completed(task: TaskData):
        ...     print(f"Video ready: {task.result.video_url}")
        >>> 
        >>> # In your webhook endpoint:
        >>> payload = await request.body()
        >>> signature = request.headers.get("X-Seedance-Signature")
        >>> await handler.process_webhook(payload, signature)
    """
    
    def __init__(self, secret: str):
        """
        Initialize webhook handler
        
        Args:
            secret: Webhook secret for signature verification
        """
        self.secret = secret
        self._completed_handlers: list[Callable] = []
        self._failed_handlers: list[Callable] = []
        self._all_handlers: list[Callable] = []
    
    def on_task_completed(self, func: Callable[[TaskData], Any]):
        """Decorator for task completed event handler"""
        self._completed_handlers.append(func)
        return func
    
    def on_task_failed(self, func: Callable[[TaskData], Any]):
        """Decorator for task failed event handler"""
        self._failed_handlers.append(func)
        return func
    
    def on_any_event(self, func: Callable[[WebhookPayload], Any]):
        """Decorator for any webhook event"""
        self._all_handlers.append(func)
        return func
    
    async def process_webhook(
        self,
        payload: bytes,
        signature: str,
        raise_on_error: bool = False
    ) -> WebhookPayload:
        """
        Process webhook payload
        
        Args:
            payload: Raw webhook payload bytes
            signature: Signature from webhook header
            raise_on_error: Whether to raise exceptions on handler errors
            
        Returns:
            WebhookPayload: Parsed webhook data
            
        Raises:
            WebhookSignatureError: If signature is invalid
        """
        import json
        import hashlib
        import hmac
        
        # Verify signature
        expected_signature = hmac.new(
            self.secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(expected_signature, signature):
            raise WebhookSignatureError("Invalid webhook signature")
        
        # Parse payload
        try:
            data = json.loads(payload.decode())
            webhook_payload = WebhookPayload(**data)
        except Exception as e:
            if raise_on_error:
                raise
            return None
        
        # Call handlers
        await self._call_handlers(webhook_payload, raise_on_error)
        
        return webhook_payload
    
    async def _call_handlers(
        self,
        webhook_payload: WebhookPayload,
        raise_on_error: bool = False
    ):
        """Call appropriate handlers based on event type"""
        task = webhook_payload.data
        
        # Call all-event handlers
        for handler in self._all_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(webhook_payload)
                else:
                    handler(webhook_payload)
            except Exception as e:
                if raise_on_error:
                    raise
                # Log error but continue processing
                print(f"Webhook handler error: {e}")
        
        # Call specific handlers
        if webhook_payload.event == "task.completed":
            for handler in self._completed_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(task)
                    else:
                        handler(task)
                except Exception as e:
                    if raise_on_error:
                        raise
                    print(f"Task completed handler error: {e}")
        
        elif webhook_payload.event == "task.failed":
            for handler in self._failed_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(task)
                    else:
                        handler(task)
                except Exception as e:
                    if raise_on_error:
                        raise
                    print(f"Task failed handler error: {e}")


class WebhookServer:
    """
    Simple webhook server for testing and development
    
    Example:
        >>> server = WebhookHandler(secret="test-secret")
        >>> 
        >>> @server.on_task_completed
        >>> def handle_completed(task):
        ...     print(f"Completed: {task.result.video_url}")
        >>> 
        >>> # Start server (for development)
        >>> server.run(host="localhost", port=8000)
    """
    
    def __init__(self, secret: str, handler: Optional[WebhookHandler] = None):
        """
        Initialize webhook server
        
        Args:
            secret: Webhook secret
            handler: Webhook handler instance
        """
        self.secret = secret
        self.handler = handler or WebhookHandler(secret)
        self.app = None
    
    def create_app(self):
        """Create FastAPI application for webhook handling"""
        try:
            from fastapi import FastAPI, Request, Response, HTTPException
            from fastapi.responses import JSONResponse
        except ImportError:
            raise ImportError("FastAPI is required for webhook server. Install with: pip install fastapi uvicorn")
        
        app = FastAPI(title="Seedance Webhook Server")
        
        @app.post("/webhook")
        async def webhook_endpoint(request: Request):
            try:
                payload = await request.body()
                signature = request.headers.get("X-Seedance-Signature")
                
                if not signature:
                    raise HTTPException(status_code=400, detail="Missing signature")
                
                webhook_payload = await self.handler.process_webhook(
                    payload, 
                    signature,
                    raise_on_error=True
                )
                
                return JSONResponse({"status": "ok"})
                
            except WebhookSignatureError as e:
                raise HTTPException(status_code=401, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.get("/health")
        async def health_check():
            return {"status": "healthy"}
        
        return app
    
    def run(self, host: str = "localhost", port: int = 8000, **kwargs):
        """Run the webhook server"""
        if not self.app:
            self.app = self.create_app()
        
        try:
            import uvicorn
            uvicorn.run(self.app, host=host, port=port, **kwargs)
        except ImportError:
            raise ImportError("Uvicorn is required for webhook server. Install with: pip install uvicorn")


# Convenience function for quick webhook testing
def create_webhook_server(secret: str, **kwargs) -> WebhookServer:
    """
    Create a webhook server with default handlers
    
    Args:
        secret: Webhook secret
        **kwargs: Additional server configuration
        
    Returns:
        WebhookServer: Configured webhook server
    """
    server = WebhookServer(secret)
    
    # Add default handlers for demonstration
    @server.handler.on_task_completed
    def default_completed_handler(task: TaskData):
        print(f"✅ Task completed: {task.id}")
        if task.result:
            print(f"   Video URL: {task.result.video_url}")
            print(f"   Duration: {task.result.duration}s")
            print(f"   Resolution: {task.result.resolution}")
    
    @server.handler.on_task_failed
    def default_failed_handler(task: TaskData):
        print(f"❌ Task failed: {task.id}")
        print(f"   Error: {task.error}")
    
    return server
