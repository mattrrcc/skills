#!/bin/bash
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Install Python dependencies for mcp-builder skill
pip install -r "$CLAUDE_PROJECT_DIR/skills/mcp-builder/scripts/requirements.txt" --quiet

# Install Python dependencies for slack-gif-creator skill
pip install -r "$CLAUDE_PROJECT_DIR/skills/slack-gif-creator/requirements.txt" --quiet
