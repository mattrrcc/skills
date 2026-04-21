function formatTime(date) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function WinnerHistory({ winners }) {
  return (
    <section className="history-section">
      <div className="card">
        <div className="card-title">🏆 Winner History ({winners.length})</div>
        <div className="history-grid">
          {winners.map((w, i) => (
            <div key={i} className="history-chip">
              <span className="history-num">#{w.drawNumber}</span>
              <span className="history-user">@{w.username}</span>
              <span className="history-time">{formatTime(w.timestamp)}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
