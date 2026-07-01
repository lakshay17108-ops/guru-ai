/**
 * CurriculumDisplay — Renders the full learning path curriculum.
 *
 * Shows a path overview (topic, estimated time, difficulty badge)
 * followed by all phase cards. Only renders when learningPath is available.
 * Uses design system tokens throughout.
 */

import { useLearningPath } from '../context/LearningPathContext';
import PhaseCard from './PhaseCard';

function DifficultyBadge({ difficulty }) {
  return (
    <span className="text-xs font-medium text-muted bg-background px-2.5 py-1 rounded-full border border-border capitalize">
      {difficulty}
    </span>
  );
}

function CurriculumDisplay() {
  const { learningPath } = useLearningPath();

  if (!learningPath) return null;

  const { topic, estimated_time, difficulty, curriculum } = learningPath;

  return (
    <div className="space-y-4 animate-fadeIn">
      {/* Path Overview */}
      <div className="module-card">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <p className="text-xs text-muted uppercase tracking-wider mb-1">
              Your Learning Path
            </p>
            <h2 className="text-xl">{topic}</h2>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <span className="text-xs text-muted bg-background px-2.5 py-1 rounded-full border border-border">
              ⏱ {estimated_time}
            </span>
            <DifficultyBadge difficulty={difficulty} />
          </div>
        </div>

        {/* Stats bar */}
        <div className="flex items-center gap-4 mt-4 pt-4 border-t border-border">
          <div className="text-center">
            <p className="text-lg font-semibold text-heading">{curriculum.length}</p>
            <p className="text-xs text-muted">Phase{curriculum.length !== 1 ? 's' : ''}</p>
          </div>
          <div className="w-px h-8 bg-border" />
          <div className="text-center">
            <p className="text-lg font-semibold text-heading">
              {curriculum.reduce((sum, phase) => sum + phase.milestones.length, 0)}
            </p>
            <p className="text-xs text-muted">Milestones</p>
          </div>
          <div className="w-px h-8 bg-border" />
          <div className="text-center">
            <p className="text-lg font-semibold text-heading">
              {curriculum.reduce(
                (sum, phase) =>
                  sum + phase.milestones.reduce((ms, m) => ms + m.objectives.length, 0),
                0
              )}
            </p>
            <p className="text-xs text-muted">Objectives</p>
          </div>
        </div>
      </div>

      {/* Phase Cards */}
      {curriculum.map((phase) => (
        <PhaseCard key={phase.phase} phase={phase} />
      ))}
    </div>
  );
}

export default CurriculumDisplay;
