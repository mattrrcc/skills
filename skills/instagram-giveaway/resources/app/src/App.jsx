import { useState, useCallback } from 'react'
import GiveawaySettings from './components/GiveawaySettings'
import CommentInput from './components/CommentInput'
import DrawButton from './components/DrawButton'
import WinnerReveal from './components/WinnerReveal'
import WinnerHistory from './components/WinnerHistory'

const DEFAULT_SETTINGS = {
  title: 'Instagram Giveaway',
  postType: 'Post',
  filterKeyword: '',
  extraEntryKeyword: '',
  extraEntryCount: 2,
  excludePreviousWinners: true,
}

function parseComments(rawText, settings) {
  const lines = rawText.split('\n').filter(l => l.trim())
  const entryMap = new Map()

  for (const line of lines) {
    const trimmed = line.trim()
    const match = trimmed.match(/^@?([A-Za-z0-9._]{2,30})/)
    if (!match) continue
    const username = match[1].toLowerCase()

    if (settings.filterKeyword) {
      const kw = settings.filterKeyword.toLowerCase()
      if (!trimmed.toLowerCase().includes(kw)) continue
    }

    let entries = 1
    if (settings.extraEntryKeyword) {
      const re = new RegExp(settings.extraEntryKeyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi')
      if ((trimmed.match(re) || []).length > 0) {
        entries = Math.max(1, Number(settings.extraEntryCount) || 2)
      }
    }

    const existing = entryMap.get(username) || 0
    entryMap.set(username, Math.max(existing, entries))
  }

  const uniqueUsers = Array.from(entryMap.keys())
  const pool = []
  for (const [u, count] of entryMap.entries()) {
    for (let i = 0; i < count; i++) pool.push(u)
  }

  return { uniqueUsers, pool }
}

export default function App() {
  const [settings, setSettings] = useState(DEFAULT_SETTINGS)
  const [rawText, setRawText] = useState('')
  const [uniqueUsers, setUniqueUsers] = useState([])
  const [pool, setPool] = useState([])
  const [winners, setWinners] = useState([])
  const [currentWinner, setCurrentWinner] = useState(null)
  const [isDrawing, setIsDrawing] = useState(false)
  const [revealKey, setRevealKey] = useState(0)

  const handleParse = useCallback(() => {
    const result = parseComments(rawText, settings)
    setUniqueUsers(result.uniqueUsers)
    setPool(result.pool)
    setCurrentWinner(null)
  }, [rawText, settings])

  const handleDraw = useCallback(() => {
    const excludeSet = settings.excludePreviousWinners
      ? new Set(winners.map(w => w.username))
      : new Set()
    const eligible = pool.filter(p => !excludeSet.has(p))
    if (eligible.length === 0) return

    const winner = eligible[Math.floor(Math.random() * eligible.length)]
    setIsDrawing(true)
    setCurrentWinner(null)
    setRevealKey(k => k + 1)

    setTimeout(() => {
      setIsDrawing(false)
      setCurrentWinner(winner)
      setWinners(prev => [
        { username: winner, timestamp: new Date(), drawNumber: prev.length + 1 },
        ...prev,
      ])
    }, 3200)
  }, [pool, winners, settings.excludePreviousWinners])

  const handleDismiss = useCallback(() => {
    setCurrentWinner(null)
    setIsDrawing(false)
  }, [])

  const eligibleCount = settings.excludePreviousWinners
    ? new Set(pool.filter(p => !new Set(winners.map(w => w.username)).has(p))).size
    : new Set(pool).size

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-inner">
          <div className="header-logo">🎉</div>
          <div className="header-text">
            <h1 className="header-title">{settings.title || 'Instagram Giveaway'}</h1>
            <p className="header-sub">
              {settings.postType} Giveaway · @rebelreaperclothing
            </p>
          </div>
          <div className="header-logo">🏆</div>
        </div>
      </header>

      <div className="app-body">
        <aside className="sidebar">
          <GiveawaySettings settings={settings} onChange={setSettings} onReparse={() => {
            if (rawText) {
              const result = parseComments(rawText, settings)
              setUniqueUsers(result.uniqueUsers)
              setPool(result.pool)
            }
          }} />
          <DrawButton
            onClick={handleDraw}
            disabled={pool.length === 0 || isDrawing}
            isDrawing={isDrawing}
            eligibleCount={eligibleCount}
            totalCount={uniqueUsers.length}
          />
        </aside>

        <main className="main-content">
          <CommentInput
            rawText={rawText}
            setRawText={setRawText}
            uniqueUsers={uniqueUsers}
            pool={pool}
            onParse={handleParse}
            settings={settings}
          />
        </main>
      </div>

      {(isDrawing || currentWinner) && (
        <WinnerReveal
          key={revealKey}
          winner={currentWinner}
          isDrawing={isDrawing}
          sampleNames={uniqueUsers.slice(0, 30)}
          onDismiss={handleDismiss}
          drawNumber={winners.length}
          giveawayTitle={settings.title}
          postType={settings.postType}
        />
      )}

      {winners.length > 0 && (
        <WinnerHistory winners={winners} />
      )}
    </div>
  )
}
