#!/usr/bin/env bash
# Deploy Telegram bot to /opt/tg-bot — isolated from the production site.
# Run as root on the target server: sudo bash deploy/setup.sh
set -euo pipefail

BOT_DIR=/opt/tg-bot
LOG_DIR=/var/log/tg-bot
SERVICE_FILE=/etc/systemd/system/tg-bot.service
BOT_USER=tg-bot

echo "==> Checking prerequisites..."
command -v python3 >/dev/null 2>&1 || { echo "python3 not found. Install it first."; exit 1; }

echo "==> Creating system user '$BOT_USER' (if not exists)..."
id "$BOT_USER" &>/dev/null || useradd --system --no-create-home --shell /usr/sbin/nologin "$BOT_USER"

echo "==> Creating directories..."
mkdir -p "$BOT_DIR" "$LOG_DIR"
chown "$BOT_USER":"$BOT_USER" "$LOG_DIR"

echo "==> Copying bot source..."
cp "$(dirname "$0")/../src/tg_bot.py" "$BOT_DIR/tg_bot.py"
cp "$(dirname "$0")/../requirements-tg-bot.txt" "$BOT_DIR/requirements-tg-bot.txt"

echo "==> Creating virtual environment..."
python3 -m venv "$BOT_DIR/venv"

echo "==> Installing dependencies (isolated venv, no global packages touched)..."
"$BOT_DIR/venv/bin/pip" install --upgrade pip -q
"$BOT_DIR/venv/bin/pip" install -r "$BOT_DIR/requirements-tg-bot.txt" -q

echo "==> Setting up .env file..."
if [ ! -f "$BOT_DIR/.env" ]; then
    cp "$(dirname "$0")/../.env.example" "$BOT_DIR/.env"
    chmod 600 "$BOT_DIR/.env"
    chown "$BOT_USER":"$BOT_USER" "$BOT_DIR/.env"
    echo ""
    echo "  *** IMPORTANT: fill in your tokens in $BOT_DIR/.env ***"
    echo ""
else
    echo "  .env already exists — not overwriting."
fi

chown -R "$BOT_USER":"$BOT_USER" "$BOT_DIR"
chmod 750 "$BOT_DIR"

echo "==> Installing systemd service..."
cp "$(dirname "$0")/tg-bot.service" "$SERVICE_FILE"
systemctl daemon-reload
systemctl enable tg-bot

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit $BOT_DIR/.env — set TELEGRAM_TOKEN and ANTHROPIC_API_KEY"
echo "  2. sudo systemctl start tg-bot"
echo "  3. sudo systemctl status tg-bot"
echo ""
echo "Useful commands (do NOT affect the production site):"
echo "  sudo systemctl status tg-bot"
echo "  sudo systemctl restart tg-bot"
echo "  sudo systemctl stop tg-bot"
echo "  sudo tail -f $LOG_DIR/bot.log"
echo "  sudo journalctl -u tg-bot -f"
