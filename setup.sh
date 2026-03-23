#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="room-sensor"

echo "=== Pi Zero Room Sensor Setup ==="
echo ""

# Check we're on a Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "WARNING: This doesn't look like a Raspberry Pi. Continuing anyway..."
fi

# Check config exists
if [ ! -f "$SCRIPT_DIR/config.json" ]; then
    echo "No config.json found. Creating from template..."
    cp "$SCRIPT_DIR/config.example.json" "$SCRIPT_DIR/config.json"
    echo ""
    echo "!! Edit config.json with your MQTT credentials before starting the service:"
    echo "   nano $SCRIPT_DIR/config.json"
    echo ""
    NEEDS_CONFIG=1
fi

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3-venv libgpiod2 > /dev/null

# Create venv and install Python packages
echo "Setting up Python environment..."
python3 -m venv "$SCRIPT_DIR/venv"
"$SCRIPT_DIR/venv/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"

# Install systemd service
echo "Installing systemd service..."
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=Pi Zero Room Sensor (DHT11 → MQTT → Home Assistant)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/venv/bin/python sensor.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}

if [ "${NEEDS_CONFIG:-0}" = "1" ]; then
    echo ""
    echo "=== Setup complete! ==="
    echo ""
    echo "Next steps:"
    echo "  1. Edit config.json with your MQTT credentials"
    echo "  2. Run: sudo systemctl start ${SERVICE_NAME}"
else
    sudo systemctl restart ${SERVICE_NAME}
    echo ""
    echo "=== Setup complete! Service is running. ==="
    echo ""
    echo "Check status: sudo systemctl status ${SERVICE_NAME}"
    echo "View logs:    sudo journalctl -u ${SERVICE_NAME} -f"
fi
