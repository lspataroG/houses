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
Shared utilities for Gemini text generation.
"""

from google.genai import types
from .llm_utils import get_part, get_generate_content_config, retry_with_exponential_backoff


@retry_with_exponential_backoff(max_retries=5)
def generate_gemini(
    text_images_pieces,
    client,
    schema=None,
    config=None,
    model="gemini-2.5-flash"
):
    """
    Generate text content using Gemini.

    Args:
        text_images_pieces: List of text strings, image bytes, or GCS paths
        client: Gemini client instance
        schema: Optional response schema for structured output
        config: Optional GenerateContentConfig (uses default if None)
        model: Model to use (default: "gemini-2.5-flash")

    Returns:
        str: Generated text response (stripped)
    """
    parts = [get_part(x) for x in text_images_pieces]
    contents = [types.Content(role="user", parts=parts)]

    if config is None:
        config = get_generate_content_config(
            temperature=0,
            response_modalities=["TEXT"],
            response_mime_type="application/json" if schema else "text/plain",
            response_schema=schema
        )

    result = client.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )
    return result.candidates[0].content.parts[0].text.strip()
