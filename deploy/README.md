# Telegram Bot — Deployment Guide

## Requirements
- Linux server with systemd
- Python 3.10+
- Root/sudo access

## First-time install

```bash
sudo bash deploy/setup.sh
```

The script:
- Creates a dedicated system user `tg-bot` (no login shell)
- Installs the bot to `/opt/tg-bot/` with an isolated Python venv
- **Does not touch** the production site directories or nginx config
- Installs and enables the systemd service `tg-bot`

After the script, edit the .env file:

```bash
sudo nano /opt/tg-bot/.env
# Set: TELEGRAM_TOKEN and ANTHROPIC_API_KEY
```

Then start:

```bash
sudo systemctl start tg-bot
```

## Day-to-day commands

| Action | Command |
|---|---|
| Check status | `sudo systemctl status tg-bot` |
| View live logs | `sudo tail -f /var/log/tg-bot/bot.log` |
| View logs via journald | `sudo journalctl -u tg-bot -f` |
| Restart bot only | `sudo systemctl restart tg-bot` |
| Stop bot only | `sudo systemctl stop tg-bot` |
| Disable autostart | `sudo systemctl disable tg-bot` |

> None of these commands affect the production site (`donify.stream`).

## Update bot code

```bash
git pull
sudo cp src/tg_bot.py /opt/tg-bot/tg_bot.py
sudo systemctl restart tg-bot
```

## Isolation guarantees

- **No open ports** — bot uses long polling, not webhook
- **Separate directory** — `/opt/tg-bot/`, site files untouched
- **Separate venv** — packages not installed globally
- **Separate systemd unit** — `tg-bot.service` is independent
- **Separate log file** — `/var/log/tg-bot/bot.log`
- **Separate OS user** — `tg-bot` system user, no shell access
