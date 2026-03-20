#!/usr/bin/env bash
set -Eeuo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_NVIM_DIR="$REPO_DIR/nvim"
CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
TARGET_NVIM_DIR="$CONFIG_HOME/nvim"

ARCH="$(uname -m)"
case "$ARCH" in
  aarch64|arm64)
    NVIM_TARBALL="nvim-linux-arm64.tar.gz"
    NVIM_DIRNAME="nvim-linux-arm64"
    ;;
  x86_64|amd64)
    NVIM_TARBALL="nvim-linux-x86_64.tar.gz"
    NVIM_DIRNAME="nvim-linux-x86_64"
    ;;
  *)
    echo "Unsupported architecture: $ARCH"
    exit 1
    ;;
esac

NVIM_URL="https://github.com/neovim/neovim/releases/latest/download/$NVIM_TARBALL"
INSTALL_DIR="/opt/nvim"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

echo "==> Installing system packages"
sudo apt update
sudo apt install -y \
  curl \
  git \
  ripgrep \
  fd-find \
  unzip \
  xclip \
  build-essential \
  python3-pip \
  python3-venv \
  nodejs \
  npm \
  luarocks

echo "==> Downloading Neovim for $ARCH"
cd "$TMP_DIR"
curl -fL "$NVIM_URL" -o "$NVIM_TARBALL"
tar xzf "$NVIM_TARBALL"

echo "==> Installing Neovim to $INSTALL_DIR"
sudo rm -rf "$INSTALL_DIR"
sudo mv "$NVIM_DIRNAME" "$INSTALL_DIR"

SHELL_RC=""
if [[ "${SHELL:-}" == */zsh ]]; then
  SHELL_RC="$HOME/.zshrc"
else
  SHELL_RC="$HOME/.bashrc"
fi

PATH_LINE='export PATH="/opt/nvim/bin:$PATH"'
if ! grep -Fqx "$PATH_LINE" "$SHELL_RC" 2>/dev/null; then
  echo "$PATH_LINE" >> "$SHELL_RC"
fi

export PATH="/opt/nvim/bin:$PATH"

echo "==> Linking Neovim config"
mkdir -p "$CONFIG_HOME"

if [[ ! -d "$SOURCE_NVIM_DIR" ]]; then
  echo "Missing repo config directory: $SOURCE_NVIM_DIR"
  exit 1
fi

if [[ -L "$TARGET_NVIM_DIR" ]]; then
  rm "$TARGET_NVIM_DIR"
elif [[ -e "$TARGET_NVIM_DIR" ]]; then
  BACKUP_DIR="${TARGET_NVIM_DIR}.bak.$(date +%Y%m%d_%H%M%S)"
  echo "Backing up existing config to $BACKUP_DIR"
  mv "$TARGET_NVIM_DIR" "$BACKUP_DIR"
fi

ln -s "$SOURCE_NVIM_DIR" "$TARGET_NVIM_DIR"

echo "==> Clearing old Neovim state"
rm -rf "$HOME/.local/share/nvim" "$HOME/.cache/nvim" "$HOME/.local/state/nvim"

echo "==> Verifying Neovim"
nvim --version | head -n 1

echo "==> Installing plugins"
nvim --headless "+Lazy! sync" +qa || true

echo
echo "Done."
echo "Neovim config: $TARGET_NVIM_DIR -> $SOURCE_NVIM_DIR"
echo "Open a new shell, or run:"
echo "  source $SHELL_RC"
