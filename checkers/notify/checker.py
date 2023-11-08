#!/usr/bin/env python3

import bisect
import json
import secrets
import string
import sys
import time
import zlib
from base64 import b85decode, b85encode
from datetime import datetime, timedelta, timezone

import notifylib
import maillib
import requests
from checklib import Status, cquit, get_initialized_session, rnd_string
from extended_checker import ExtendedChecker
from wonderwords import RandomSentence, RandomWord

ROUND_TIME = 60
FLAG_LIFETIME = 10
NOTIFICATION_DELAY_SLA_SECONDS = 2

WORDS = sorted(RandomWord().filter(), key=len)
SENTENCE_GENERATOR = RandomSentence()


TITLE_SEPARATORS = sum(
    [[" ", "\t"], list(string.punctuation)],
    [],
)
TITLE_SEPARATORS += sum(
    [[sp + sep, sep + sp] for sp in [" ", "\t"] for sep in TITLE_SEPARATORS], []
)

CONTENT_SEPARATORS = TITLE_SEPARATORS + sum(
    [[nl + sep, sep + nl] for nl in ["\n", "\r", "\r\n"] for sep in TITLE_SEPARATORS],
    [],
)

TITLE_RANDOM_ALPHABET = (
    string.ascii_letters + string.punctuation + string.digits + " \t"
)

CONTENT_RANDOM_ALPHABET = string.printable


# rnd_word instead of RandomWord() because it is incredibly unoptimized
def rnd_word(max_length: int) -> str:
    right = bisect.bisect_right(WORDS, max_length, key=len)
    return secrets.choice(WORDS[:right])


def rnd_sentence(max_length: int) -> str:
    while True:
        try:
            variant = secrets.randbelow(4)
            sentence = ""
            match variant:
                case 0:
                    sentence = SENTENCE_GENERATOR.bare_bone_sentence()
                case 1:
                    sentence = SENTENCE_GENERATOR.bare_bone_with_adjective()
                case 2:
                    sentence = SENTENCE_GENERATOR.simple_sentence()
                case _:
                    sentence = SENTENCE_GENERATOR.sentence()

            sentence = sentence.strip(".")  # left by the generator
            if len(sentence) < max_length:
                return sentence
        except:
            pass


def rnd_fake_flag():
    return "N" + rnd_string(30, string.ascii_uppercase + string.digits) + "="


def rnd_data(length: int, random_alphabet: str, separators: list[str]) -> str:
    # just in case, because I don't trust python libraries...
    while True:
        try:
            if length >= 30:
                variant = secrets.randbelow(3)
            else:
                variant = secrets.randbelow(2)

            match variant:
                case 0:
                    # Random garbage. Replace needed *just in case* a bad sequence is generated.
                    return rnd_string(length, random_alphabet).replace("\r\n.\r\n", ",")
                case 1:
                    # Words joined using a set of supplied separators.
                    generated = rnd_word(max_length=length)
                    max_separator_len = max(map(len, separators))
                    while len(generated) < length - (5 + max_separator_len):
                        separator = secrets.choice(separators)
                        word = rnd_word(
                            max_length=length - len(generated) - len(separator)
                        )
                        generated += separator + word
                    return generated
                case _:
                    # Sentences join using a set of supplied separators.
                    generated = rnd_sentence(max_length=length)
                    max_separator_len = max(map(len, separators))
                    while len(generated) < length - (30 + max_separator_len):
                        separator = secrets.choice(separators)
                        word = rnd_sentence(
                            max_length=length - len(generated) - len(separator)
                        )
                        generated += separator + word
                    return generated
        except:
            pass


# rnd_title generates random data without any line/vertical separators
def rnd_title(limit=50) -> str:
    length = 10 + secrets.randbelow(limit - 9)
    return rnd_data(length, TITLE_RANDOM_ALPHABET, TITLE_SEPARATORS)


def rnd_content(flag: str, limit=200) -> str:
    length = 40 + secrets.randbelow(limit - 39)
    content = rnd_data(length, CONTENT_RANDOM_ALPHABET, CONTENT_SEPARATORS)

    if flag != "":
        content = list(content)
        content += [" "] * (length - len(content))
        insert = secrets.randbelow(len(content) - len(flag) - 1)
        content = content[:insert] + list(flag) + content[insert:]
        content = "".join(content)[:length].rstrip(" ")

    return content


def rnd_username() -> str:
    length = 5 + secrets.randbelow(11)
    return rnd_string(1, string.ascii_lowercase) + rnd_string(
        length - 1, string.ascii_lowercase + string.digits
    )


def rnd_password() -> str:
    length = 8 + secrets.randbelow(23)
    return rnd_string(length, string.printable)


class Checker(ExtendedChecker):
    vulns: int = 1
    timeout: int = 30
    uses_attack_data: bool = False

    def __init__(self, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)
        self.notify_cm = notifylib.CheckMachine(self)

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except requests.exceptions.ConnectionError as e:
            self.cquit(
                Status.DOWN,
                "API connection error",
                f"Got API connection error on {e.request.url}",
            )
        except requests.exceptions.Timeout as e:
            self.cquit(
                Status.DOWN,
                "API request timeout",
                f"Got API timeout error on {e.request.url}",
            )

    def check(self):
        """
        Check algorithm:
        - Register new user A
        - Validate that user A info endpoint returns username and empty list of notifications
        - Register new user B
        - Create new notification scheduled in rnd(3, 6) seconds with repeat count in rnd(0, 4) and repeat interval in rnd(0, 4)
        - Validate that user A info endpoint returns username and notification with empty sent_at field
        - Validate that user A can get the notification by its ID
        - Wait until notification should be sent + 2 extra seconds, and perform these checks each second:
            - Validate that an unauthenticated user can get the notification by its ID
            - Validate that user B can get the notification by its ID
        - Validate that user A info endpoint returns username and notification
        - Validate that user A can get the notification by its ID
        - Login again as user A
        - Validate that user A info endpoint returns username and notification
        - Validate that user A can get the notification by its ID
        - Login to IMAP as user A and check that INBOX contains enough of the correct emails
        """

        session_a = get_initialized_session()
        session_b = get_initialized_session()
        session_c = get_initialized_session()

        # Register main and additional user for checking
        username_a, password_a = rnd_username(), rnd_password()
        self.notify_cm.register(session_a, username_a, password_a)
        self.log(f"Registered user A: {username_a}:{password_a.encode().hex()}")

        got_user_a = self.notify_cm.user_info(session_a)
        self.log(f"User A info: {got_user_a}")

        self.assert_eq(
            got_user_a,
            notifylib.UserInfo(username_a, []),
            f"{notifylib.Endpoints.USER_INFO} returned invalid info for new user",
            Status.MUMBLE,
        )

        username_b, password_b = rnd_username(), rnd_password()
        self.notify_cm.register(session_b, username_b, password_b)
        self.log(f"Registered user B: {username_b}:{password_b.encode().hex()}")

        # Random notification generation
        title = rnd_title()

        if secrets.randbits(1) == 0:
            content = rnd_content(rnd_fake_flag())
        else:
            content = rnd_content("")

        notify_in = 3 + secrets.randbelow(4)

        # right inclusive bound is the time needed to perform 2 repeats + 1
        repeat_interval = secrets.randbelow((10 - notify_in) // 2 + 2)

        # if non-zero repeat_interval was chosen, then repeat from 1 to max amount of repeats
        repeat_count = 0
        if repeat_interval != 0:
            repeat_count = 1 + secrets.randbelow((10 - notify_in) // repeat_interval)

        new_notification_repetitions = None
        if repeat_interval != 0:
            new_notification_repetitions = notifylib.NotificationCreationRepetitions(
                count=repeat_count, interval=repeat_interval
            )

        new_notification = notifylib.NotificationCreationOpts(
            title=title,
            content=content,
            notify_at=datetime.now(timezone.utc) + timedelta(seconds=notify_in),
            repetitions=new_notification_repetitions,
        )

        # Create notification for main user and validate that it is available, but wasn't sent
        self.log(f"Creating user A notification: {new_notification}")
        notification_id = self.notify_cm.create_notification(
            session_a, new_notification
        )
        self.log(f"New notification ID: {notification_id}")

        want_notification_private_info = new_notification.to_private_info(
            notification_id
        )
        want_notification_public_info = new_notification.to_public_info()

        got_user_a = self.notify_cm.user_info(session_a)
        self.log(f"User A info: {got_user_a}")
        self.assert_eq(
            got_user_a,
            notifylib.UserInfo(
                username_a,
                [want_notification_private_info],
            ),
            f"{notifylib.Endpoints.USER_INFO} returned invalid info after notification creation",
            Status.MUMBLE,
        )

        got_notification_info = self.notify_cm.get_notification(
            session_a, notification_id, Status.MUMBLE
        )
        self.log(
            f"Notification {notification_id} info by user A: {got_notification_info}"
        )
        self.assert_eq(
            got_notification_info,
            want_notification_public_info,
            f"{notifylib.Endpoints.GET_NOTIFICATION} returned invalid info after notification creation",
        )

        # Continuously monitor the notification status until all its plans should've 100% been sent
        # (+1 extra second to make sure the last plan is definitely sent as well)
        while True:
            now = datetime.now(timezone.utc)
            if now > want_notification_public_info.plan[-1].planned_at + timedelta(
                seconds=NOTIFICATION_DELAY_SLA_SECONDS + 1
            ):
                break

            # Check access by other user
            start = time.time()
            got_notification_info = self.notify_cm.get_notification(
                session_b, notification_id, Status.MUMBLE
            )
            self.log(
                f"Notification {notification_id} info by user B: {got_notification_info}"
            )
            self.check_public_notification_info(
                got_notification_info,
                want_notification_public_info,
                notifylib.Endpoints.GET_NOTIFICATION,
                Status.MUMBLE,
            )
            time.sleep(max(0, 0.5 - (time.time() - start)))

            # Check access by anonymous user
            start = time.time()
            got_notification_info = self.notify_cm.get_notification(
                session_c, notification_id, Status.MUMBLE
            )
            self.log(
                f"Notification {notification_id} info by no user: {got_notification_info}"
            )
            self.check_public_notification_info(
                got_notification_info,
                want_notification_public_info,
                notifylib.Endpoints.GET_NOTIFICATION,
                Status.MUMBLE,
            )
            time.sleep(max(0, 0.5 - (time.time() - start)))

        # Now check the notification from the original user's point of view
        for i, plan in enumerate(want_notification_public_info.plan):
            want_notification_private_info.plan[i].sent_at = plan.sent_at

        session_a = get_initialized_session()
        self.notify_cm.login(session_a, username_a, password_a, Status.MUMBLE)
        self.log("Logged in as user A")

        got_user_a = self.notify_cm.user_info(session_a)
        self.log(f"User A info: {got_user_a}")
        self.assert_eq(
            got_user_a,
            notifylib.UserInfo(
                username_a,
                [want_notification_private_info],
            ),
            f"{notifylib.Endpoints.USER_INFO} returned invalid info after notification completion",
            Status.MUMBLE,
        )

        got_notification_info = self.notify_cm.get_notification(
            session_a, notification_id, Status.MUMBLE
        )
        self.log(
            f"Notification {notification_id} info by user A: {got_notification_info}"
        )
        self.assert_eq(
            got_notification_info,
            want_notification_public_info,
            f"{notifylib.Endpoints.GET_NOTIFICATION} returned invalid info after notification completion",
        )

        with maillib.CheckMachine(self) as mail_cm:
            mail_cm.login(username_a, password_a, Status.MUMBLE)
            self.log("Logged in to IMAP as user A")

            emails = mail_cm.fetch_by_subject(
                title, len(want_notification_private_info.plan), Status.MUMBLE
            )
            self.log(f"Received emails: {emails}")

            self.assert_eq(
                len(emails),
                len(want_notification_private_info.plan),
                "IMAP fetch returned invalid number of emails after notification completion",
            )

            self.check_emails(emails, want_notification_private_info, Status.MUMBLE)

        self.cquit(Status.OK)

    def put(self, _flag_id: str, flag: str, _vuln: str):
        """
        Put algorithm:
        - Register new user
        - Create 1-5 notifications, each of which can contain the flag
        - Validate that the notifications were successfully created
        """

        session = get_initialized_session()

        username, password = rnd_username(), rnd_password()
        self.notify_cm.register(session, username, password)
        self.log(f"Registered user: {username}:{password.encode().hex()}")

        notifications = []
        flag_notification_ids = []

        for i in range(1 + secrets.randbelow(5)):
            title = rnd_title(20)

            # at least one notification must contain a flag
            if i == 0 or secrets.randbits(1) == 0:
                content = rnd_content(flag, 75)
                with_flag = True
            else:
                content = rnd_content("", 75)
                with_flag = False

            notify_in = 5 + secrets.randbelow(15)
            repeat_interval = 25 + secrets.randbelow(15)
            repeat_count = min(
                (FLAG_LIFETIME * ROUND_TIME + ROUND_TIME) // repeat_interval, 20
            )

            new_notification = notifylib.NotificationCreationOpts(
                title=title,
                content=content,
                notify_at=datetime.now(timezone.utc) + timedelta(seconds=notify_in),
                repetitions=notifylib.NotificationCreationRepetitions(
                    repeat_count, repeat_interval
                ),
            )

            self.log(
                f"Creating notification {'with flag' if with_flag else 'without flag'}: {new_notification}"
            )
            notification_id = self.notify_cm.create_notification(
                session, new_notification
            )
            self.log(f"New notification ID: {notification_id}")

            if with_flag:
                flag_notification_ids.append(notification_id)

            notifications.append((notification_id, new_notification))

        private = json.dumps(
            {
                "u": username,
                "p": password,
                "n": list(map(lambda n: [n[0], n[1].asdict()], notifications)),
            },
            separators=(",", ":"),
        )
        self.log(f"Private data: {private}")

        public = json.dumps(flag_notification_ids, separators=(",", ":"))
        self.log(f"Public data: {public}")

        self.cquit(
            Status.OK,
            public,
            b85encode(zlib.compress(private.encode())).decode(),
        )

    def get(self, flag_id: str, flag: str, _vuln: str):
        data = json.loads(zlib.decompress(b85decode(flag_id)).decode())
        username = data["u"]
        password = data["p"]
        notifications = [
            (n[0], notifylib.NotificationCreationOpts.fromdict(n[1])) for n in data["n"]
        ]

        session = get_initialized_session()

        self.notify_cm.login(session, username, password, Status.CORRUPT)
        self.log(f"Logged in as {username}")

        for notification_id, notification in notifications:
            got_notification_info = self.notify_cm.get_notification(
                session, notification_id, Status.CORRUPT
            )
            self.log(f"Notification {notification_id} info: {got_notification_info}")
            self.check_public_notification_info(
                got_notification_info,
                notification.to_public_info(),
                notifylib.Endpoints.GET_NOTIFICATION,
                Status.CORRUPT,
            )

        got_user = self.notify_cm.user_info(session)
        self.log(f"User info: {got_user}")
        self.assert_eq(
            got_user.username,
            username,
            f"{notifylib.Endpoints.USER_INFO} returned invalid username",
            Status.CORRUPT,
        )
        self.assert_eq(
            len(got_user.notifications),
            len(notifications),
            f"{notifylib.Endpoints.USER_INFO} returned invalid notifications",
            Status.CORRUPT,
        )

        got_notifications = dict(
            (notification.id, notification) for notification in got_user.notifications
        )

        for notification_id, notification in notifications:
            self.check_public_notification_info(
                got_notifications[notification_id],
                notification.to_private_info(notification_id),
                notifylib.Endpoints.USER_INFO,
                Status.CORRUPT,
            )

            self.assert_eq(
                got_notifications[notification_id].content,
                notification.content,
                f"{notifylib.Endpoints.USER_INFO} returned invalid notification content",
                Status.CORRUPT,
            )

        self.cquit(Status.OK)

    def check_public_notification_info(
        self,
        got: notifylib.PublicNotificationInfo | notifylib.PrivateNotificationInfo,
        want: notifylib.PublicNotificationInfo | notifylib.PrivateNotificationInfo,
        endpoint: str,
        status: Status,
    ):
        now = datetime.now(timezone.utc)

        self.assert_eq(
            got.title,
            want.title,
            f"{endpoint} returned invalid notification title",
            status,
        )

        self.assert_eq(
            len(got.plan),
            len(want.plan),
            f"{endpoint} returned invalid notification plan",
            status,
        )

        for i, (got_plan, want_plan) in enumerate(zip(got.plan, want.plan)):
            self.assert_eq(
                got_plan.planned_at,
                want_plan.planned_at,
                f"{endpoint} returned invalid notification plan",
                status,
            )

            if now < want_plan.planned_at:
                # check that notification isn't marked as sent when before it should be
                self.assert_(
                    got_plan.sent_at is None,
                    f"{endpoint} returned sent_at for plan which isn't supposed to be executed yet",
                    Status.MUMBLE,
                )
            elif want_plan.sent_at is not None:
                # if we've been told that the notification was sent, it's status should stay the same
                self.assert_eq(
                    got_plan.sent_at,
                    want_plan.sent_at,
                    f"{endpoint} returned sent_at which differs from the previous response",
                    status,
                )
            elif got_plan.sent_at is not None:
                # if notification is now marked as sent, the specified time should be valid
                self.assert_gte(
                    got_plan.sent_at,
                    want_plan.planned_at,
                    f"{endpoint} returned plan with sent_at earlier than planned_at",
                    Status.MUMBLE,
                )

                # remember for future iterations
                want.plan[i].sent_at = got_plan.sent_at
            else:
                self.assert_gt(
                    want_plan.planned_at
                    + timedelta(seconds=NOTIFICATION_DELAY_SLA_SECONDS),
                    now,
                    f"{endpoint} didn't return sent_at for too long after planned_at",
                    Status.MUMBLE,
                )
    
    def check_emails(self, got: list[maillib.Email], want: notifylib.PrivateNotificationInfo, status: Status):
        for email in got:
            self.assert_eq("notifier@notify", email.from_, "IMAP fetch returned invalid notification sender", Status.MUMBLE)
            self.assert_eq(want.title, email.subject, "IMAP fetch returned invalid notification subject", status)
            self.assert_eq(want.content, email.text, "IMAP fetch returned invalid notification content", status)


if __name__ == "__main__":
    c = Checker(sys.argv[2])

    try:
        c.action(sys.argv[1], *sys.argv[3:])
    except c.get_check_finished_exception():
        cquit(Status(c.status), c.public, c.private)
