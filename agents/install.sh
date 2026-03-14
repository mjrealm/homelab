#!/usr/bin/env bash
#
# install.sh — Installs homelab agents to the local Gemini environments
#
# This script copies the open-standard agents in this repository to both the Gemini CLI
# and Antigravity skills directories, prefixing them with 'homelab-'.

set -euo pipefail

# --- Colour helpers ---
if [[ -t 1 && -z "${NO_COLOR:-}" && "${TERM:-}" != "dumb" ]]; then
  GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; RED=$'\033[0;31m'; BOLD=$'\033[1m'; RESET=$'\033[0m'
else
  GREEN=''; YELLOW=''; RED=''; BOLD=''; RESET=''
fi

info()  { printf "${GREEN}[OK]${RESET}  %s\n" "$*"; }
error() { printf "${RED}[ERR]${RESET} %s\n" "$*" >&2; }

# --- Paths ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS_DIR="$SCRIPT_DIR"

CLI_SKILLS_DIR="$HOME/.gemini/skills"
AG_SKILLS_DIR="$HOME/.gemini/antigravity/skills"

# Create directories if they don't exist
mkdir -p "$CLI_SKILLS_DIR"
mkdir -p "$AG_SKILLS_DIR"

echo -e "${BOLD}Installing agents to local Gemini environments...${RESET}"

count=0

# Iterate over all subdirectories in agents/
for dir in "$AGENTS_DIR"/*/; do
    dir="${dir%/}" # Remove trailing slash
    
    # Check if this is a valid skill directory containing SKILL.md
    if [[ ! -f "$dir/SKILL.md" ]]; then
        continue
    fi

    agent_name="$(basename "$dir")"
    target_name="homelab-${agent_name}"

    info "Installing ${agent_name} -> ${target_name}"

    # 1. Install for Gemini CLI
    cli_target="$CLI_SKILLS_DIR/$target_name"
    rm -rf "$cli_target"
    cp -R "$dir" "$cli_target"
    
    # Standard macOS sed for in-place replacement
    sed -i '' "s/^name:[[:space:]]*.*/name: ${target_name}/" "$cli_target/SKILL.md"

    # 2. Install for Antigravity
    ag_target="$AG_SKILLS_DIR/$target_name"
    rm -rf "$ag_target"
    cp -R "$dir" "$ag_target"
    
    sed -i '' "s/^name:[[:space:]]*.*/name: ${target_name}/" "$ag_target/SKILL.md"

    count=$((count + 1))
done

echo ""
info "Successfully installed $count agents."
