/**
 * API Service Layer
 *
 * Centralizes all backend communication. Components never call fetch directly.
 * When we swap mock → real LLM, only this file changes.
 *
 * Base URL is configurable via VITE_API_URL env var (defaults to localhost:5000).
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

/**
 * Generate a structured learning path for the given topic.
 *
 * @param {string} topic - The learning topic (e.g., "Machine Learning")
 * @param {string} difficulty - One of "beginner", "intermediate", "advanced"
 * @returns {Promise<Object>} The validated LearningPath object
 * @throws {Error} On network failure, non-200 response, or JSON parse error
 */
export async function generateLearningPath(topic, difficulty = 'beginner') {
  let response;

  try {
    response = await fetch(`${API_BASE_URL}/api/generate-path`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, difficulty }),
    });
  } catch (networkError) {
    throw new Error(
      'Unable to connect to the server. Please check that the backend is running and try again.'
    );
  }

  // Parse the response body (may fail if server returns non-JSON)
  let data;
  try {
    data = await response.json();
  } catch (parseError) {
    throw new Error(
      'Received an invalid response from the server. Please try again later.'
    );
  }

  // Handle non-200 responses with server-provided error messages
  if (!response.ok) {
    const serverMessage = data?.error || `Server returned status ${response.status}`;
    throw new Error(serverMessage);
  }

  return data;
}
