/**
 * LoadingState — Skeleton loader for the curriculum display.
 *
 * Renders 3 pulsing skeleton cards that mimic the PhaseCard layout.
 * Designed to be reassuring during 10-15 second LLM generation times.
 * Uses Tailwind's animate-pulse — no external dependencies.
 */

function SkeletonPhase({ phaseNum }) {
  return (
    <div className="module-card animate-pulse">
      {/* Phase header skeleton */}
      <div className="flex items-center gap-3 mb-4">
        <div className="w-8 h-8 bg-gray-200 rounded-lg" />
        <div className="flex-1">
          <div className="h-4 bg-gray-200 rounded w-48 mb-1.5" />
          <div className="h-3 bg-gray-100 rounded w-24" />
        </div>
      </div>

      {/* Milestone skeletons */}
      <div className="space-y-3 ml-11">
        {[1, 2].map((i) => (
          <div
            key={i}
            className="flex items-center gap-3 py-3 border-t border-border"
          >
            <div className="w-5 h-5 bg-gray-200 rounded" />
            <div className="flex-1">
              <div className="h-3.5 bg-gray-200 rounded w-56 mb-1" />
              <div className="h-3 bg-gray-100 rounded w-32" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function LoadingState() {
  return (
    <div className="space-y-4">
      {/* Status message */}
      <div className="text-center py-2">
        <div className="inline-flex items-center gap-2 text-sm text-muted">
          <svg
            className="w-4 h-4 animate-spin text-accent"
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
          Building your personalized curriculum…
        </div>
      </div>

      {/* Skeleton cards */}
      {[1, 2, 3].map((i) => (
        <SkeletonPhase key={i} phaseNum={i} />
      ))}
    </div>
  );
}

export default LoadingState;
