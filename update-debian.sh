#!/bin/bash
set -e

echo "Updating Komiko..."
echo ""

KOMIKO_DIR="/opt/komiko"
KOMIKO_DATA="/var/lib/komiko"

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "[1/3] Updating application files..."
cp -r "$SCRIPT_DIR/app" "$KOMIKO_DIR/"
cp "$SCRIPT_DIR/config.py" "$KOMIKO_DIR/"
cp "$SCRIPT_DIR/run.py" "$KOMIKO_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$KOMIKO_DIR/"
echo "  Done."

echo "[2/3] Updating dependencies..."
"$KOMIKO_DIR/venv/bin/pip" install -r "$KOMIKO_DIR/requirements.txt" -q
echo "  Done."

echo "[3/3] Restarting service..."
systemctl restart komiko
echo "  Done."

echo ""
echo "Komiko updated and restarted."
echo "Check status: systemctl status komiko"