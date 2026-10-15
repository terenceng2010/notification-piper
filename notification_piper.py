"""Forward Windows toast notifications to an Android phone via ntfy.

Windows side: polls UserNotificationListener for new toasts.
Phone side:   the ntfy Android app subscribed to the same topic.
"""

import argparse
import asyncio
import json
import logging
import secrets
import sys
import time
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path

from winrt.windows.ui.notifications import KnownNotificationBindings, NotificationKinds
from winrt.windows.ui.notifications.management import (
    UserNotificationListener,
    UserNotificationListenerAccessStatus,
)

APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "config.json"
LOG_PATH = APP_DIR / "notification_piper.log"

DEFAULT_CONFIG = {
    "server": "https://ntfy.sh",
    "topic": "",  # generated on first run; treat it like a password
    "token": "",  # optional ntfy access token (for self-hosted / protected topics)
    "poll_seconds": 2,
    "priority": 3,  # ntfy priority 1..5
    # Apps whose notifications are never forwarded. Phone Link is excluded
    # by default so notifications mirrored *from* the phone don't loop back.
    "exclude_apps": ["Phone Link", "Your Phone"],
    # If non-empty, only these apps are forwarded.
    "include_apps": [],
}

log = logging.getLogger("notification_piper")


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        cfg.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    if not cfg["topic"]:
        cfg["topic"] = "winpipe-" + secrets.token_urlsafe(18)
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        log.info("Created %s with new topic %s", CONFIG_PATH, cfg["topic"])
    return cfg


def extract(user_notification):
    """Return (app_name, title, body) for a UserNotification."""
    try:
        app_name = user_notification.app_info.display_info.display_name
    except Exception:
        app_name = "Unknown app"

    texts = []
    binding = user_notification.notification.visual.get_binding(
        KnownNotificationBindings.toast_generic
    )
    if binding is not None:
        texts = [t.text.strip() for t in binding.get_text_elements() if t.text and t.text.strip()]

    title = texts[0] if texts else app_name
    body = "\n".join(texts[1:])
    return app_name, title, body


def app_allowed(cfg, app_name):
    name = app_name.lower()
    if any(name == a.lower() for a in cfg["exclude_apps"]):
        return False
    if cfg["include_apps"]:
        return any(name == a.lower() for a in cfg["include_apps"])
    return True


def publish(cfg, app_name, title, body):
    # JSON publishing keeps non-ASCII titles intact (headers would not).
    payload = {
        "topic": cfg["topic"],
        "title": f"{app_name}: {title}" if title != app_name else app_name,
        "message": body or title,
        "priority": int(cfg["priority"]),
        "tags": ["computer"],
    }
    req = urllib.request.Request(
        cfg["server"].rstrip("/"),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    if cfg["token"]:
        req.add_header("Authorization", f"Bearer {cfg['token']}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        resp.read()


async def get_listener():
    listener = UserNotificationListener.current
    status = await listener.request_access_async()
    if status != UserNotificationListenerAccessStatus.ALLOWED:
        sys.exit(
            "Notification access denied. Enable it in Settings > Privacy & security > "
            "Notifications ('Let apps access your notifications'), then retry."
        )
    return listener


async def run(cfg):
    listener = await get_listener()
    seen = {n.id for n in await listener.get_notifications_async(NotificationKinds.TOAST)}
    pending = deque()  # messages that failed to send, retried each poll
    log.info("Watching notifications (%d already present, skipped). Topic: %s", len(seen), cfg["topic"])

    while True:
        current = await listener.get_notifications_async(NotificationKinds.TOAST)
        current_ids = set()
        for n in current:
            current_ids.add(n.id)
            if n.id in seen:
                continue
            seen.add(n.id)
            try:
                app_name, title, body = extract(n)
            except Exception:
                log.exception("Could not read notification %s", n.id)
                continue
            if app_allowed(cfg, app_name):
                pending.append((app_name, title, body))
            else:
                log.debug("Skipped %s (filtered)", app_name)

        # Forget dismissed notifications so the set doesn't grow forever.
        seen &= current_ids

        while pending:
            app_name, title, body = pending[0]
            try:
                publish(cfg, app_name, title, body)
                log.info("Sent: [%s] %s", app_name, title)
                pending.popleft()
            except (urllib.error.URLError, OSError) as e:
                log.warning("Send failed (%s); %d queued, will retry", e, len(pending))
                break
        while len(pending) > 200:
            pending.popleft()

        await asyncio.sleep(cfg["poll_seconds"])


async def list_apps():
    listener = await get_listener()
    names = sorted({extract(n)[0] for n in await listener.get_notifications_async(NotificationKinds.TOAST)})
    print("Apps with notifications currently in Action Center:")
    for name in names:
        print("  " + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--test", action="store_true", help="send a test notification and exit")
    parser.add_argument("--list-apps", action="store_true", help="list app names (for include/exclude filters)")
    parser.add_argument("--show-topic", action="store_true", help="print the ntfy subscription details")
    args = parser.parse_args()

    handlers = [logging.FileHandler(LOG_PATH, encoding="utf-8")]
    if sys.stdout is not None:  # pythonw has no console
        handlers.append(logging.StreamHandler())
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=handlers)

    cfg = load_config()

    if args.show_topic:
        print(f"Server: {cfg['server']}\nTopic:  {cfg['topic']}")
        print("In the ntfy Android app: + > enter the topic (and server, if not ntfy.sh).")
        return
    if args.test:
        publish(cfg, "Notification Piper", "Test", "If you see this on your phone, it works.")
        print("Test sent to topic", cfg["topic"])
        return
    if args.list_apps:
        asyncio.run(list_apps())
        return

    while True:
        try:
            asyncio.run(run(cfg))
        except KeyboardInterrupt:
            return
        except SystemExit:
            raise
        except Exception:
            log.exception("Watcher crashed; restarting in 10s")
            time.sleep(10)


if __name__ == "__main__":
    main()
