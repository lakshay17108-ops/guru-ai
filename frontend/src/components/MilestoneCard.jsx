/**
 * MilestoneCard — Expandable milestone within a phase.
 *
 * Defaults to collapsed. Click to toggle expanded state.
 * Expanded view shows: objectives, resources, suggested queries, project.
 * Uses design system tokens — no inline styles.
 */

import { useState } from 'react';

function MilestoneCard({ milestone, index }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="border-t border-border">
      {/* Collapsed header — always visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-3 py-3 px-1 text-left
                   hover:bg-background/80 transition-colors rounded-md group"
        aria-expanded={isExpanded}
      >
        {/* Expand/collapse chevron */}
        <svg
          className={`w-4 h-4 text-muted flex-shrink-0 transition-transform duration-200 ${
            isExpanded ? 'rotate-90' : ''
          }`}
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2}
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M8.25 4.5l7.5 7.5-7.5 7.5"
          />
        </svg>

        {/* Title and meta */}
        <div className="flex-1 min-w-0">
          <span className="text-sm font-medium text-heading block truncate">
            {milestone.title}
          </span>
          <span className="text-xs text-muted">
            {milestone.objectives.length} objective{milestone.objectives.length !== 1 ? 's' : ''}
            {' · '}
            {milestone.resources.length} resource{milestone.resources.length !== 1 ? 's' : ''}
          </span>
        </div>

        {/* Milestone ID badge */}
        <span className="text-xs text-muted bg-background px-2 py-0.5 rounded border border-border flex-shrink-0">
          {milestone.milestone_id}
        </span>
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <div className="pl-8 pr-1 pb-4 space-y-4 animate-fadeIn">
          {/* Objectives */}
          <div>
            <h4 className="text-xs font-medium text-muted uppercase tracking-wider mb-2">
              Learning Objectives
            </h4>
            <ul className="space-y-1.5">
              {milestone.objectives.map((obj, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-body">
                  <span className="w-4 h-4 mt-0.5 flex-shrink-0 rounded border border-border bg-background" />
                  {obj}
                </li>
              ))}
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="text-xs font-medium text-muted uppercase tracking-wider mb-2">
              Resources
            </h4>
            <div className="space-y-1.5">
              {milestone.resources.map((res, i) => (
                <a
                  key={i}
                  href={res.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-sm text-accent hover:text-accent-hover
                             transition-colors group/link"
                >
                  <svg
                    className="w-3.5 h-3.5 text-muted group-hover/link:text-accent flex-shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    strokeWidth={2}
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m9.86-2.194a4.5 4.5 0 0 0-1.242-7.244l-4.5-4.5a4.5 4.5 0 0 0-6.364 6.364L4.343 8.07"
                    />
                  </svg>
                  <span className="underline underline-offset-2">
                    {res.resource_title}
                  </span>
                </a>
              ))}
            </div>
          </div>

          {/* Suggested Queries */}
          <div>
            <h4 className="text-xs font-medium text-muted uppercase tracking-wider mb-2">
              Suggested Search Queries
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {milestone.suggested_queries.map((query, i) => (
                <span
                  key={i}
                  className="text-xs text-muted bg-background px-2.5 py-1 rounded-full border border-border"
                >
                  {query}
                </span>
              ))}
            </div>
          </div>

          {/* Milestone Project */}
          <div className="bg-background rounded-md p-4 border border-border">
            <h4 className="text-xs font-medium text-muted uppercase tracking-wider mb-2">
              🎯 Milestone Project
            </h4>
            <p className="text-sm font-medium text-heading mb-1">
              {milestone.milestone_project.project_title}
            </p>
            <p className="text-sm text-muted leading-relaxed">
              {milestone.milestone_project.description}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default MilestoneCard;
