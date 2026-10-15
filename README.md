# Notification Piper

Forwards Windows toast notifications to your Android phone using [ntfy](https://ntfy.sh).

## Setup

1. **Windows**
   ```powershell
   py -3.13 -m venv .venv
   .\.venv\Scripts\python -m pip install -r requirements.txt
   .\.venv\Scripts\python notification_piper.py --show-topic   # creates config.json
   ```
   If access is denied: Settings > Privacy & security > Notifications > allow apps to access notifications.

2. **Android**: install **ntfy** (Play Store / F-Droid), tap **+**, and subscribe to the topic shown above.
   In the app's settings, turn on "instant delivery" if notifications arrive late.

3. Check it: `.\.venv\Scripts\python notification_piper.py --test`

4. Run it at logon: `powershell -ExecutionPolicy Bypass -File install_startup.ps1`

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
