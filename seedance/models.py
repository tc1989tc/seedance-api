"""
Data models for Seedance API
"""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl, field_validator


class Model(str, Enum):
    """Available AI models"""
    SEEDANCE_2_0 = "seedance-2.0"
    KLING_V2_6 = "kling-v2-6"
    SORA_2 = "sora-2"


class Resolution(str, Enum):
    """Video resolution options"""
    P480 = "480p"
    P720 = "720p"
    P1080 = "1080p"


class Duration(int, Enum):
    """Video duration options in seconds"""
    SEEDANCE_4 = 4
    SEEDANCE_8 = 8
    SEEDANCE_12 = 12
    KLING_5 = 5
    KLING_10 = 10
    SORA_10 = 10


class AspectRatio(str, Enum):
    """Video aspect ratio options"""
    R16_9 = "16:9"
    R9_16 = "9:16"
    R1_1 = "1:1"
    R4_3 = "4:3"
    R3_4 = "3:4"


class TaskStatus(str, Enum):
    """Task status values"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """Task type values"""
    TEXT_TO_VIDEO = "text_to_video"
    IMAGE_TO_VIDEO = "image_to_video"


class GenerationRequest(BaseModel):
    """Request model for video generation"""
    model: Model = Field(default=Model.SEEDANCE_2_0, description="AI model to use")
    prompt: str = Field(..., min_length=1, max_length=1000, description="Text prompt for generation")
    image_urls: Optional[List[HttpUrl]] = Field(default=None, description="Images for image-to-video")
    duration: Optional[int] = Field(default=None, description="Video duration in seconds")
    aspect_ratio: AspectRatio = Field(default=AspectRatio.R16_9, description="Video aspect ratio")
    resolution: Optional[Resolution] = Field(default=None, description="Output resolution")
    generate_audio: bool = Field(default=False, description="Generate background audio")
    callback_url: Optional[HttpUrl] = Field(default=None, description="Webhook callback URL")

    @field_validator('duration')
    @classmethod
    def validate_duration(cls, v, info):
        """Validate duration based on model"""
        if v is None:
            return v
            
        model = values.get('model', Model.SEEDANCE_2_0)
        
        if model == Model.SEEDANCE_2_0:
            if v not in [4, 8, 12]:
                raise ValueError("Seedance 2.0 only supports durations: 4, 8, 12 seconds")
        elif model == Model.KLING_V2_6:
            if v not in [5, 10]:
                raise ValueError("Kling v2.6 only supports durations: 5, 10 seconds")
        elif model == Model.SORA_2:
            if v != 10:
                raise ValueError("Sora 2 only supports duration: 10 seconds")
        
        return v

    @field_validator('image_urls')
    @classmethod
    def validate_image_urls(cls, v, info):
        """Validate image_urls for image-to-video models"""
        if v and len(v) > 0:
            model = info.data.get('model', Model.SEEDANCE_2_0)
            if model == Model.SORA_2:
                raise ValueError("Sora 2 does not support image-to-video")
        return v


class GenerationResponse(BaseModel):
    """Response model for generation request"""
    success: bool
    data: "TaskData"


class TaskData(BaseModel):
    """Task data model"""
    id: str = Field(..., description="Unique task ID")
    status: TaskStatus
    model: Model
    task_type: TaskType
    created_at: datetime
    updated_at: datetime
    estimated_time: Optional[int] = Field(default=None, description="Estimated processing time in seconds")
    credits_consumed: Optional[int] = Field(default=None, description="Credits consumed for this task")
    result: Optional["TaskResult"] = Field(default=None, description="Task result if completed")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class TaskResult(BaseModel):
    """Task result model"""
    video_url: HttpUrl
    thumbnail_url: Optional[HttpUrl] = None
    duration: int
    resolution: Resolution
    has_audio: bool
    file_size: Optional[int] = Field(default=None, description="File size in bytes")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class TaskListResponse(BaseModel):
    """Response model for task list"""
    success: bool
    data: "TaskListData"


class TaskListData(BaseModel):
    """Task list data model"""
    tasks: List[TaskData]
    pagination: "PaginationInfo"


class PaginationInfo(BaseModel):
    """Pagination information"""
    page: int
    limit: int
    total: int
    total_pages: int


class WebhookPayload(BaseModel):
    """Webhook payload model"""
    event: Literal["task.completed", "task.failed"]
    data: TaskData
    timestamp: datetime
    signature: Optional[str] = None  # HMAC signature for verification


class CreditsInfo(BaseModel):
    """Credits information model"""
    total: int
    used: int
    remaining: int
    last_updated: datetime


# Forward references for circular imports
GenerationResponse.model_rebuild()
TaskListResponse.model_rebuild()
