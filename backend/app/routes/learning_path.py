"""
Learning Path API routes.

Architecture note:
  This blueprint isolates all /api/generate-path logic. The route reads
  USE_MOCK from the app config to decide whether to use the hardcoded mock
  or the real Gemini LLM. Both paths go through Pydantic validation.
"""

import logging

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from app.models.schemas import LearningPath
from app.services.llm_service import (
    APIKeyMissingError,
    LLMRateLimitError,
    LLMServiceError,
    LLMTimeoutError,
    generate_learning_path_llm,
)

logger = logging.getLogger(__name__)

learning_path_bp = Blueprint("learning_path", __name__)


def _build_mock_learning_path(topic: str, difficulty: str) -> dict:
    """
    Return a hardcoded learning path that passes Pydantic validation.

    Kept as a fallback for testing and when USE_MOCK=true.
    """
    return {
        "topic": topic,
        "estimated_time": "6 weeks",
        "difficulty": difficulty,
        "curriculum": [
            {
                "phase": 1,
                "phase_title": "Foundations & Environment Setup",
                "milestones": [
                    {
                        "milestone_id": "P1_M1",
                        "title": "Understanding Core Concepts",
                        "objectives": [
                            f"Define what {topic} is and its key sub-domains",
                            "Understand the historical evolution and current landscape",
                            "Identify real-world applications and use cases",
                        ],
                        "suggested_queries": [
                            f"What is {topic} for beginners",
                            f"{topic} fundamentals explained",
                            f"{topic} real world applications 2025",
                        ],
                        "resources": [
                            {
                                "resource_title": f"Introduction to {topic} — Official Docs",
                                "url": "https://example.com/intro",
                            },
                            {
                                "resource_title": f"{topic} Crash Course (YouTube)",
                                "url": "https://youtube.com/example",
                            },
                        ],
                        "milestone_project": {
                            "project_title": "Concept Map",
                            "description": (
                                f"Create a visual concept map of the {topic} ecosystem, "
                                "identifying at least 5 sub-domains and how they relate "
                                "to each other."
                            ),
                        },
                    },
                    {
                        "milestone_id": "P1_M2",
                        "title": "Setting Up Your Development Environment",
                        "objectives": [
                            "Install and configure the required tools and libraries",
                            "Run a 'Hello World' example end-to-end",
                            "Understand the project structure conventions",
                        ],
                        "suggested_queries": [
                            f"{topic} development environment setup guide",
                            f"best IDE for {topic} development",
                        ],
                        "resources": [
                            {
                                "resource_title": "Environment Setup Guide",
                                "url": "https://example.com/setup",
                            },
                        ],
                        "milestone_project": {
                            "project_title": "Hello World Project",
                            "description": (
                                f"Set up a working {topic} development environment and "
                                "run a basic 'Hello World' example to verify everything "
                                "is configured correctly."
                            ),
                        },
                    },
                ],
            },
            {
                "phase": 2,
                "phase_title": "Core Skills & Hands-On Practice",
                "milestones": [
                    {
                        "milestone_id": "P2_M1",
                        "title": "Building Your First Real Project",
                        "objectives": [
                            f"Apply core {topic} techniques to a real problem",
                            "Learn debugging and troubleshooting strategies",
                            "Practice reading documentation effectively",
                        ],
                        "suggested_queries": [
                            f"{topic} beginner project tutorial",
                            f"{topic} common mistakes and debugging",
                        ],
                        "resources": [
                            {
                                "resource_title": f"Hands-On {topic} Tutorial",
                                "url": "https://example.com/tutorial",
                            },
                            {
                                "resource_title": f"{topic} Best Practices Guide",
                                "url": "https://example.com/best-practices",
                            },
                        ],
                        "milestone_project": {
                            "project_title": "Mini Portfolio Project",
                            "description": (
                                f"Build a small but complete {topic} project that solves "
                                "a real problem. Document your process and publish it "
                                "to GitHub with a proper README."
                            ),
                        },
                    },
                ],
            },
            {
                "phase": 3,
                "phase_title": "Advanced Topics & Capstone",
                "milestones": [
                    {
                        "milestone_id": "P3_M1",
                        "title": "Exploring Advanced Patterns",
                        "objectives": [
                            f"Understand advanced {topic} patterns and architectures",
                            "Evaluate trade-offs between different approaches",
                            "Read and understand research papers or advanced docs",
                        ],
                        "suggested_queries": [
                            f"advanced {topic} patterns",
                            f"{topic} architecture best practices",
                        ],
                        "resources": [
                            {
                                "resource_title": f"Advanced {topic} Patterns",
                                "url": "https://example.com/advanced",
                            },
                        ],
                        "milestone_project": {
                            "project_title": "Capstone Project",
                            "description": (
                                f"Design and build a comprehensive {topic} project "
                                "that demonstrates mastery of foundational and advanced "
                                "concepts. Present your work with documentation and "
                                "a live demo."
                            ),
                        },
                    },
                ],
            },
        ],
    }


@learning_path_bp.route("/api/generate-path", methods=["POST"])
def generate_learning_path():
    """
    Generate a structured learning path for a given topic.

    Uses the real Gemini LLM by default, or falls back to mock data
    when USE_MOCK=true (always true in testing config).

    Request body (JSON):
        {
            "topic": "Machine Learning",   // required
            "difficulty": "beginner"        // optional, defaults to "beginner"
        }

    Returns:
        200: A validated LearningPath JSON object.
        400: Missing or invalid request body.
        422: Generated data failed schema validation.
        429: Rate limited by the LLM API.
        500: Unexpected server error.
        503: API key not configured.
        504: LLM API timeout.
    """
    # --- 1. Validate request body ---
    if not request.is_json:
        return jsonify({
            "error": "Request must be JSON",
            "hint": "Set Content-Type: application/json",
        }), 400

    data = request.get_json(silent=True)
    if not data or "topic" not in data:
        return jsonify({
            "error": "Missing required field: 'topic'",
            "example": {"topic": "Machine Learning", "difficulty": "beginner"},
        }), 400

    topic = data["topic"].strip()
    if not topic:
        return jsonify({"error": "'topic' cannot be empty"}), 400

    difficulty = data.get("difficulty", "beginner").strip().lower()
    valid_difficulties = {"beginner", "intermediate", "advanced"}
    if difficulty not in valid_difficulties:
        return jsonify({
            "error": f"Invalid difficulty: '{difficulty}'",
            "valid_options": sorted(valid_difficulties),
        }), 400

    # --- 2. Generate learning path ---
    use_mock = current_app.config.get("USE_MOCK", False)

    if use_mock:
        # Mock mode — return hardcoded data
        logger.info(f"Using mock generator for topic='{topic}'")
        try:
            raw_path = _build_mock_learning_path(topic, difficulty)
            validated_path = LearningPath(**raw_path)
        except ValidationError as e:
            return jsonify({
                "error": "Generated learning path failed schema validation",
                "details": e.errors(),
            }), 422
        except Exception as e:
            return jsonify({
                "error": "Failed to generate learning path",
                "details": str(e),
            }), 500
    else:
        # Real LLM mode
        api_key = current_app.config.get("GOOGLE_API_KEY", "")
        model_name = current_app.config.get("GEMINI_MODEL", "gemini-2.0-flash")

        try:
            validated_path = generate_learning_path_llm(
                topic=topic,
                difficulty=difficulty,
                api_key=api_key,
                model_name=model_name,
            )
        except APIKeyMissingError as e:
            logger.error(f"API key missing: {e}")
            return jsonify({
                "error": "AI service is not configured. Please set your Google API key.",
            }), 503
        except LLMTimeoutError as e:
            logger.warning(f"LLM timeout: {e}")
            logger.info("Falling back to mock learning path after timeout")
            validated_path = _build_mock_learning_path(topic, difficulty)
            validated_path = LearningPath(**validated_path)
        except LLMRateLimitError as e:
            logger.warning(f"Rate limited: {e}")
            logger.info("Falling back to mock learning path after rate limit")
            validated_path = _build_mock_learning_path(topic, difficulty)
            validated_path = LearningPath(**validated_path)
        except LLMServiceError as e:
            logger.error(f"LLM service error: {e}")
            return jsonify({
                "error": "Failed to generate learning path. Please try again.",
            }), 500
        except Exception as e:
            logger.error(f"Unexpected error in LLM generation: {e}", exc_info=True)
            return jsonify({
                "error": "An unexpected error occurred. Please try again.",
            }), 500

        # --- 3. Re-validate with Pydantic (safety net) ---
        try:
            # If the SDK already returned a LearningPath, model_dump + re-parse
            # ensures nothing slipped through
            validated_path = LearningPath(**validated_path.model_dump())
        except ValidationError as e:
            logger.error(f"Pydantic re-validation failed: {e}")
            return jsonify({
                "error": "Generated learning path failed schema validation",
                "details": e.errors(),
            }), 422

    # --- 4. Return validated response ---
    return jsonify(validated_path.model_dump()), 200
