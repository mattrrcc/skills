import { useEffect, useRef, useState } from 'react'

function buildSpinNames(sampleNames, winner, count = 40) {
  const pool = sampleNames.length > 0 ? sampleNames : ['winner']
  const items = []
  for (let i = 0; i < count; i++) {
    items.push(pool[Math.floor(Math.random() * pool.length)])
  }
  items.push(winner)
  return items
}

export default function WinnerReveal({
  winner,
  isDrawing,
  sampleNames,
  onDismiss,
  drawNumber,
  giveawayTitle,
  postType,
}) {
  const trackRef = useRef(null)
  const [spinNames] = useState(() => buildSpinNames(sampleNames, winner || 'winner'))
  const ITEM_HEIGHT = 36

  useEffect(() => {
    if (!trackRef.current) return
    const totalItems = spinNames.length
    const finalOffset = -((totalItems - 1) * ITEM_HEIGHT) + (72 / 2 - ITEM_HEIGHT / 2)
    trackRef.current.style.setProperty('--final-offset', `${finalOffset}px`)
    trackRef.current.style.setProperty('--spin-duration', '3.2s')
  }, [spinNames])

  const handleCopy = () => {
    const text = `🎉 Giveaway Winner!\n\n@${winner} has been selected as the winner of our ${giveawayTitle} ${postType} Giveaway!\n\n📸 @rebelreaperclothing\n#giveaway #winner #rebelreaper`
    navigator.clipboard.writeText(text).catch(() => {})
  }

  return (
    <div className="reveal-overlay" onClick={e => { if (e.target === e.currentTarget && !isDrawing) onDismiss() }}>
      <div className="reveal-card">
        {isDrawing ? (
          <>
            <div className="drawing-label">🎰 Drawing Winner…</div>
            <div className="slot-machine">
              <div className="slot-track" ref={trackRef}>
                {spinNames.map((name, i) => (
                  <div
                    key={i}
                    className={`slot-item${i === spinNames.length - 1 ? ' winner-item' : ''}`}
                  >
                    @{name}
                  </div>
                ))}
              </div>
            </div>
            <div className="drawing-sub">Picking from the comment pool…</div>
          </>
        ) : winner ? (
          <>
            <div className="confetti-row">🎊 🏆 🎊</div>
            <div className="reveal-title">Winner #{drawNumber}!</div>
            <div className="winner-at">@</div>
            <div className="winner-name">{winner}</div>
            <div className="reveal-meta">
              {giveawayTitle} · {postType} Giveaway · @rebelreaperclothing
            </div>
            <div className="reveal-actions">
              <button className="btn btn-primary" onClick={handleCopy}>
                📋 Copy Announcement
              </button>
              <button className="btn btn-secondary" onClick={onDismiss}>
                ✓ Done
              </button>
            </div>
          </>
        ) : null}
      </div>
    </div>
  )
}
