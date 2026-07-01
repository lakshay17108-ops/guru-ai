"""
LLM Service — Google Gemini structured output integration.

Uses the google-genai SDK's native structured output feature:
  - Passes our Pydantic LearningPath model as response_schema
  - Gemini is constrained to output valid JSON matching the schema
  - SDK returns response.parsed — already a Pydantic model instance

This eliminates manual JSON parsing and the entire class of
"LLM returned malformed JSON" errors.
"""

import logging
import time

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


def generate_learning_path_llm(
    topic: str,
    difficulty: str,
    api_key: str,
    model_name: str = "gemini-2.0-flash",
    max_retries: int = 1,
) -> LearningPath:
    """
    Generate a learning path using Google Gemini with structured output.

    Args:
        topic: The learning topic (e.g., "Machine Learning")
        difficulty: One of "beginner", "intermediate", "advanced"
        api_key: Google API key
        model_name: Gemini model to use
        max_retries: Number of retries on transient failures

    Returns:
        A validated LearningPath Pydantic model instance

    Raises:
        APIKeyMissingError: If api_key is empty
        LLMTimeoutError: If the API call times out after retries
        LLMRateLimitError: If rate limited by the API
        LLMServiceError: For any other LLM-related failure
    """
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
                import json
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
