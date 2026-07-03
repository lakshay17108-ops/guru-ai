"""
LLM Service — Google Gemini & OpenRouter structured output integration.

Uses the google-genai SDK's native structured output feature:
  - Passes our Pydantic LearningPath model as response_schema
  - Gemini is constrained to output valid JSON matching the schema
  - SDK returns response.parsed — already a Pydantic model instance

For OpenRouter (free LLaMA), we manually call the API and parse JSON,
with full error handling for HTTP failures, network errors, and schema
validation failures.
"""

import json
import logging
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import ValidationError

from google import genai
from google.genai import types

from app.models.schemas import LearningPath

logger = logging.getLogger(__name__)

# --- Prompt Template ---
SYSTEM_PROMPT = """You are an expert curriculum designer and educator. Your task is to create comprehensive, structured learning paths for any topic.

Guidelines for high-quality curricula:
- Create 3-5 phases that progress from fundamentals to advanced topics
- Each phase should have 2-3 milestones
- Each milestone should have 3-5 specific, measurable learning objectives
- Suggest 2-4 real search queries the learner can use to find materials
- Provide 2-3 real, existing learning resources with actual URLs (documentation sites, tutorials, YouTube channels, courses)
- Each milestone project should be hands-on and build progressively on prior milestones
- Milestone IDs should follow the format P{phase}_M{milestone} (e.g., P1_M1, P2_M3)
- Estimated time should be realistic (e.g., "8 weeks", "12 weeks")
- Tailor the depth and pacing to the specified difficulty level"""

USER_PROMPT_TEMPLATE = """Create a detailed learning path for the following:

Topic: {topic}
Difficulty Level: {difficulty}

Generate a comprehensive, multi-phase curriculum with realistic timelines, actual resources, and hands-on projects."""

# Explicit schema prompt used for OpenRouter (free models need extra guidance)
OPENROUTER_SYSTEM_PROMPT = SYSTEM_PROMPT + """

CRITICAL: You MUST respond with ONLY a valid JSON object that exactly matches this schema.
No markdown, no code fences, no explanation — raw JSON only.

Required JSON structure:
{
  "topic": "string",
  "estimated_time": "string (e.g. '8 weeks')",
  "difficulty": "string (beginner|intermediate|advanced)",
  "curriculum": [
    {
      "phase": 1,
      "phase_title": "string",
      "milestones": [
        {
          "milestone_id": "P1_M1",
          "title": "string",
          "objectives": ["string", "string", "string"],
          "suggested_queries": ["string", "string"],
          "resources": [
            {"resource_title": "string", "url": "https://..."}
          ],
          "milestone_project": {
            "project_title": "string",
            "description": "string"
          }
        }
      ]
    }
  ]
}"""


class LLMServiceError(Exception):
    """Base exception for LLM service errors."""
    pass


class APIKeyMissingError(LLMServiceError):
    """Raised when the Google API key is not configured."""
    pass


class LLMTimeoutError(LLMServiceError):
    """Raised when the Gemini API call times out."""
    pass


class LLMRateLimitError(LLMServiceError):
    """Raised when we hit Gemini's rate limit."""
    pass


def _call_openrouter(
    topic: str,
    difficulty: str,
    api_key: str,
    model_name: str,
) -> LearningPath:
    """Call OpenRouter as a free/low-cost alternative provider."""
    if not api_key:
        raise APIKeyMissingError("OpenRouter API key is not configured.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://guru-ai.onrender.com",
        "X-Title": "Guru AI Learning Path Generator",
    }
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": OPENROUTER_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(topic=topic, difficulty=difficulty),
            },
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.4,
    }

    request = Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    # --- HTTP request with full error handling ---
    try:
        with urlopen(request, timeout=90) as response:
            body = json.loads(response.read().decode("utf-8"))
    except HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8")
        except Exception:
            pass

        logger.error(f"OpenRouter HTTP {e.code} error: {error_body}")

        if e.code in (401, 403):
            raise APIKeyMissingError(
                "Invalid or unauthorized OpenRouter API key. "
                "Please check your OPENROUTER_API_KEY in the Render dashboard."
            ) from e
        if e.code == 429:
            raise LLMRateLimitError(
                "OpenRouter rate limit reached. Please wait a moment and try again."
            ) from e
        if e.code == 408 or e.code == 504:
            raise LLMTimeoutError(
                "OpenRouter request timed out. Please try again."
            ) from e
        # 5xx or other errors
        raise LLMServiceError(
            f"OpenRouter returned an error (HTTP {e.code}). Please try again."
        ) from e
    except URLError as e:
        logger.error(f"OpenRouter network error: {e.reason}")
        raise LLMServiceError(
            "Could not reach OpenRouter. Please check network connectivity."
        ) from e
    except TimeoutError as e:
        raise LLMTimeoutError(
            "OpenRouter request timed out. Please try again."
        ) from e

    # --- Parse the response body ---
    # Check for OpenRouter-level errors inside the response body
    if "error" in body:
        err_msg = body["error"].get("message", str(body["error"]))
        err_code = body["error"].get("code", 0)
        logger.error(f"OpenRouter API error in response body: {err_msg}")
        if err_code in (401, 403):
            raise APIKeyMissingError(f"OpenRouter auth error: {err_msg}")
        if err_code == 429:
            raise LLMRateLimitError(f"OpenRouter rate limit: {err_msg}")
        raise LLMServiceError(f"OpenRouter error: {err_msg}")

    content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content or not content.strip():
        raise LLMServiceError("OpenRouter returned an empty response.")

    # --- Parse JSON from LLM output ---
    # Some models wrap the JSON in markdown fences — strip them
    stripped = content.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = lines[1:] if lines[0].startswith("```") else lines
        lines = lines[:-1] if lines and lines[-1].strip() == "```" else lines
        stripped = "\n".join(lines).strip()

    try:
        raw_data = json.loads(stripped)
    except json.JSONDecodeError as e:
        logger.error(f"OpenRouter returned non-JSON content: {content[:500]}")
        raise LLMServiceError(
            "The AI returned an invalid response format. Please try again."
        ) from e

    # --- Validate against Pydantic schema ---
    try:
        return LearningPath(**raw_data)
    except ValidationError as e:
        logger.error(f"OpenRouter response failed schema validation: {e}")
        raise LLMServiceError(
            "The AI response did not match the expected structure. Please try again."
        ) from e
    except (TypeError, KeyError) as e:
        logger.error(f"OpenRouter response had unexpected structure: {e}")
        raise LLMServiceError(
            "The AI returned an unexpected response structure. Please try again."
        ) from e


def generate_learning_path_llm(
    topic: str,
    difficulty: str,
    api_key: str,
    model_name: str | None = None,
    max_retries: int = 1,
) -> LearningPath:
    """
    Generate a learning path using Google Gemini with structured output,
    or OpenRouter as the free alternative.

    Args:
        topic: The learning topic (e.g., "Machine Learning")
        difficulty: One of "beginner", "intermediate", "advanced"
        api_key: API key (Google or OpenRouter, depending on LLM_PROVIDER)
        model_name: Model to use
        max_retries: Number of retries on transient failures

    Returns:
        A validated LearningPath Pydantic model instance

    Raises:
        APIKeyMissingError: If api_key is empty or invalid
        LLMTimeoutError: If the API call times out after retries
        LLMRateLimitError: If rate limited by the API
        LLMServiceError: For any other LLM-related failure
    """
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    if model_name is None:
        model_name = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")

    if provider == "openrouter":
        return _call_openrouter(topic, difficulty, api_key, model_name)

    if not api_key:
        raise APIKeyMissingError(
            "Google API key is not configured. "
            "Set GOOGLE_API_KEY in your .env file."
        )

    # Initialize the client
    client = genai.Client(api_key=api_key)

    # Build the prompt
    user_prompt = USER_PROMPT_TEMPLATE.format(topic=topic, difficulty=difficulty)

    # Configure structured output
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        response_mime_type="application/json",
        response_schema=LearningPath,
        temperature=0.7,  # Some creativity, but not too wild
    )

    # Retry loop for transient failures
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            logger.info(
                f"Calling Gemini API (attempt {attempt + 1}/{max_retries + 1}) "
                f"for topic='{topic}', difficulty='{difficulty}'"
            )

            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=config,
            )

            # The SDK parses the JSON into our Pydantic model automatically
            if response.parsed is not None:
                logger.info("Successfully generated and parsed learning path")
                return response.parsed

            # If parsed is None, try to get text and parse manually
            if response.text:
                raw_data = json.loads(response.text)
                return LearningPath(**raw_data)

            raise LLMServiceError("Gemini returned an empty response")

        except (APIKeyMissingError, LLMRateLimitError):
            # Don't retry these — they won't resolve on their own
            raise

        except Exception as e:
            last_error = e
            error_str = str(e).lower()

            # Log the full error for debugging
            logger.error(f"Gemini API error (attempt {attempt + 1}): {type(e).__name__}: {e}")

            # Check for rate limiting (various error patterns)
            if any(term in error_str for term in ["429", "resource_exhausted", "rate", "quota"]):
                raise LLMRateLimitError(
                    "Rate limited by the Gemini API. Please wait a moment and try again."
                ) from e

            # Check for auth errors
            if any(term in error_str for term in ["401", "403", "permission", "api_key", "invalid"]):
                raise APIKeyMissingError(
                    "Invalid or unauthorized API key. Please check your GOOGLE_API_KEY."
                ) from e

            # Check for timeout
            if "timeout" in error_str or "deadline" in error_str:
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s
                    logger.warning(
                        f"Timeout on attempt {attempt + 1}, retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                    continue
                raise LLMTimeoutError(
                    "The AI took too long to respond. Please try again."
                ) from e

            # Transient errors — retry
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.warning(
                    f"Error on attempt {attempt + 1}: {e}. Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
                continue

            # All retries exhausted
            logger.error(f"All retries exhausted. Last error: {e}")
            raise LLMServiceError(
                "Failed to generate learning path. Please try again."
            ) from e

    # Should not reach here, but just in case
    raise LLMServiceError(
        "Failed to generate learning path after all retries."
    ) from last_error
