# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Shared LLM utilities for creating Gemini content parts.
Used by both text generation (gemini) and image generation (nano_banana).
"""

from google.genai import types
from google.genai.errors import ClientError
from typing import List, Optional, Callable, Any
import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)


def retry_with_exponential_backoff(
    max_retries: int = 5,
    initial_delay: float = 1.0,
    exponential_base: float = 5.0,
    max_delay: float = 60.0,
    exceptions: tuple = (ClientError,),
):
    """
    Decorator for retrying a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts (default: 5)
        initial_delay: Initial delay in seconds (default: 1.0)
        exponential_base: Base for exponential backoff (default: 5.0)
                         Delays: 1s, 5s, 25s, 60s (capped), 60s
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        exceptions: Tuple of exception types to catch (default: (ClientError,))

    Returns:
        Decorated function that retries on failure with exponential backoff
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retry_num = 0
            while retry_num <= max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if retry_num == max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} retries: {e}"
                        )
                        return None

                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay * (exponential_base**retry_num), max_delay
                    )
                    retry_num += 1

                    logger.warning(
                        f"{func.__name__} failed (attempt {retry_num}/{max_retries + 1}), retrying in {delay:.1f}s: {e}"
                    )
                    time.sleep(delay)

            return None

        return wrapper

    return decorator


def get_mime_type_from_bytes(data):
    """
    Detect MIME type from file signature (magic bytes).

    Args:
        data: Bytes to analyze

    Returns:
        str: Detected MIME type (e.g., "image/png", "video/mp4", "image/jpeg")
    """
    if len(data) < 12:
        return "application/octet-stream"

    # PNG signature
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"

    # JPEG signature
    if data[:2] == b"\xff\xd8":
        return "image/jpeg"

    # WebP signature
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"

    # GIF signature
    if data[:3] == b"GIF":
        return "image/gif"

    # MP4/MOV signatures
    if b"ftyp" in data[4:12]:
        return "video/mp4"

    # WebM signature
    if data[:4] == b"\x1a\x45\xdf\xa3":
        return "video/webm"

    # AVI signature
    if data[:4] == b"RIFF" and b"AVI " in data[:16]:
        return "video/avi"

    return "application/octet-stream"


def get_mime_type_from_path(path):
    """
    Detect MIME type from file extension in path.

    Args:
        path: File path or URL

    Returns:
        str: Detected MIME type
    """
    path_lower = path.lower()

    # Image formats
    if path_lower.endswith(".png"):
        return "image/png"
    elif path_lower.endswith(".webp"):
        return "image/webp"
    elif path_lower.endswith(".gif"):
        return "image/gif"
    elif path_lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"

    # Video formats
    elif path_lower.endswith(".mp4"):
        return "video/mp4"
    elif path_lower.endswith(".webm"):
        return "video/webm"
    elif path_lower.endswith(".avi"):
        return "video/avi"
    elif path_lower.endswith(".mov"):
        return "video/mp4"  # MOV uses mp4 container

    # Default to JPEG for images
    return "image/jpeg"


def get_part(input_piece, return_dict=False):
    """
    Convert input to appropriate Part type (text, image/video bytes, or GCS path).
    Auto-detects MIME type from bytes or file extension.

    Args:
        input_piece: Can be a string (text or GCS path) or bytes (image/video)
        return_dict: If True, returns the part as a JSON dict

    Returns:
        Part object or dict representation
    """
    if isinstance(input_piece, bytes):
        # Auto-detect and create appropriate part (image or video)
        mime_type = get_mime_type_from_bytes(input_piece)
        part = types.Part.from_bytes(data=input_piece, mime_type=mime_type)
    elif isinstance(input_piece, str) and "gs://" in input_piece:
        mime_type = get_mime_type_from_path(input_piece)
        part = types.Part.from_uri(file_uri=input_piece, mime_type=mime_type)
    else:
        part = types.Part.from_text(text=input_piece)

    if return_dict:
        return part.to_json_dict()
    return part


def get_generate_content_config(
    temperature: float = 1,
    top_p: float = 0.95,
    max_output_tokens: int = 32768,
    response_modalities: Optional[List[str]] = None,
    response_mime_type: Optional[str] = None,
    response_schema: Optional[dict] = None,
    safety_off: bool = True,
) -> types.GenerateContentConfig:
    """
    Create standard configuration for Gemini content generation.

    Args:
        temperature: Temperature for generation (default: 1)
        top_p: Top-p sampling parameter (default: 0.95)
        max_output_tokens: Maximum tokens to generate (default: 32768)
        response_modalities: List of response types (default: None/empty)
                           Examples: ["IMAGE", "TEXT"], ["TEXT"], ["IMAGE"]
        response_mime_type: MIME type for response (e.g., "application/json", "text/plain")
        response_schema: Schema for structured output (for JSON responses)
        safety_off: If True, disables all safety settings (default: True)

    Returns:
        GenerateContentConfig object
    """
    config_params = {
        "temperature": temperature,
        "top_p": top_p,
        "max_output_tokens": max_output_tokens,
    }

    if response_modalities is not None:
        config_params["response_modalities"] = response_modalities

    if response_mime_type is not None:
        config_params["response_mime_type"] = response_mime_type

    if response_schema is not None:
        config_params["response_schema"] = response_schema

    if safety_off:
        config_params["safety_settings"] = [
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"
            ),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
        ]

    return types.GenerateContentConfig(**config_params)
