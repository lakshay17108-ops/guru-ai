/**
 * Header — App branding and navigation bar.
 *
 * Minimal, professional header with app name and subtitle.
 * Uses design system tokens only — no inline styles or flashy elements.
 */
function Header() {
  return (
    <header className="border-b border-border bg-surface">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4 flex items-center gap-3">
        {/* Icon */}
        <div className="w-8 h-8 bg-accent rounded-lg flex items-center justify-center flex-shrink-0">
          <svg
            className="w-4 h-4 text-white"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={2}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M4.26 10.147a60.438 60.438 0 0 0-.491 6.347A48.62 48.62 0 0 1 12 20.904a48.62 48.62 0 0 1 8.232-4.41 60.46 60.46 0 0 0-.491-6.347m-15.482 0a50.636 50.636 0 0 0-2.658-.813A59.906 59.906 0 0 1 12 3.493a59.903 59.903 0 0 1 10.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.717 50.717 0 0 1 12 13.489a50.702 50.702 0 0 1 7.74-3.342"
            />
          </svg>
        </div>

        {/* Text */}
        <div>
          <h1 className="text-lg leading-tight">Guru AI</h1>
          <p className="text-xs text-muted leading-tight">
            Personal Learning Path Generator
          </p>
        </div>
      </div>
    </header>
  );
}

export default Header;
