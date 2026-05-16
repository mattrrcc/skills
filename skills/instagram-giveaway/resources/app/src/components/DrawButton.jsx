export default function DrawButton({ onClick, disabled, isDrawing, eligibleCount, totalCount }) {
  const label = isDrawing
    ? '🎰 Drawing…'
    : eligibleCount === 0
    ? '🚫 No Eligible Entrants'
    : `🎉 Draw a Winner!`

  const sub = isDrawing
    ? 'Picking a random winner…'
    : eligibleCount > 0
    ? `${eligibleCount} eligible of ${totalCount} total entrant${totalCount !== 1 ? 's' : ''}`
    : totalCount > 0
    ? 'All entrants have already won'
    : 'Parse comments first'

  return (
    <div className="draw-btn-wrap">
      <button
        className={`draw-btn${isDrawing ? ' drawing' : ''}`}
        onClick={onClick}
        disabled={disabled}
      >
        {label}
      </button>
      <span className="draw-btn-sub">{sub}</span>
    </div>
  )
}
