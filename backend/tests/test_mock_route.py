"""
Smoke tests for the mock /api/generate-path endpoint.

These tests verify:
  1. The mock endpoint returns 200 with valid JSON.
  2. The response body conforms to the LearningPath Pydantic schema.
  3. Error cases return appropriate status codes and messages.
"""

import json
import pytest

from app import create_app
from app.models.schemas import LearningPath
from app.services.llm_service import LLMRateLimitError, generate_learning_path_llm


@pytest.fixture
def client():
    """Create a test client using the testing config."""
    app = create_app("testing")
    with app.test_client() as client:
        yield client


class TestGeneratePath:
    """Tests for POST /api/generate-path."""

    def test_successful_generation(self, client):
        """A valid request should return 200 and a schema-compliant body."""
        response = client.post(
            "/api/generate-path",
            json={"topic": "Machine Learning", "difficulty": "beginner"},
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify the response deserializes into a valid LearningPath
        validated = LearningPath(**data)
        assert validated.topic == "Machine Learning"
        assert validated.difficulty == "beginner"
        assert len(validated.curriculum) >= 1

    def test_response_has_all_required_fields(self, client):
        """Every field in the schema must be present in the response."""
        response = client.post(
            "/api/generate-path",
            json={"topic": "Python", "difficulty": "intermediate"},
        )

        data = response.get_json()
        # Top-level fields
        assert "topic" in data
        assert "estimated_time" in data
        assert "difficulty" in data
        assert "curriculum" in data

        # Drill into the first milestone
        first_phase = data["curriculum"][0]
        assert "phase" in first_phase
        assert "phase_title" in first_phase
        assert "milestones" in first_phase

        first_milestone = first_phase["milestones"][0]
        assert "milestone_id" in first_milestone
        assert "title" in first_milestone
        assert "objectives" in first_milestone
        assert "suggested_queries" in first_milestone
        assert "resources" in first_milestone
        assert "milestone_project" in first_milestone

    def test_default_difficulty(self, client):
        """Omitting difficulty should default to 'beginner'."""
        response = client.post(
            "/api/generate-path",
            json={"topic": "Data Science"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["difficulty"] == "beginner"

    def test_missing_topic_returns_400(self, client):
        """A request without 'topic' should return 400."""
        response = client.post(
            "/api/generate-path",
            json={"difficulty": "advanced"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_empty_topic_returns_400(self, client):
        """An empty string topic should return 400."""
        response = client.post(
            "/api/generate-path",
            json={"topic": "   ", "difficulty": "beginner"},
        )

        assert response.status_code == 400

    def test_invalid_difficulty_returns_400(self, client):
        """An unrecognized difficulty level should return 400."""
        response = client.post(
            "/api/generate-path",
            json={"topic": "Rust", "difficulty": "godmode"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "valid_options" in data

    def test_no_json_body_returns_400(self, client):
        """A request with no JSON body should return 400."""
        response = client.post(
            "/api/generate-path",
            data="not json",
            content_type="text/plain",
        )

        assert response.status_code == 400

    def test_falls_back_to_mock_when_llm_is_rate_limited(self, client, monkeypatch):
        """A transient LLM failure should still return a valid learning path."""

        def raise_rate_limit(*args, **kwargs):
            raise LLMRateLimitError("rate limited")

        monkeypatch.setattr(
            "app.routes.learning_path.generate_learning_path_llm",
            raise_rate_limit,
        )

        response = client.post(
            "/api/generate-path",
            json={"topic": "React", "difficulty": "beginner"},
        )

        assert response.status_code == 200
        data = response.get_json()
        validated = LearningPath(**data)
        assert validated.topic == "React"
        assert validated.difficulty == "beginner"

    def test_openrouter_provider_returns_structured_learning_path(self, monkeypatch):
        """The backend should support OpenRouter as an alternative free LLM provider."""

        class FakeResponse:
            def __init__(self, payload):
                self._payload = payload

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return json.dumps(self._payload).encode("utf-8")

        def fake_urlopen(request, timeout=60):
            payload = {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps({
                                "topic": "Python",
                                "estimated_time": "4 weeks",
                                "difficulty": "beginner",
                                "curriculum": [
                                    {
                                        "phase": 1,
                                        "phase_title": "Basics",
                                        "milestones": [
                                            {
                                                "milestone_id": "P1_M1",
                                                "title": "Intro",
                                                "objectives": ["Learn Python basics"],
                                                "suggested_queries": ["Python basics"],
                                                "resources": [{"resource_title": "Python docs", "url": "https://www.python.org/"}],
                                                "milestone_project": {"project_title": "Hello World", "description": "Write a small script"},
                                            }
                                        ],
                                    }
                                ],
                            })
                        }
                    }
                ]
            }
            return FakeResponse(payload)

        monkeypatch.setenv("LLM_PROVIDER", "openrouter")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        monkeypatch.setattr("app.services.llm_service.urlopen", fake_urlopen)

        result = generate_learning_path_llm(
            topic="Python",
            difficulty="beginner",
            api_key="test-key",
            model_name="meta-llama/llama-3.1-8b-instruct:free",
        )

        assert result.topic == "Python"
        assert result.difficulty == "beginner"

    def test_route_uses_openrouter_credentials_when_enabled(self, monkeypatch):
        """The route should forward OpenRouter credentials when that provider is selected."""
        captured = {}

        def fake_generate_learning_path_llm(*, topic, difficulty, api_key, model_name, **kwargs):
            captured["api_key"] = api_key
            captured["model_name"] = model_name
            return LearningPath(**{
                "topic": topic,
                "estimated_time": "4 weeks",
                "difficulty": difficulty,
                "curriculum": [
                    {
                        "phase": 1,
                        "phase_title": "Basics",
                        "milestones": [
                            {
                                "milestone_id": "P1_M1",
                                "title": "Intro",
                                "objectives": ["Learn basics"],
                                "suggested_queries": ["intro"],
                                "resources": [{"resource_title": "Docs", "url": "https://example.com"}],
                                "milestone_project": {"project_title": "Hello", "description": "Say hi"},
                            }
                        ],
                    }
                ],
            })

        monkeypatch.setenv("LLM_PROVIDER", "openrouter")
        monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")
        monkeypatch.setenv("OPENROUTER_MODEL", "openrouter-model")
        monkeypatch.setattr(
            "app.routes.learning_path.generate_learning_path_llm",
            fake_generate_learning_path_llm,
        )

        app = create_app("development")
        with app.test_client() as client:
            response = client.post(
                "/api/generate-path",
                json={"topic": "Python", "difficulty": "beginner"},
            )

        assert response.status_code == 200
        assert captured.get("api_key") == "openrouter-key"
        assert captured.get("model_name") == "openrouter-model"

    def test_empty_json_body_returns_400(self, client):
        """An empty JSON object should return 400."""
        response = client.post(
            "/api/generate-path",
            json={},
        )

        assert response.status_code == 400


class TestHealthCheck:
    """Tests for GET /api/health."""

    def test_health_check(self, client):
        """The health endpoint should return 200 with status healthy."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
