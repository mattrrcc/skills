---
name: instagram-giveaway
description: Scaffolds and launches a browser-based Instagram giveaway winner-picker app. Parses pasted Instagram comments to extract entrants, applies filters and extra-entry rules, then randomly draws one winner at a time with an animated slot-machine reveal. Use when running a giveaway on an Instagram Post or Reel and needing to fairly select a winner from comments.
---

# Instagram Giveaway Picker

A zero-backend, single-page React app that picks a random winner from Instagram post or reel comments.

## What This Skill Does

1. Provides a full React + Vite application in `resources/app/`
2. Parses pasted Instagram comment text → extracts unique usernames
3. Applies optional keyword filters and extra-entry rules
4. Draws one winner at a time with an animated slot-machine reveal
5. Tracks winner history for the session
6. Deployable to Vercel or GitHub Pages with zero config

## Quick Start

```bash
# 1. Copy app to your project folder
cp -r resources/app ./instagram-giveaway-app
cd instagram-giveaway-app

# 2. Install dependencies
npm install

# 3. Run locally
npm run dev
# → Open http://localhost:5173

# 4. Deploy to Vercel (optional)
npm run build
npx vercel deploy --prod
```

## How to Use the App

1. **Configure** your giveaway in the left panel:
   - Set the Giveaway Title
   - Choose Post or Reel
   - Optionally set a required keyword (e.g., `@friend` to require tagging)
   - Set extra-entry keyword and multiplier
   - Toggle "Exclude Previous Winners"

2. **Paste Comments** into the right panel:
   - Go to your Instagram post/reel
   - Select all visible comments (scroll to load more first)
   - Copy and paste them into the text area
   - Click **Parse Comments**

3. **Draw a Winner**:
   - Click the **Draw Winner** button
   - Watch the slot-machine animation
   - Winner is revealed with a celebration screen
   - Check Winner History at the bottom

## Parsing Tips

The parser handles these Instagram comment formats:
```
@username great product! @friend check this out
username just comment text
@username123 🔥🔥
```

It extracts the first `@username` or first word per line as the entrant.
Multiple lines from the same username are deduplicated (one entry per person by default).

## Customization Options

| Setting | Description |
|---|---|
| Giveaway Title | Displayed in the header |
| Post Type | "Post" or "Reel" label |
| Required Keyword | Only count comments containing this word/tag |
| Extra Entry Keyword | Comments with this word get bonus entries |
| Extra Entry Multiplier | How many entries the extra keyword earns |
| Exclude Previous Winners | Auto-remove past winners from the pool |

## Deployment

**Vercel (recommended — 1 command):**
```bash
npm run build && npx vercel deploy --prod
```

**GitHub Pages:**
```bash
# In vite.config.js, set base: '/your-repo-name/'
npm run build
# Then push the dist/ folder to gh-pages branch
npx gh-pages -d dist
```

## File Structure

```
resources/app/
├── package.json          # React 18 + Vite
├── vite.config.js        # Build config
├── index.html            # HTML entry
├── vercel.json           # Zero-config Vercel deploy
└── src/
    ├── main.jsx
    ├── App.jsx            # Main state + layout
    ├── index.css          # Global styles (Instagram dark theme)
    └── components/
        ├── GiveawaySettings.jsx   # Left panel config
        ├── CommentInput.jsx       # Paste + parse comments
        ├── DrawButton.jsx         # Trigger the draw
        ├── WinnerReveal.jsx       # Slot-machine animation + winner card
        └── WinnerHistory.jsx      # Session winner log
```
