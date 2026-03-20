#!/usr/bin/env bash
set -e

CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/alacritty"
THEME_DIR="$CONFIG_DIR/themes/themes"
THEME_NAME="cyber_punk_neon.toml"

THEME_URL="https://raw.githubusercontent.com/alacritty/alacritty-theme/master/themes/cyber_punk_neon.toml"

echo "Setting up Alacritty cyberpunk theme..."

# create directories
mkdir -p "$THEME_DIR"

# download theme
curl -L "$THEME_URL" -o "$THEME_DIR/$THEME_NAME"

echo "Theme installed:"
echo "$THEME_DIR/$THEME_NAME"

CONFIG_FILE="$CONFIG_DIR/alacritty.toml"

# create config if missing
if [ ! -f "$CONFIG_FILE" ]; then
cat <<EOF > "$CONFIG_FILE"
[window]
decorations = "transparent"
dynamic_padding = true

[window.padding]
x = 20
y = 35

[selection]
save_to_clipboard = true

[general]
import = [
    "~/.config/alacritty/themes/themes/cyber_punk_neon.toml"
]
EOF

echo "Created new config:"
echo "$CONFIG_FILE"

else
echo "Config already exists:"
echo "$CONFIG_FILE"
fi

echo "Done."
echo "Restart Alacritty to apply the theme."
