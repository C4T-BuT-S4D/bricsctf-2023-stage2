from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urljoin
from functools import cache

import requests
from checklib import Status
from extended_checker import ExtendedChecker

API_PORT = 7777


class Endpoints:
    REGISTER = "POST /register"
    LOGIN = "POST /login"
    CREATE_NOTIFICATION = "POST /notifications"
    GET_NOTIFICATION = "GET /notification/:id"
    USER_INFO = "GET /user"


@dataclass(frozen=True)
class NotificationCreationRepetitions:
    count: int
    interval: int

    def asdict(self) -> dict:
        return {"c": self.count, "i": self.interval}

    @staticmethod
    def fromdict(d) -> "NotificationCreationRepetitions":
        return NotificationCreationRepetitions(count=d["c"], interval=d["i"])


@dataclass(frozen=True)
class NotificationCreationOpts:
    title: str
    content: str
    notify_at: datetime
    repetitions: Optional[NotificationCreationRepetitions]

    @cache
    def to_private_info(self, id: str) -> "PrivateNotificationInfo":
        return PrivateNotificationInfo(
            id=id,
            title=self.title,
            content=self.content,
            plan=self.repetitions_to_plan(),
        )

    @cache
    def to_public_info(self) -> "PublicNotificationInfo":
        return PublicNotificationInfo(title=self.title, plan=self.repetitions_to_plan())

    @cache
    def repetitions_to_plan(self) -> list["NotificationPlan"]:
        plan = [NotificationPlan(planned_at=self.notify_at, sent_at=None)]

        if self.repetitions is not None:
            for _ in range(self.repetitions.count):
                plan.append(
                    NotificationPlan(
                        planned_at=plan[-1].planned_at
                        + timedelta(seconds=self.repetitions.interval),
                        sent_at=None,
                    )
                )

        return plan

    def asdict(self) -> dict:
        return {
            "t": self.title,
            "c": self.content,
            "n": self.notify_at.timestamp(),
            "r": self.repetitions.asdict() if self.repetitions is not None else None,
        }

    @staticmethod
    def fromdict(d) -> "NotificationCreationOpts":
        return NotificationCreationOpts(
            title=d["t"],
            content=d["c"],
            notify_at=datetime.fromtimestamp(d["n"], tz=timezone.utc),
            repetitions=NotificationCreationRepetitions.fromdict(d["r"]),
        )


@dataclass
class NotificationPlan:
    planned_at: datetime
    sent_at: Optional[datetime]


@dataclass
class PrivateNotificationInfo:
    id: str
    title: str
    content: str
    plan: list[NotificationPlan]


@dataclass
class PublicNotificationInfo:
    title: str
    plan: list[NotificationPlan]


@dataclass
class UserInfo:
    username: str
    notifications: list[PrivateNotificationInfo]


# CheckMachine for the HTTP-based notify-api.
# timeouts are set so that the service isn't able to cheat the checker while it is waiting for notifications to be sent.
class CheckMachine:
    def __init__(self, checker: ExtendedChecker):
        self.c = checker
        self.port = API_PORT

    def url(self, path):
        return urljoin(f"http://{self.c.host}:{self.port}/api/", path)

    def register(self, session: requests.Session, username: str, password: str):
        resp = session.post(
            self.url("register"),
            json={"username": username, "password": password},
            timeout=1,
        )

        self.c.check_status(resp, 201, Endpoints.REGISTER, Status.MUMBLE)

        self.c.assert_in(
            "notify_session",
            resp.cookies,
            f"{Endpoints.REGISTER} didn't return session",
            Status.MUMBLE,
        )

    def login(
        self, session: requests.Session, username: str, password: str, status: Status
    ):
        resp = session.post(
            self.url("login"),
            json={"username": username, "password": password},
            timeout=1,
        )

        self.c.check_status(resp, 200, Endpoints.LOGIN, status)

        self.c.assert_in(
            "notify_session",
            resp.cookies,
            f"{Endpoints.LOGIN} didn't return session",
            Status.MUMBLE,
        )

    def user_info(self, session: requests.Session) -> UserInfo:
        resp = session.get(self.url("user"), timeout=1)

        self.c.check_status(resp, 200, Endpoints.USER_INFO, Status.MUMBLE)

        data = self.c.get_json_dict(
            resp, f"{Endpoints.USER_INFO} returned invalid response", Status.MUMBLE
        )

        username = self.c.get_field(
            data, "username", str, f"{Endpoints.USER_INFO} response", Status.MUMBLE
        )

        notifications = self.c.get_field(
            data,
            "notifications",
            list[dict],
            f"{Endpoints.USER_INFO} response",
            Status.MUMBLE,
        )

        user = UserInfo(username, [])

        for notification in notifications:
            public_info = self.parse_public_notification(
                notification, f"{Endpoints.USER_INFO} response"
            )

            notification_id = self.c.get_field(
                notification,
                "id",
                str,
                f"notifications in {Endpoints.USER_INFO} response",
                Status.MUMBLE,
            )

            content = self.c.get_field(
                notification,
                "content",
                str,
                f"notifications in {Endpoints.USER_INFO} response",
                Status.MUMBLE,
            )

            user.notifications.append(
                PrivateNotificationInfo(
                    id=notification_id,
                    title=public_info.title,
                    content=content,
                    plan=public_info.plan,
                )
            )

        return user

    def create_notification(
        self, session: requests.Session, notification: NotificationCreationOpts
    ) -> str:
        request = {
            "title": notification.title,
            "content": notification.content,
            "notify_at": notification.notify_at.isoformat(),
        }

        if notification.repetitions is not None:
            request["repetitions"] = {  # type: ignore
                "count": notification.repetitions.count,
                "interval": notification.repetitions.interval,
            }

        resp = session.post(self.url("notifications"), json=request, timeout=1)

        self.c.check_status(resp, 201, Endpoints.CREATE_NOTIFICATION, Status.MUMBLE)

        data = self.c.get_json_dict(
            resp,
            f"{Endpoints.CREATE_NOTIFICATION} returned invalid response",
            Status.MUMBLE,
        )

        notification_id = self.c.get_field(
            data,
            "notification_id",
            str,
            f"{Endpoints.CREATE_NOTIFICATION} response",
            Status.MUMBLE,
        )

        self.c.assert_neq(
            notification_id,
            "",
            f"{Endpoints.CREATE_NOTIFICATION} returned empty notification_id",
            Status.MUMBLE,
        )

        return notification_id

    def get_notification(
        self,
        session: requests.Session,
        notification_id: str,
        status: Status,
    ) -> PublicNotificationInfo:
        resp = session.get(self.url(f"notification/{notification_id}"), timeout=0.5)

        self.c.check_status(resp, 200, Endpoints.GET_NOTIFICATION, status)

        data = self.c.get_json_dict(
            resp,
            f"{Endpoints.GET_NOTIFICATION} returned invalid response",
            Status.MUMBLE,
        )

        public_info = self.parse_public_notification(
            data, f"{Endpoints.GET_NOTIFICATION} response"
        )

        return public_info

    def parse_public_notification(
        self, data: dict, location: str
    ) -> PublicNotificationInfo:
        title = self.c.get_field(
            data,
            "title",
            str,
            location,
            Status.MUMBLE,
        )

        plan = self.c.get_field(
            data,
            "plan",
            list[dict],
            location,
            Status.MUMBLE,
        )

        parsed_plan: list[NotificationPlan] = []

        for p in plan:
            planned_at = self.c.get_field(
                p,
                "planned_at",
                str,
                location,
                Status.MUMBLE,
            )

            planned_at = self.parse_datetime(
                planned_at, f"invalid planned_at in {location}"
            )

            sent_at = p.get("sent_at")
            if sent_at is not None:
                self.c.assert_type(
                    sent_at, str, f"invalid sent_at in {location}", Status.MUMBLE
                )

                sent_at = self.parse_datetime(sent_at, f"invalid sent_at in {location}")

            parsed_plan.append(NotificationPlan(planned_at, sent_at))

        return PublicNotificationInfo(title=title, plan=parsed_plan)

    def parse_datetime(self, v: str, public: str) -> datetime:  # type: ignore
        try:
            return datetime.fromisoformat(v)
        except Exception as e:
            self.c.cquit(
                Status.MUMBLE,
                public,
                f"Failed to parse string {v} as Iso8601: {e}",
            )
