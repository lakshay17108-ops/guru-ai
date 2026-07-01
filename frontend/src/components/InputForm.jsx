/**
 * InputForm — Topic and difficulty input with generate button.
 *
 * Validates input (non-empty topic) before enabling submission.
 * Disables all inputs during loading to prevent duplicate requests.
 * Uses .btn-primary from the design system.
 */

import { useState } from 'react';
import { useLearningPath } from '../context/LearningPathContext';

function InputForm() {
  const { generatePath, isLoading, clearPath } = useLearningPath();
  const [topic, setTopic] = useState('');
  const [difficulty, setDifficulty] = useState('beginner');

  const canSubmit = topic.trim().length > 0 && !isLoading;

  function handleSubmit(e) {
    e.preventDefault();
    if (!canSubmit) return;
    clearPath();
    generatePath(topic.trim(), difficulty);
  }

  return (
    <form onSubmit={handleSubmit} className="module-card">
      <h2 className="text-base mb-4">What do you want to learn?</h2>

      <div className="space-y-4">
        {/* Topic Input */}
        <div>
          <label
            htmlFor="topic-input"
            className="block text-sm text-muted mb-1.5"
          >
            Topic
          </label>
          <input
            id="topic-input"
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g., Machine Learning, Rust, UX Design"
            disabled={isLoading}
            className="w-full px-3 py-2 text-sm bg-background border border-border rounded-md
                       text-heading placeholder:text-muted/60
                       focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent
                       disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors"
          />
        </div>

        {/* Difficulty Select */}
        <div>
          <label
            htmlFor="difficulty-select"
            className="block text-sm text-muted mb-1.5"
          >
            Difficulty
          </label>
          <select
            id="difficulty-select"
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value)}
            disabled={isLoading}
            className="w-full px-3 py-2 text-sm bg-background border border-border rounded-md
                       text-heading
                       focus:outline-none focus:ring-2 focus:ring-accent/20 focus:border-accent
                       disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors appearance-none"
          >
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={!canSubmit}
          className="btn-primary w-full disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <span className="flex items-center justify-center gap-2">
              <svg
                className="w-4 h-4 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              Generating your learning path…
            </span>
          ) : (
            'Generate Learning Path'
          )}
        </button>
      </div>
    </form>
  );
}

export default InputForm;
