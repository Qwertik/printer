#!/bin/bash
set -euo pipefail

INSTALL_DIR="/opt/print-api"
SERVICE_USER="printapi"

echo "=== Thermal Print API Installer ==="

# Create service user
if ! id "$SERVICE_USER" &>/dev/null; then
    echo "Creating user: $SERVICE_USER"
    sudo useradd -r -s /usr/sbin/nologin -G lp "$SERVICE_USER"
else
    echo "User $SERVICE_USER already exists"
fi

# Deploy application
echo "Deploying to $INSTALL_DIR"
sudo mkdir -p "$INSTALL_DIR"
sudo cp -r server.py config.py api/ print_queue/ driver/ templates/ fonts/ requirements.txt "$INSTALL_DIR/"
sudo chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# Create .env from example if it doesn't exist
if [ ! -f "$INSTALL_DIR/.env" ]; then
    sudo cp .env.example "$INSTALL_DIR/.env"
    sudo chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/.env"
    echo "Created $INSTALL_DIR/.env — edit it with your settings"
fi

# Create virtualenv and install dependencies
echo "Setting up Python virtualenv"
sudo -u "$SERVICE_USER" python3 -m venv "$INSTALL_DIR/venv"
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

# Install systemd service
echo "Installing systemd service"
sudo cp deploy/print-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable print-api

# Install udev rules
echo "Installing udev rules"
sudo cp deploy/99-thermal-printer.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules

echo ""
echo "=== Installation complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit $INSTALL_DIR/.env with your settings (API tokens, Tailscale IP, etc.)"
echo "  2. Edit /etc/udev/rules.d/99-thermal-printer.rules with your printer's USB VID/PID"
echo "     Run 'lsusb' with the printer plugged in to find the IDs"
echo "  3. Start the service: sudo systemctl start print-api"
echo "  4. Check status: sudo systemctl status print-api"
echo "  5. View logs: sudo journalctl -u print-api -f"
