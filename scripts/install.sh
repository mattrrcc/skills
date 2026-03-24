#!/usr/bin/env bash
# install.sh — Ruflo installer (from Git source)
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/anthropics/skills/main/scripts/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/anthropics/skills/main/scripts/install.sh | bash -s -- --full
#
# Options:
#   --full            Complete setup: install + build + MCP integration + diagnostics
#   --minimal         Skip optional dependencies
#   --setup-mcp       Configure MCP server for Claude Code after install
#   --doctor          Run diagnostics only
#   --dir PATH        Install directory (default: ./ruflo)
#   --version TAG     Git tag/branch to checkout (default: main)
#   --help            Show this help message

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
RUFLO_REPO="https://github.com/ruvnet/ruflo.git"
RUFLO_DEFAULT_DIR="ruflo"
RUFLO_DEFAULT_VERSION="main"
NODE_MIN_VERSION=20

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
info()    { printf '\033[0;34m[INFO]\033[0m  %s\n' "$*"; }
success() { printf '\033[0;32m[OK]\033[0m    %s\n' "$*"; }
warn()    { printf '\033[0;33m[WARN]\033[0m  %s\n' "$*" >&2; }
error()   { printf '\033[0;31m[ERROR]\033[0m %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<EOF
Ruflo Installer (from Git source)

USAGE:
  bash install.sh [OPTIONS]

OPTIONS:
  --full            Complete setup: install + build + MCP + diagnostics
  --minimal         Skip optional dependencies
  --setup-mcp       Configure MCP server integration with Claude Code
  --doctor          Run prerequisite diagnostics only
  --dir PATH        Directory to clone into (default: ./${RUFLO_DEFAULT_DIR})
  --version TAG     Git branch or tag to checkout (default: ${RUFLO_DEFAULT_VERSION})
  --help            Show this help message

EXAMPLES:
  # Basic install
  bash install.sh

  # Full setup with MCP integration
  bash install.sh --full

  # Install into custom directory
  bash install.sh --dir ~/tools/ruflo

  # Install a specific version
  bash install.sh --version v3.5.0
EOF
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
FULL=false
MINIMAL=false
SETUP_MCP=false
DOCTOR=false
INSTALL_DIR=""
VERSION="${RUFLO_DEFAULT_VERSION}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --full)      FULL=true; shift ;;
    --minimal)   MINIMAL=true; shift ;;
    --setup-mcp) SETUP_MCP=true; shift ;;
    --doctor)    DOCTOR=true; shift ;;
    --dir)       INSTALL_DIR="${2:-}"; shift 2 ;;
    --version)   VERSION="${2:-}"; shift 2 ;;
    --help|-h)   usage; exit 0 ;;
    *) warn "Unknown option: $1"; shift ;;
  esac
done

[[ -z "$INSTALL_DIR" ]] && INSTALL_DIR="$(pwd)/${RUFLO_DEFAULT_DIR}"

# --full implies --setup-mcp
[[ "$FULL" == "true" ]] && SETUP_MCP=true

# ---------------------------------------------------------------------------
# Prerequisite checks
# ---------------------------------------------------------------------------
check_command() {
  local cmd="$1" hint="${2:-}"
  if ! command -v "$cmd" &>/dev/null; then
    [[ -n "$hint" ]] && error "'${cmd}' not found. ${hint}"
    error "'${cmd}' is required but not installed."
  fi
  success "'${cmd}' found: $(command -v "$cmd")"
}

check_node_version() {
  check_command node "Install Node.js ${NODE_MIN_VERSION}+ from https://nodejs.org"
  local version
  version=$(node -e "process.stdout.write(process.versions.node)" 2>/dev/null)
  local major="${version%%.*}"
  if [[ "$major" -lt "$NODE_MIN_VERSION" ]]; then
    error "Node.js ${NODE_MIN_VERSION}+ required (found ${version}). Update at https://nodejs.org"
  fi
  success "Node.js ${version} satisfies requirement (>=${NODE_MIN_VERSION})"
}

detect_package_manager() {
  if command -v bun &>/dev/null;  then echo "bun"
  elif command -v pnpm &>/dev/null; then echo "pnpm"
  else echo "npm"
  fi
}

run_diagnostics() {
  info "Running diagnostics..."
  check_command git  "Install git from https://git-scm.com"
  check_node_version
  local pm
  pm=$(detect_package_manager)
  success "Package manager: ${pm} ($(command -v "$pm"))"
  if command -v claude &>/dev/null; then
    success "Claude Code CLI found: $(claude --version 2>/dev/null || echo 'version unknown')"
  else
    warn "Claude Code CLI not found — MCP integration will be skipped."
    warn "Install it with: npm install -g @anthropic-ai/claude-code"
  fi
}

# ---------------------------------------------------------------------------
# Install steps
# ---------------------------------------------------------------------------
clone_repo() {
  if [[ -d "$INSTALL_DIR/.git" ]]; then
    info "Existing repo found at '${INSTALL_DIR}', pulling latest changes..."
    git -C "$INSTALL_DIR" fetch origin
    git -C "$INSTALL_DIR" checkout "$VERSION"
    git -C "$INSTALL_DIR" pull origin "$VERSION" || true
  else
    info "Cloning ruflo @ ${VERSION} into '${INSTALL_DIR}'..."
    git clone --branch "$VERSION" --depth 1 "$RUFLO_REPO" "$INSTALL_DIR"
  fi
  success "Source ready at ${INSTALL_DIR}"
}

install_dependencies() {
  local pm
  pm=$(detect_package_manager)
  info "Installing dependencies with ${pm}..."
  if [[ "$MINIMAL" == "true" ]]; then
    case "$pm" in
      bun)  bun install --production --cwd "$INSTALL_DIR" ;;
      pnpm) pnpm install --prod --dir "$INSTALL_DIR" ;;
      *)    npm install --omit=optional --prefix "$INSTALL_DIR" ;;
    esac
  else
    case "$pm" in
      bun)  bun install --cwd "$INSTALL_DIR" ;;
      pnpm) pnpm install --dir "$INSTALL_DIR" ;;
      *)    npm install --prefix "$INSTALL_DIR" ;;
    esac
  fi
  success "Dependencies installed"
}

build_project() {
  local pm
  pm=$(detect_package_manager)
  info "Building TypeScript source..."
  case "$pm" in
    bun)  bun run build --cwd "$INSTALL_DIR" ;;
    pnpm) pnpm --dir "$INSTALL_DIR" run build ;;
    *)    npm run build --prefix "$INSTALL_DIR" ;;
  esac
  success "Build complete"
}

setup_mcp() {
  if ! command -v claude &>/dev/null; then
    warn "Claude Code CLI not found — skipping MCP setup."
    warn "To set up MCP later, run: claude mcp add ruflo -- node ${INSTALL_DIR}/bin/cli.js mcp start"
    return
  fi
  info "Configuring MCP server with Claude Code..."
  claude mcp add ruflo -- node "${INSTALL_DIR}/bin/cli.js" mcp start
  success "MCP server 'ruflo' registered with Claude Code"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
  echo ""
  echo "  Ruflo Installer"
  echo "  ==============="
  echo "  Source: ${RUFLO_REPO}"
  echo "  Target: ${INSTALL_DIR}"
  echo "  Version: ${VERSION}"
  echo ""

  if [[ "$DOCTOR" == "true" ]]; then
    run_diagnostics
    exit 0
  fi

  run_diagnostics
  echo ""

  clone_repo
  install_dependencies
  build_project

  if [[ "$SETUP_MCP" == "true" ]]; then
    setup_mcp
  fi

  echo ""
  success "Ruflo installed successfully!"
  echo ""
  echo "  Binary:  ${INSTALL_DIR}/bin/cli.js"
  echo "  Run:     node ${INSTALL_DIR}/bin/cli.js --help"
  echo ""
  if [[ "$SETUP_MCP" != "true" ]]; then
    echo "  To add MCP integration with Claude Code:"
    echo "    bash install.sh --setup-mcp --dir ${INSTALL_DIR}"
    echo ""
  fi
}

main "$@"
