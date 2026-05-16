export default function GiveawaySettings({ settings, onChange, onReparse }) {
  const set = (key, value) => {
    onChange(prev => ({ ...prev, [key]: value }))
  }

  const handleBlur = () => {
    onReparse()
  }

  return (
    <div className="card">
      <div className="card-title">⚙️ Giveaway Settings</div>

      <div className="form-row">
        <label>Giveaway Title</label>
        <input
          type="text"
          value={settings.title}
          onChange={e => set('title', e.target.value)}
          placeholder="e.g. Holiday Giveaway"
          maxLength={60}
        />
      </div>

      <div className="form-row">
        <label>Post Type</label>
        <select value={settings.postType} onChange={e => set('postType', e.target.value)}>
          <option value="Post">Post</option>
          <option value="Reel">Reel</option>
          <option value="Story">Story</option>
          <option value="Live">Live</option>
        </select>
      </div>

      <div className="form-row">
        <label>Required Keyword (optional)</label>
        <input
          type="text"
          value={settings.filterKeyword}
          onChange={e => set('filterKeyword', e.target.value)}
          onBlur={handleBlur}
          placeholder="e.g. @friend or #giveaway"
        />
      </div>

      <div className="form-row">
        <label>Extra Entry Keyword (optional)</label>
        <div className="form-row-inline">
          <div className="form-row" style={{ flex: 2 }}>
            <input
              type="text"
              value={settings.extraEntryKeyword}
              onChange={e => set('extraEntryKeyword', e.target.value)}
              onBlur={handleBlur}
              placeholder="e.g. @tag"
            />
          </div>
          <div className="form-row" style={{ flex: 1 }}>
            <label style={{ fontSize: '11px' }}>× Entries</label>
            <input
              type="number"
              min={2}
              max={10}
              value={settings.extraEntryCount}
              onChange={e => set('extraEntryCount', e.target.value)}
              onBlur={handleBlur}
            />
          </div>
        </div>
      </div>

      <div className="toggle-row">
        <span className="toggle-label">Exclude Previous Winners</span>
        <label className="toggle">
          <input
            type="checkbox"
            checked={settings.excludePreviousWinners}
            onChange={e => set('excludePreviousWinners', e.target.checked)}
          />
          <span className="toggle-slider" />
        </label>
      </div>
    </div>
  )
}
