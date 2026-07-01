/**
 * PhaseCard — Renders a single learning phase with its milestones.
 *
 * Each phase gets a numbered badge, title, and a list of
 * expandable MilestoneCards. Uses .module-card from the design system.
 */

import MilestoneCard from './MilestoneCard';

function PhaseCard({ phase }) {
  return (
    <div className="module-card">
      {/* Phase header */}
      <div className="flex items-center gap-3 mb-1">
        {/* Phase number badge */}
        <div className="w-8 h-8 bg-accent text-white rounded-lg flex items-center justify-center flex-shrink-0 text-sm font-semibold">
          {phase.phase}
        </div>

        <div className="flex-1 min-w-0">
          <h3 className="text-base truncate">{phase.phase_title}</h3>
          <p className="text-xs text-muted">
            {phase.milestones.length} milestone{phase.milestones.length !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      {/* Milestones list */}
      <div className="ml-11">
        {phase.milestones.map((milestone, i) => (
          <MilestoneCard key={milestone.milestone_id} milestone={milestone} index={i} />
        ))}
      </div>
    </div>
  );
}

export default PhaseCard;
