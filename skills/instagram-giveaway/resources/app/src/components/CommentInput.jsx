export default function CommentInput({ rawText, setRawText, uniqueUsers, pool, onParse, settings }) {
  const hasContent = rawText.trim().length > 0
  const hasParsed = uniqueUsers.length > 0

  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      onParse()
    }
  }

  return (
    <div className="card">
      <div className="card-title">💬 Instagram Comments</div>

      <textarea
        className="comment-input-area"
        value={rawText}
        onChange={e => setRawText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={`Paste your Instagram comments here — one per line.

Example:
@skatergirl99 I love this brand! 🔥
@john_doe tagging @friend
coastalvibes this is so cool omg
@rebelreaper_fan @bestfriend enter me!

Tip: On Instagram, scroll to load all comments before copying.
Ctrl+Enter to parse.`}
        spellCheck={false}
      />

      <button
        className="parse-btn"
        onClick={onParse}
        disabled={!hasContent}
      >
        {hasParsed ? '↻ Re-parse Comments' : '→ Parse Comments'}
        {hasContent && !hasParsed && ' (Ctrl+Enter)'}
      </button>

      {hasParsed && (
        <>
          <div className="stats-row">
            <div className="stat-pill">
              <span className="stat-number">{uniqueUsers.length}</span>
              <span className="stat-label">Unique Entrants</span>
            </div>
            <div className="stat-pill">
              <span className="stat-number">{pool.length}</span>
              <span className="stat-label">Total Entries</span>
            </div>
            {settings.filterKeyword && (
              <div className="stat-pill">
                <span className="stat-number" style={{ fontSize: '13px', paddingTop: '4px' }}>
                  "{settings.filterKeyword}"
                </span>
                <span className="stat-label">Filter Active</span>
              </div>
            )}
          </div>

          {uniqueUsers.length > 0 && (
            <div className="user-preview">
              <div className="user-preview-title">
                Entrants Preview ({uniqueUsers.length})
              </div>
              {uniqueUsers.slice(0, 60).map(u => (
                <span key={u} className="user-chip">@{u}</span>
              ))}
              {uniqueUsers.length > 60 && (
                <span className="user-chip" style={{ color: 'var(--text-muted)' }}>
                  +{uniqueUsers.length - 60} more
                </span>
              )}
            </div>
          )}
        </>
      )}

      {!hasParsed && (
        <div className="hint-box">
          <p>
            <strong>How to copy Instagram comments:</strong><br />
            Open your post → scroll down to load all comments → select all text in the comments section → paste here.<br /><br />
            The parser will extract one entry per unique username. Comments with extra-entry keywords earn bonus entries.
          </p>
        </div>
      )}
    </div>
  )
}
