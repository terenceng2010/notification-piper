# Notification Piper

Forwards Windows toast notifications to your Android phone using [ntfy](https://ntfy.sh).

## Setup

1. **Windows** (requires [uv](https://docs.astral.sh/uv/))
   ```powershell
   uv sync
   uv run notification_piper.py --show-topic   # creates config.json
   ```
   If access is denied: Settings > Privacy & security > Notifications > allow apps to access notifications.

2. **Android**: install **ntfy** (Play Store / F-Droid), tap **+**, and subscribe to the topic shown above.
   In the app's settings, turn on "instant delivery" if notifications arrive late.

3. Check it: `uv run notification_piper.py --test`

4. Run it at logon: `powershell -ExecutionPolicy Bypass -File install_startup.ps1`
   (uses the `.venv` created by `uv sync`)

## Tray icon

While running, a tray icon shows the status: green = forwarding, grey = paused, orange = offline
(messages queued for retry), red = error (see the log). Hover for the count sent this session.
Right-click for **Pause** (also on double-click), **Send test**, **Open config**, **Open log** and **Quit**.
Notifications that arrive while paused are dropped, not sent on resume.

Use `--no-tray` to run headless. Only one instance runs at a time.

## config.json

| key | meaning |
|---|---|
| `server` | ntfy server (`https://ntfy.sh` or a self-hosted URL) |
| `topic` | random topic name; anyone who knows it can read your notifications |
| `token` | optional ntfy access token for protected topics |
| `poll_seconds` | how often to check for new notifications |
| `priority` | ntfy priority, 1–5 |
| `exclude_apps` | app names never forwarded (Phone Link by default, to prevent loops) |
| `include_apps` | if set, only these apps are forwarded |

Use `--list-apps` to see exact app names. Logs go to `notification_piper.log`.

## Privacy

On public ntfy.sh, messages pass through a third-party server and are kept there for about 12 hours. For sensitive content (OTP codes, chats),
self-host ntfy or restrict forwarding with `include_apps`.
