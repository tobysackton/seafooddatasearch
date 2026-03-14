#!/bin/bash
# install-qcal.sh
# Installs qcal to ~/.local/bin/ so it's available from any directory.
# Run from any location: bash ~/seafooddatasearch/tools/install-qcal.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/bin"
SOURCE="$SCRIPT_DIR/qcal"

echo "Installing qcal..."

# Create install directory if needed
mkdir -p "$INSTALL_DIR"

# Copy and make executable
cp "$SOURCE" "$INSTALL_DIR/qcal"
chmod +x "$INSTALL_DIR/qcal"

echo "Installed to $INSTALL_DIR/qcal"

# Check if ~/.local/bin is on PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo "Adding ~/.local/bin to PATH in ~/.zprofile..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zprofile"
    echo "Run 'source ~/.zprofile' or open a new terminal to use qcal."
else
    echo "~/.local/bin is already on PATH."
fi

echo ""
echo "Done. Test with: qcal --today"
