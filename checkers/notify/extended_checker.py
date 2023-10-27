import os
from datetime import datetime
from typing import Any, Type, TypeVar, get_origin

import requests
from checklib import BaseChecker, Status

T = TypeVar("T")

LOGGING = os.getenv("LOGGING") == "t"


class ExtendedChecker(BaseChecker):
    def get_json_dict(
        self, resp: requests.Response, public: str, status: Status
    ) -> dict[str, Any]:
        data = self.get_json(resp, public, status)
        self.assert_type(data, dict, public, status)
        return data  # type: ignore

    def get_field(
        self,
        data: dict[str, Any],
        field: str,
        want_type: Type[T],
        public: str,
        status: Status,
    ) -> T:
        self.assert_in(field, data, f"missing {field} in {public}", status)
        v = data[field]
        self.assert_type(v, want_type, f"invalid {field} in {public}", status)
        return v

    def assert_type(self, a: Any, want_type: type, public: str, status: Status):
        origin = get_origin(want_type)
        if origin is not None:
            want_type = origin
        self.assert_(isinstance(a, want_type), public, status)

    def check_status(
        self, resp: requests.Response, want_status: int, public: str, status: Status
    ):
        if resp.status_code >= 500:
            self.cquit(Status.DOWN, public, f"Code {resp.status_code} on {resp.url}")

        self.assert_eq(
            resp.status_code,
            want_status,
            f"{public} returned bad status code {resp.status_code}",
            status,
        )

    def log(self, *args):
        if LOGGING:
            print(datetime.now(), *args, end="\n\n")
