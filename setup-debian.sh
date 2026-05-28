#!/bin/bash
set -e

echo "====================================="
echo "  Komiko - Self-hosted Comics Server"
echo "====================================="
echo ""

DEPENDENCIES="python3 python3-venv python3-pip libxml2-dev libxslt1-dev"
KOMIKO_DIR="/opt/komiko"
KOMIKO_DATA="/var/lib/komiko"
KOMIKO_USER="komiko"

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)./setup-debian.sh"
    exit 1
fi

echo "[1/6] Installing system dependencies..."
apt-get update
apt-get install -y $DEPENDENCIES
echo "  Done."

echo "[2/6] Creating Komiko user..."
if ! id "$KOMIKO_USER" &>/dev/null; then
    adduser --system --group --home "$KOMIKO_DIR" --shell /usr/sbin/nologin "$KOMIKO_USER"
fi
echo "  Done."

echo "[3/6] Setting up application..."
mkdir -p "$KOMIKO_DIR"
mkdir -p "$KOMIKO_DATA"
mkdir -p "$KOMIKO_DATA/covers"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ "$SCRIPT_DIR" != "$KOMIKO_DIR" ]; then
    cp -r "$SCRIPT_DIR/app" "$KOMIKO_DIR/"
    cp -r "$SCRIPT_DIR/config.py" "$KOMIKO_DIR/"
    cp -r "$SCRIPT_DIR/run.py" "$KOMIKO_DIR/"
    cp "$SCRIPT_DIR/requirements.txt" "$KOMIKO_DIR/"
fi

python3 -m venv "$KOMIKO_DIR/venv"
"$KOMIKO_DIR/venv/bin/pip" install --upgrade pip
"$KOMIKO_DIR/venv/bin/pip" install -r "$KOMIKO_DIR/requirements.txt"
"$KOMIKO_DIR/venv/bin/pip" install gunicorn
echo "  Done."

echo "[4/6] Generating secret key..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
echo "  Generated."

echo "[5/6] Installing systemd service..."
cat > /etc/systemd/system/komiko.service << EOF
[Unit]
Description=Komiko Comics Server
After=network.target

[Service]
Type=notify
User=$KOMIKO_USER
Group=$KOMIKO_USER
WorkingDirectory=$KOMIKO_DIR
Environment=FLASK_ENV=production
Environment=SECRET_KEY=$SECRET_KEY
Environment=KOMIKO_DATA_DIR=$KOMIKO_DATA
Environment=PATH=$KOMIKO_DIR/venv/bin:/usr/bin:/bin
ExecStart=$KOMIKO_DIR/venv/bin/gunicorn \\
    --bind 0.0.0.0:5000 \\
    --workers 2 \\
    --threads 4 \\
    --timeout 120 \\
    run:app

Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

chown -R "$KOMIKO_USER:$KOMIKO_USER" "$KOMIKO_DIR"
chown -R "$KOMIKO_USER:$KOMIKO_USER" "$KOMIKO_DATA"
echo "  Done."

echo "[6/6] Starting Komiko..."
systemctl daemon-reload
systemctl enable komiko
systemctl start komiko
echo "  Done."

echo ""
echo "====================================="
echo "  Komiko is running!"
echo "====================================="
echo ""
echo "  URL:        http://$(hostname -I | awk '{print $1}'):5000"
echo "  Data:       $KOMIKO_DATA"
echo "  Config:     /etc/systemd/system/komiko.service"
echo "  Logs:       journalctl -u komiko -f"
echo "  Restart:    systemctl restart komiko"
echo "  Stop:       systemctl stop komiko"
echo ""
echo "  Open the URL above to complete the initial setup."
echo ""