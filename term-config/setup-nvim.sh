#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_NVIM_DIR="$REPO_DIR/nvim"
TARGET_NVIM_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/nvim"

if [[ ! -d "$SOURCE_NVIM_DIR" ]]; then
  echo "Missing source config: $SOURCE_NVIM_DIR"
  exit 1
fi

mkdir -p "$(dirname "$TARGET_NVIM_DIR")"

if [[ -e "$TARGET_NVIM_DIR" && ! -L "$TARGET_NVIM_DIR" ]]; then
  BACKUP_DIR="${TARGET_NVIM_DIR}.bak.$(date +%Y%m%d_%H%M%S)"
  echo "Backing up existing config to: $BACKUP_DIR"
  mv "$TARGET_NVIM_DIR" "$BACKUP_DIR"
fi

if [[ -L "$TARGET_NVIM_DIR" ]]; then
  rm "$TARGET_NVIM_DIR"
fi

ln -s "$SOURCE_NVIM_DIR" "$TARGET_NVIM_DIR"

echo "Neovim config linked:"
echo "  $TARGET_NVIM_DIR -> $SOURCE_NVIM_DIR"

if command -v nvim >/dev/null 2>&1; then
  echo "Running headless sync step..."
  nvim --headless "+Lazy! sync" +qa || true
else
  echo "nvim not found in PATH; install Neovim first."
fi
