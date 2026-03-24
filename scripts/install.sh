#!/usr/bin/env bash
# install.sh — Anthropic Agent Skills installer
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/anthropics/skills/main/scripts/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/anthropics/skills/main/scripts/install.sh | bash -s -- --full
#
# Options:
#   --full        Install all skill sets (document-skills, example-skills, claude-api)
#   --plugin NAME Install a specific plugin by name
#   --help        Show this help message

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REPO="anthropics/skills"
MARKETPLACE_CMD="/plugin marketplace add ${REPO}"
DOCUMENT_SKILLS_CMD="/plugin install document-skills@anthropic-agent-skills"
EXAMPLE_SKILLS_CMD="/plugin install example-skills@anthropic-agent-skills"
CLAUDE_API_SKILL_CMD="/plugin install claude-api@anthropic-agent-skills"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
info()    { printf '\033[0;34m[INFO]\033[0m  %s\n' "$*"; }
success() { printf '\033[0;32m[OK]\033[0m    %s\n' "$*"; }
warn()    { printf '\033[0;33m[WARN]\033[0m  %s\n' "$*" >&2; }
error()   { printf '\033[0;31m[ERROR]\033[0m %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<EOF
Anthropic Agent Skills Installer

USAGE:
  bash install.sh [OPTIONS]

OPTIONS:
  --full           Install all available skill sets
  --plugin NAME    Install a specific plugin (document-skills, example-skills, claude-api)
  --help           Show this help message

EXAMPLES:
  # Register the marketplace only
  bash install.sh

  # Register the marketplace and install all skills
  bash install.sh --full

  # Install a specific plugin
  bash install.sh --plugin document-skills
EOF
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
FULL=false
PLUGIN=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --full)   FULL=true; shift ;;
    --plugin) PLUGIN="${2:-}"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) warn "Unknown option: $1"; shift ;;
  esac
done

# ---------------------------------------------------------------------------
# Prerequisite checks
# ---------------------------------------------------------------------------
check_claude_code() {
  if ! command -v claude &>/dev/null; then
    error "Claude Code CLI not found. Install it from https://docs.claude.com/en/claude-code/overview and re-run this script."
  fi
  success "Claude Code CLI found: $(claude --version 2>/dev/null || echo 'version unknown')"
}

# ---------------------------------------------------------------------------
# Install steps
# ---------------------------------------------------------------------------
register_marketplace() {
  info "Registering Anthropic Agent Skills marketplace..."
  info "Run the following command inside Claude Code:"
  echo ""
  echo "  ${MARKETPLACE_CMD}"
  echo ""
}

install_plugin() {
  local name="$1"
  case "$name" in
    document-skills)
      info "To install document skills (PDF, Word, Excel, PowerPoint), run in Claude Code:"
      echo "  ${DOCUMENT_SKILLS_CMD}"
      ;;
    example-skills)
      info "To install example skills, run in Claude Code:"
      echo "  ${EXAMPLE_SKILLS_CMD}"
      ;;
    claude-api)
      info "To install the Claude API skill, run in Claude Code:"
      echo "  ${CLAUDE_API_SKILL_CMD}"
      ;;
    *)
      error "Unknown plugin '${name}'. Available: document-skills, example-skills, claude-api"
      ;;
  esac
}

install_all() {
  info "Full install — all skill sets:"
  echo ""
  echo "  ${MARKETPLACE_CMD}"
  echo "  ${DOCUMENT_SKILLS_CMD}"
  echo "  ${EXAMPLE_SKILLS_CMD}"
  echo "  ${CLAUDE_API_SKILL_CMD}"
  echo ""
  info "Run the commands above inside Claude Code to complete the installation."
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  echo ""
  echo "  Anthropic Agent Skills Installer"
  echo "  ================================="
  echo ""

  check_claude_code

  if [[ -n "$PLUGIN" ]]; then
    register_marketplace
    install_plugin "$PLUGIN"
  elif [[ "$FULL" == "true" ]]; then
    install_all
  else
    register_marketplace
    cat <<EOF
To install a skill set, run one of the following inside Claude Code:

  ${DOCUMENT_SKILLS_CMD}
  ${EXAMPLE_SKILLS_CMD}
  ${CLAUDE_API_SKILL_CMD}

Or re-run this script with --full to see all commands at once:

  bash install.sh --full

EOF
  fi

  success "Done. See https://github.com/${REPO} for more information."
  echo ""
}

main "$@"
