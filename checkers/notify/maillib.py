from collections.abc import Callable
from imaplib import IMAP4
from typing import ParamSpec, TypeVar
from dataclasses import dataclass
from email.errors import MessageError

from checklib import Status
from extended_checker import ExtendedChecker
from imap_tools.errors import ImapToolsError, UnexpectedCommandStatusError
from imap_tools.mailbox import MailBoxUnencrypted
from imap_tools.query import AND

IMAP_PORT = 143


@dataclass
class Email:
    from_: str
    subject: str
    text: str


T = TypeVar("T")
P = ParamSpec("P")


# CheckMachine for the IMAP interface of the Stalwart Mail Server.
class CheckMachine:
    def __init__(self, checker: ExtendedChecker):
        self.c = checker
        self.mailbox: MailBoxUnencrypted = None  # type: ignore
        self.with_exceptions(
            "connection establishment",
            Status.DOWN,
            self._connect,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        try:
            self.mailbox.__exit__(exc_type, exc_value, exc_traceback)
        except:
            # ignore possible exception on logout from mailbox because who cares
            pass
        if exc_type is not None:
            return False
        return True

    def _connect(self):
        self.mailbox = MailBoxUnencrypted(host=self.c.host, port=IMAP_PORT, timeout=1)
        self.mailbox.client.socket().settimeout(1)

    def login(self, username: str, password: str, status: Status):
        self.with_exceptions(
            "login", status, self.mailbox.login_utf8, username, password
        )

    def fetch_by_subject(self, subject: str, limit: int, status: Status) -> list[Email]:  # type: ignore
        try:
            return self.with_exceptions(
                "fetch", Status.MUMBLE, self._fetch_by_subject, subject, limit
            )
        except MessageError as e:
            self.c.cquit(
                status,
                "IMAP fetch returned invalid emails",
                f"Got email MessageError on fetch: {e}",
            )

    def _fetch_by_subject(self, subject: str, limit: int) -> list[Email]:
        messages = []
        for message in self.mailbox.fetch(AND(subject=subject), limit=limit, bulk=True):
            messages.append(
                Email(from_=message.from_, subject=message.subject, text=message.text)
            )
        return messages

    def with_exceptions(
        self,
        action: str,
        status: Status,
        f: Callable[P, T],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:  # type: ignore
        try:
            return f(*args, **kwargs)
        except ConnectionRefusedError:
            self.c.cquit(
                Status.DOWN,
                "IMAP connection error",
                f"Got IMAP connection error on {action}",
            )
        except TimeoutError:
            self.c.cquit(
                Status.DOWN,
                "IMAP request timeout",
                f"Got IMAP request timeout on {action}",
            )
        except IMAP4.error as e:
            self.c.cquit(
                status,
                f"IMAP {action} returned an error",
                f"Got IMAP4 error on {action}: {e}",
            )
        except UnexpectedCommandStatusError as e:
            self.c.cquit(
                status,
                f"IMAP {action} returned bad status {e.command_result}",
                f"Got imap-tools UnexpectedCommandStatusError on {action}: {e}",
            )
        except ImapToolsError as e:
            self.c.cquit(
                status,
                f"IMAP {action} returned an error",
                f"Got imap-tools error on {action}: {e}",
            )
