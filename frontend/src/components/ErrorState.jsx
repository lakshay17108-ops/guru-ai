/**
 * ErrorState — Error display with retry capability.
 *
 * Shows the error message from the API/context and a "Try Again" button
 * that clears the error so the user can re-submit.
 * Uses .module-card and .btn-secondary from the design system.
 */

import { useLearningPath } from '../context/LearningPathContext';

function ErrorState() {
  const { error, clearError } = useLearningPath();

  if (!error) return null;

  return (
    <div className="module-card border-red-200">
      <div className="flex items-start gap-3">
        {/* Error icon */}
        <div className="w-8 h-8 bg-red-50 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
          <svg
            className="w-4 h-4 text-red-500"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={2}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"
            />
          </svg>
        </div>

        {/* Error content */}
        <div className="flex-1 min-w-0">
          <h3 className="text-sm mb-1">Something went wrong</h3>
          <p className="text-sm text-muted mb-4">{error}</p>
          <button onClick={clearError} className="btn-secondary text-xs">
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
}

export default ErrorState;
