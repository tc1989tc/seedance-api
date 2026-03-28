"""
Utility functions for Seedance SDK
"""
import re
from typing import Dict, Any


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key format
    
    Args:
        api_key: API key to validate
        
    Returns:
        bool: True if valid format
    """
    if not api_key or not isinstance(api_key, str):
        return False
    
    # API keys should start with 'sk-video-' followed by alphanumeric characters
    pattern = r'^sk-video-[a-zA-Z0-9]{16,}$'
    return bool(re.match(pattern, api_key))


def parse_error_response(response_data: Dict[str, Any]) -> str:
    """
    Parse error message from API response
    
    Args:
        response_data: Response data from API
        
    Returns:
        str: Error message
    """
    if isinstance(response_data, dict):
        # Try different error field names
        for field in ['error', 'message', 'detail', 'error_description']:
            if field in response_data and response_data[field]:
                return str(response_data[field])
        
        # If no error field found, return the whole response as string
        return str(response_data)
    
    return str(response_data)


def format_duration(seconds: int) -> str:
    """
    Format duration in human-readable format
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration (e.g., "2min 30s")
    """
    if seconds < 60:
        return f"{seconds}s"
    
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    
    if remaining_seconds == 0:
        return f"{minutes}min"
    
    return f"{minutes}min {remaining_seconds}s"


def format_file_size(bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        bytes: File size in bytes
        
    Returns:
        str: Formatted file size
    """
    if bytes < 1024:
        return f"{bytes} B"
    
    kb = bytes / 1024
    if kb < 1024:
        return f"{kb:.1f} KB"
    
    mb = kb / 1024
    if mb < 1024:
        return f"{mb:.1f} MB"
    
    gb = mb / 1024
    return f"{gb:.1f} GB"


def calculate_estimated_cost(
    model: str,
    duration: int,
    resolution: str,
    with_audio: bool = False
) -> int:
    """
    Calculate estimated credits cost for generation
    
    Args:
        model: Model name
        duration: Duration in seconds
        resolution: Resolution
        with_audio: Whether to generate audio
        
    Returns:
        int: Estimated credits cost
    """
    # Seedance 2.0 pricing
    if model == "seedance-2.0":
        if resolution == "480p":
            if duration == 4:
                return 20 if with_audio else 15
            elif duration == 8:
                return 40 if with_audio else 25
            elif duration == 12:
                return 60 if with_audio else 45
        elif resolution == "720p":
            if duration == 4:
                return 43 if with_audio else 30
            elif duration == 8:
                return 86 if with_audio else 45
            elif duration == 12:
                return 129 if with_audio else 90
        elif resolution == "1080p":
            if duration == 4:
                return 90 if with_audio else 50
            elif duration == 8:
                return 180 if with_audio else 100
            elif duration == 12:
                return 270 if with_audio else 150
    
    # Kling pricing (text-to-video)
    elif model == "kling-v2-6":
        if duration == 5:
            return 150  # Text-to-video base price
        elif duration == 10:
            return 280
    
    # Sora 2 pricing
    elif model == "sora-2":
        if resolution == "1080p":
            return 85  # HD
        else:
            return 65  # SD
    
    # Default fallback
    return 100


def sanitize_prompt(prompt: str) -> str:
    """
    Sanitize user prompt for API submission
    
    Args:
        prompt: User prompt
        
    Returns:
        str: Sanitized prompt
    """
    if not prompt:
        return ""
    
    # Remove excessive whitespace
    prompt = re.sub(r'\s+', ' ', prompt.strip())
    
    # Remove or replace potentially problematic characters
    prompt = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', prompt)
    
    # Limit length
    if len(prompt) > 1000:
        prompt = prompt[:997] + "..."
    
    return prompt


def extract_video_id_from_url(url: str) -> str:
    """
    Extract video ID from URL (if applicable)
    
    Args:
        url: Video URL
        
    Returns:
        str: Video ID or empty string
    """
    # This is a placeholder implementation
    # Adjust based on your actual URL patterns
    import re
    
    # Example: extract from URLs like https://cdn.example.com/videos/abc123.mp4
    match = re.search(r'/([^/]+)\.(mp4|mov|avi)$', url)
    if match:
        return match.group(1)
    
    return ""


def create_progress_callback(verbose: bool = False):
    """
    Create a progress callback function for task monitoring
    
    Args:
        verbose: Whether to print detailed progress
        
    Returns:
        Callable: Progress callback function
    """
    def callback(task):
        from .models import TaskStatus
        
        if verbose:
            print(f"Task {task.id}: {task.status.value}")
            if task.estimated_time:
                print(f"  Estimated time: {task.estimated_time}s")
            if task.credits_consumed:
                print(f"  Credits consumed: {task.credits_consumed}")
        else:
            # Simple progress indicator
            status_map = {
                TaskStatus.PENDING: "⏳",
                TaskStatus.PROCESSING: "🔄",
                TaskStatus.COMPLETED: "✅",
                TaskStatus.FAILED: "❌",
                TaskStatus.CANCELLED: "🚫"
            }
            print(status_map.get(task.status, "❓"), end="", flush=True)
    
    return callback
