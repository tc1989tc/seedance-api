#!/usr/bin/env python3
"""
Basic usage examples for Seedance SDK
"""
import asyncio
import os
from seedance import SeedanceClient, Model, Resolution, create_progress_callback


async def basic_async_example():
    """Basic async example"""
    print("=== Basic Async Example ===")
    
    # Initialize client
    api_key = os.getenv("SEEDANCE_API_KEY", "sk-video-xxxxx")
    
    async with SeedanceClient(api_key) as client:
        try:
            # Generate video
            print("Generating video...")
            task = await client.generate_video(
                prompt="A cinematic aerial shot of a mountain range at sunrise, golden light, volumetric clouds",
                model=Model.SEEDANCE_2_0,
                duration=8,
                resolution=Resolution.P1080P,
                generate_audio=True
            )
            
            print(f"Task created: {task.id}")
            print(f"Estimated time: {task.estimated_time}s")
            
            # Wait for completion with progress
            progress_callback = create_progress_callback(verbose=True)
            result = await client.wait_for_completion(
                task.id, 
                timeout=300,  # 5 minutes timeout
                on_progress=progress_callback
            )
            
            print(f"\n✅ Video ready!")
            print(f"URL: {result.result.video_url}")
            print(f"Duration: {result.result.duration}s")
            print(f"Resolution: {result.result.resolution}")
            print(f"File size: {result.result.file_size} bytes")
            
        except Exception as e:
            print(f"❌ Error: {e}")


def basic_sync_example():
    """Basic sync example"""
    print("\n=== Basic Sync Example ===")
    
    api_key = os.getenv("SEEDANCE_API_KEY", "sk-video-xxxxx")
    
    with SeedanceClient(api_key) as client:
        try:
            # Generate video
            print("Generating video...")
            task = client.generate_video_sync(
                prompt="A futuristic city at night with neon lights reflecting on wet streets",
                model=Model.SEEDANCE_2_0,
                duration=4,
                resolution=Resolution.P720P,
                generate_audio=False
            )
            
            print(f"Task created: {task.id}")
            
            # Wait for completion
            result = client.wait_for_completion_sync(task.id, timeout=300)
            
            print(f"✅ Video ready!")
            print(f"URL: {result.result.video_url}")
            
        except Exception as e:
            print(f"❌ Error: {e}")


async def batch_generation_example():
    """Batch generation example"""
    print("\n=== Batch Generation Example ===")
    
    api_key = os.getenv("SEEDANCE_API_KEY", "sk-video-xxxxx")
    
    async with SeedanceClient(api_key) as client:
        prompts = [
            "A cat playing piano in a cozy room",
            "A dog surfing on a big wave",
            "A robot cooking in a modern kitchen"
        ]
        
        tasks = []
        
        # Submit all tasks
        for i, prompt in enumerate(prompts):
            try:
                task = await client.generate_video(
                    prompt=prompt,
                    model=Model.SEEDANCE_2_0,
                    duration=4,
                    resolution=Resolution.P720P
                )
                tasks.append(task)
                print(f"Task {i+1} submitted: {task.id}")
            except Exception as e:
                print(f"❌ Task {i+1} failed: {e}")
        
        # Wait for all tasks to complete
        print(f"\nWaiting for {len(tasks)} tasks to complete...")
        
        results = []
        for i, task in enumerate(tasks):
            try:
                result = await client.wait_for_completion(task.id, timeout=300)
                results.append(result)
                print(f"✅ Task {i+1} completed: {result.result.video_url}")
            except Exception as e:
                print(f"❌ Task {i+1} failed: {e}")
        
        print(f"\n{len(results)}/{len(tasks)} videos generated successfully")


async def image_to_video_example():
    """Image-to-video example"""
    print("\n=== Image-to-Video Example ===")
    
    api_key = os.getenv("SEEDANCE_API_KEY", "sk-video-xxxxx")
    
    async with SeedanceClient(api_key) as client:
        try:
            # Generate video from image
            task = await client.generate_video(
                prompt="The person slowly turns and smiles at the camera",
                image_urls=["https://example.com/portrait.jpg"],
                model=Model.KLING_V2_6,
                duration=5,
                resolution=Resolution.P1080P
            )
            
            print(f"Image-to-video task created: {task.id}")
            
            result = await client.wait_for_completion(task.id, timeout=300)
            print(f"✅ Video ready: {result.result.video_url}")
            
        except Exception as e:
            print(f"❌ Error: {e}")


async def task_management_example():
    """Task management example"""
    print("\n=== Task Management Example ===")
    
    api_key = os.getenv("SEEDANCE_API_KEY", "sk-video-xxxxx")
    
    async with SeedanceClient(api_key) as client:
        try:
            # Get credits info
            credits = await client.get_credits()
            print(f"Credits: {credits.remaining}/{credits.total}")
            
            # List recent tasks
            tasks_response = await client.list_tasks(page=1, limit=5)
            print(f"\nRecent tasks ({len(tasks_response.data.tasks)}):")
            
            for task in tasks_response.data.tasks:
                print(f"  {task.id}: {task.status.value} - {task.model}")
            
            # Get specific task details
            if tasks_response.data.tasks:
                first_task = tasks_response.data.tasks[0]
                task_detail = await client.get_task(first_task.id)
                print(f"\nTask details for {task_detail.id}:")
                print(f"  Status: {task_detail.status.value}")
                print(f"  Created: {task_detail.created_at}")
                if task_detail.credits_consumed:
                    print(f"  Credits consumed: {task_detail.credits_consumed}")
            
        except Exception as e:
            print(f"❌ Error: {e}")


def cost_estimation_example():
    """Cost estimation example"""
    print("\n=== Cost Estimation Example ===")
    
    from seedance import calculate_estimated_cost
    
    scenarios = [
        ("seedance-2.0", 4, "720p", False),
        ("seedance-2.0", 8, "1080p", True),
        ("seedance-2.0", 12, "1080p", True),
        ("kling-v2-6", 5, "1080p", False),
        ("kling-v2-6", 10, "1080p", False),
        ("sora-2", 10, "1080p", False),
    ]
    
    print("Cost estimation for different scenarios:")
    print("Model\t\tDuration\tResolution\tAudio\tCredits")
    print("-" * 60)
    
    for model, duration, resolution, with_audio in scenarios:
        credits = calculate_estimated_cost(model, duration, resolution, with_audio)
        print(f"{model}\t{duration}s\t\t{resolution}\t{with_audio}\t{credits}")


if __name__ == "__main__":
    print("Seedance SDK Examples")
    print("=" * 50)
    
    # Run examples
    asyncio.run(basic_async_example())
    basic_sync_example()
    asyncio.run(batch_generation_example())
    asyncio.run(image_to_video_example())
    asyncio.run(task_management_example())
    cost_estimation_example()
    
    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nTo run with your real API key:")
    print("export SEEDANCE_API_KEY=sk-video-your-real-key")
    print("python examples/basic_usage.py")
