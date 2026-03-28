#!/usr/bin/env python3
"""
Webhook examples for Seedance SDK
"""
import asyncio
import os
from seedance import create_webhook_server, WebhookHandler, TaskData


def webhook_server_example():
    """Example of running a webhook server"""
    print("=== Webhook Server Example ===")
    
    # Create webhook server with default handlers
    webhook_secret = os.getenv("SEEDANCE_WEBHOOK_SECRET", "your-webhook-secret")
    server = create_webhook_server(webhook_secret)
    
    # Add custom handlers
    @server.handler.on_task_completed
    def custom_completed_handler(task: TaskData):
        print(f"🎉 Custom handler: Task {task.id} completed!")
        print(f"   Model: {task.model}")
        print(f"   Duration: {task.result.duration}s")
        
        # You could:
        # - Update your database
        # - Send notifications
        # - Process the video further
        # - Update user credits
    
    @server.handler.on_task_failed
    def custom_failed_handler(task: TaskData):
        print(f"💥 Custom handler: Task {task.id} failed!")
        print(f"   Error: {task.error}")
        
        # You could:
        # - Log the error
        # - Notify users
        # - Retry with different parameters
        # - Issue refunds
    
    print(f"Starting webhook server on http://localhost:8000")
    print("Send webhooks to: http://localhost:8000/webhook")
    print("Health check: http://localhost:8000/health")
    print("\nPress Ctrl+C to stop the server")
    
    # Run server (this blocks)
    server.run(host="localhost", port=8000)


async def webhook_handler_example():
    """Example of using webhook handler in your own endpoint"""
    print("\n=== Webhook Handler Example ===")
    
    webhook_secret = os.getenv("SEEDANCE_WEBHOOK_SECRET", "your-webhook-secret")
    handler = WebhookHandler(webhook_secret)
    
    # Define handlers
    completed_tasks = []
    failed_tasks = []
    
    @handler.on_task_completed
    async def handle_completed(task: TaskData):
        completed_tasks.append(task)
        print(f"✅ Completed: {task.id}")
        
        # Example: Save to database
        # await save_video_result(task)
        
        # Example: Send notification
        # await send_user_notification(task.user_id, "Your video is ready!")
        
        # Example: Queue additional processing
        # await queue_video_processing(task.result.video_url)
    
    @handler.on_task_failed
    async def handle_failed(task: TaskData):
        failed_tasks.append(task)
        print(f"❌ Failed: {task.id} - {task.error}")
        
        # Example: Log error
        # await log_error(task.error, task.id)
        
        # Example: Notify support
        # await notify_support(f"Task {task.id} failed: {task.error}")
    
    @handler.on_any_event
    async def handle_any_event(webhook_payload):
        print(f"📡 Event: {webhook_payload.event}")
        print(f"   Timestamp: {webhook_payload.timestamp}")
    
    # Simulate webhook processing
    print("Simulating webhook processing...")
    
    # This would normally come from your HTTP endpoint
    mock_payload = b'''
    {
        "event": "task.completed",
        "timestamp": "2025-01-01T12:00:00Z",
        "data": {
            "id": "task_123456",
            "status": "completed",
            "model": "seedance-2.0",
            "task_type": "text_to_video",
            "created_at": "2025-01-01T11:58:00Z",
            "updated_at": "2025-01-01T12:00:00Z",
            "credits_consumed": 180,
            "result": {
                "video_url": "https://cdn.example.com/videos/task_123456.mp4",
                "thumbnail_url": "https://cdn.example.com/thumbnails/task_123456.jpg",
                "duration": 8,
                "resolution": "1080p",
                "has_audio": true,
                "file_size": 15728640
            }
        }
    }
    '''
    
    # Generate mock signature (in real scenario, this comes from Seedance)
    import hashlib
    import hmac
    mock_signature = hmac.new(
        webhook_secret.encode(),
        mock_payload,
        hashlib.sha256
    ).hexdigest()
    
    # Process webhook
    try:
        webhook_payload = await handler.process_webhook(
            mock_payload,
            mock_signature,
            raise_on_error=True
        )
        
        print(f"\n✅ Webhook processed successfully!")
        print(f"   Event: {webhook_payload.event}")
        print(f"   Task ID: {webhook_payload.data.id}")
        print(f"   Video URL: {webhook_payload.data.result.video_url}")
        
    except Exception as e:
        print(f"❌ Webhook processing failed: {e}")


def flask_webhook_example():
    """Example of integrating webhook handler with Flask"""
    print("\n=== Flask Webhook Example ===")
    
    webhook_secret = os.getenv("SEEDANCE_WEBHOOK_SECRET", "your-webhook-secret")
    handler = WebhookHandler(webhook_secret)
    
    try:
        from flask import Flask, request, jsonify
        
        app = Flask(__name__)
        
        @app.route("/webhook", methods=["POST"])
        def webhook_endpoint():
            try:
                payload = request.data
                signature = request.headers.get("X-Seedance-Signature")
                
                if not signature:
                    return jsonify({"error": "Missing signature"}), 400
                
                # Process webhook asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    webhook_payload = loop.run_until_complete(
                        handler.process_webhook(payload, signature, raise_on_error=True)
                    )
                    return jsonify({"status": "ok"})
                finally:
                    loop.close()
                    
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @app.route("/health")
        def health_check():
            return jsonify({"status": "healthy"})
        
        print("Flask webhook example code generated!")
        print("To run:")
        print("pip install flask")
        print("python examples/webhook_example.py")
        print("Then run: flask run")
        
        return app
        
    except ImportError:
        print("Flask not installed. Install with: pip install flask")
        return None


def django_webhook_example():
    """Example of integrating webhook handler with Django"""
    print("\n=== Django Webhook Example ===")
    
    webhook_code = '''
# Django views.py example
import json
import asyncio
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from seedance import WebhookHandler

# Initialize webhook handler
webhook_secret = "your-webhook-secret"
handler = WebhookHandler(webhook_secret)

@handler.on_task_completed
async def handle_completed(task):
    # Handle completed task
    pass

@handler.on_task_failed  
async def handle_failed(task):
    # Handle failed task
    pass

@csrf_exempt
@require_http_methods(["POST"])
def webhook_endpoint(request):
    try:
        payload = request.body
        signature = request.headers.get("X-Seedance-Signature")
        
        if not signature:
            return JsonResponse({"error": "Missing signature"}, status=400)
        
        # Process webhook
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            webhook_payload = loop.run_until_complete(
                handler.process_webhook(payload, signature, raise_on_error=True)
            )
            return JsonResponse({"status": "ok"})
        finally:
            loop.close()
            
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def health_check(request):
    return JsonResponse({"status": "healthy"})
'''
    
    print("Django webhook example code:")
    print(webhook_code)


if __name__ == "__main__":
    print("Seedance SDK Webhook Examples")
    print("=" * 50)
    
    # Uncomment to run webhook server
    # webhook_server_example()
    
    # Run other examples
    asyncio.run(webhook_handler_example())
    flask_webhook_example()
    django_webhook_example()
    
    print("\n" + "=" * 50)
    print("Webhook examples completed!")
    print("\nTo test with real webhooks:")
    print("1. Set SEEDANCE_WEBHOOK_SECRET environment variable")
    print("2. Configure your Seedance dashboard to send webhooks to your endpoint")
    print("3. Run one of the webhook server examples")
