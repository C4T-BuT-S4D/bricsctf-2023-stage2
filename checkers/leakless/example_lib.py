from typing import NamedTuple, List, Optional

import requests
from checklib import *

PORT = 2112

class Secret(NamedTuple):
    uid: int
    secret: str

class Company(NamedTuple):
    uid: int
    name: str
    login: str
    documents: List[int]
    secrets: Optional[List[Secret]]

class Hashes(NamedTuple):
    p: int
    q: int
    hashes: List[int]

    def hash(self, s: str) -> int:
        h = 0
        for c in s.encode("utf-8"):
            h = (h * self.q) % self.p
            h = (h + c) % self.p
        return h


class CheckMachine:
    @property
    def url(self):
        return f'http://{self.c.host}:{self.port}'

    def __init__(self, checker: BaseChecker):
        self.c = checker
        self.port = PORT

    def register(self, session: requests.Session, name: str, login: str, password: str, status: Status):
        resp = session.post(f"{self.url}/register", json={
            "name": name,
            "login": login,
            "password": password,
            })

        resp = self.c.get_json(resp, "invalid response on register", status)
        self.c.assert_eq(type(resp), dict, "invalid response on register", status)
        if resp.get("status") != "success":
            self.c.cquit(status, f"could not register: {resp.get('message', '')}")
        self.c.assert_eq(type(resp.get("message")), dict, "invalid response on register", status)
        jwt = resp["message"].get("jwt")
        self.c.assert_eq(type(jwt), str, "invalid response on register", status)

        session.headers["Authorization"] = f"Bearer {jwt}"


    def login(self, session: requests.Session, login: str, password: str, status: Status):
        resp = session.post(f"{self.url}/login", json={
            "login": login,
            "password": password,
            })

        resp = self.c.get_json(resp, "invalid response on login", status)
        self.c.assert_eq(type(resp), dict, "invalid response on login", status)
        if resp.get("status") != "success":
            self.c.cquit(status, f"could not login: {resp.get('message', '')}")
        self.c.assert_eq(type(resp.get("message")), dict, "invalid response on login", status)
        jwt = resp["message"].get("jwt")
        self.c.assert_eq(type(jwt), str, "invalid response on login", status)

        session.headers["Authorization"] = f"Bearer {jwt}"

    def put_secret(self, session: requests.Session, secret: str, status: Status) -> int:
        resp = session.put(f"{self.url}/me/secret", json={
            "secret": secret,
            })

        resp = self.c.get_json(resp, "invalid response on PutSecret", status)
        self.c.assert_eq(type(resp), dict, "invalid response on PutSecret", status)
        if resp.get("status") != "success":
            self.c.cquit(status, f"could not PutSecret: {resp.get('message', '')}")
        self.c.assert_eq(type(resp.get("message")), dict, "invalid response on PutSecret", status)
        uid = resp["message"].get("id")
        self.c.assert_eq(type(uid), int, "invalid response on PutSecret", status)

        return uid


    def get_secret(self, session: requests.Session, secret_id: int, status: Status) -> str:
        resp = session.get(f"{self.url}/me/secret/{secret_id}")

        resp = self.c.get_json(resp, "invalid response on GetSecret", status)
        self.c.assert_eq(type(resp), dict, "invalid response on GetSecret", status)
        if resp.get("status") != "success":
            self.c.cquit(status, f"could not GetSecret: {resp.get('message', '')}")
        self.c.assert_eq(type(resp.get("message")), dict, "invalid response on GetSecret", status)
        secret = resp["message"].get("secret")
        self.c.assert_eq(type(secret), str, "invalid response on GetSecret", status)

        return resp["message"]["secret"]

    def delete_secret(self, session: requests.Session, secret_id: int, status: Status):
        resp = session.delete(f"{self.url}/me/secret/{secret_id}")

        resp = self.c.get_json(resp, "invalid response on DeleteSecret", status)
        self.c.assert_eq(type(resp), dict, "invalid response on DeleteSecret", status)
        if resp.get("status") != "success":
            self.c.cquit(status, f"could not DeleteSecret: {resp.get('message', '')}")



    def get_company(self, session: requests.Session, company_id: int, status: Status) -> Company:
        resp = session.get(f"{self.url}/company/{secret_id}")

        resp = self.c.get_json(resp, "invalid response on GetCompany", status)
        self.c.assert_eq(type(resp), dict, "invalid response on GetCompany", status)
        if resp.get("status") != "success":
            self.c.cquit(status, f"could not GetCompany: {resp.get('message', '')}")
        self.c.assert_eq(type(resp.get("message")), dict, "invalid response on GetCompany", status)

        uid = resp["message"].get("id")
        name = resp["message"].get("name")
        login = resp["message"].get("login")
        documents = resp["message"].get("documents")
        self.c.assert_eq(type(uid), int, "invalid response on GetCompany", status)
        self.c.assert_eq(type(name), str, "invalid response on GetCompany", status)
        self.c.assert_eq(type(login), str, "invalid response on GetCompany", status)
        self.c.assert_eq(type(documents), list, "invalid response on GetCompany", status)
        for doc in documents:
            self.c.assert_eq(type(doc), int, "invalid response on GetCompany", status)

        return Company(
                uid=uid,
                name=name,
                login=login,
                documents=documents,
                secrets=None,
                )

    def get_self_company(self, session: requests.Session, status: Status) -> Company:
        resp = session.get(f"{self.url}/me")

        resp = self.c.get_json(resp, "invalid response on GetCompany", status)
        self.c.assert_eq(type(resp), dict, "invalid response on GetCompany", status)
        if resp.get("status") != "success":
            self.c.cquit(status, f"could not GetCompany: {resp.get('message', '')}")
        self.c.assert_eq(type(resp.get("message")), dict, "invalid response on GetCompany", status)

        uid = resp["message"].get("id")
        name = resp["message"].get("name")
        login = resp["message"].get("login")
        documents = resp["message"].get("documents")
        resp_secrets = resp["message"].get("secrets")
        self.c.assert_eq(type(uid), int, "invalid response on GetCompany", status)
        self.c.assert_eq(type(name), str, "invalid response on GetCompany", status)
        self.c.assert_eq(type(login), str, "invalid response on GetCompany", status)
        self.c.assert_eq(type(documents), list, "invalid response on GetCompany", status)
        for doc in documents:
            self.c.assert_eq(type(doc), int, "invalid response on GetCompany", status)

        secrets = []
        for sec in resp_secrets:
            secret = sec.get("secret")
            secret_id = sec.get("id")
            self.c.assert_eq(type(secret), str, "invalid response on GetCompany", status)
            self.c.assert_eq(type(secret_id), int, "invalid response on GetCompany", status)
            secrets.append(Secret(
                secret=secret,
                uid=secret_id,
                ))

        return Company(
                uid=uid,
                name=name,
                login=login,
                documents=documents,
                secrets=secrets,
                )

    def get_company_hashes(self, session: requests.Session, company_id: int, status: Status) -> Hashes:
        resp = session.get(f"{self.url}/company/{company_id}/hashes")

        resp = self.c.get_json(resp, "invalid response on GetHashes", status)
        self.c.assert_eq(type(resp), dict, "invalid response on GetHashes", status)
        if resp.get("status") != "success":
            self.c.cquit(status, f"could not GetHashes: {resp.get('message', '')}")
        self.c.assert_eq(type(resp.get("message")), dict, "invalid response on GetHashes", status)

        p = resp["message"].get("p")
        q = resp["message"].get("q")
        hashes = resp["message"].get("hashes")
        self.c.assert_eq(type(p), int, "invalid response on GetHashes", status)
        self.c.assert_eq(type(q), int, "invalid response on GetHashes", status)
        self.c.assert_eq(type(hashes), list, "invalid response on GetHashes", status)
        for h in hashes:
            self.c.assert_eq(type(h), int, "invalid response on GetHashes", status)

        return Hashes(
            p=p,
            q=q,
            hashes=hashes,
            )

    def put_document(self, session: requests.Session, company_id: int, text: str, status: Status) -> List[int]:
        resp = session.put(f"{self.url}/company/{company_id}/doc", json={
            "text": text,
            })

        resp = self.c.get_json(resp, "invalid response on PutDocument", status)
        self.c.assert_eq(type(resp), dict, "invalid response on PutDocument", status)
        if resp.get("status") != "success":
            self.c.cquit(status, f"could not PutDocument: {resp.get('message', '')}")
        self.c.assert_eq(type(resp.get("message")), dict, "invalid response on PutDocument", status)

        uid = resp["message"].get("id")
        self.c.assert_eq(type(uid), int, "invalid response on PutDocument", status)

        return uid

    def get_document(self, session: requests.Session, document_id: int, status: Status) -> str:
        resp = session.get(f"{self.url}/doc/{document_id}")

        resp = self.c.get_json(resp, "invalid response on GetDocument", status)
        self.c.assert_eq(type(resp), dict, "invalid response on GetDocument", status)
        if resp.get("status") != "success":
            self.c.cquit(status, f"could not GetDocument: {resp.get('message', '')}")
        self.c.assert_eq(type(resp.get("message")), dict, "invalid response on GetDocument", status)
        text = resp["message"].get("text")
        self.c.assert_eq(type(text), str, "invalid response on GetDocument", status)

        return text

    def get_sanitized_document(self, session: requests.Session, document_id: int, status: Status) -> str:
        resp = session.get(f"{self.url}/doc/{document_id}/sanitized")

        resp = self.c.get_json(resp, "invalid response on GetSanitizedDocument", status)
        self.c.assert_eq(type(resp), dict, "invalid response on GetSanitizedDocument", status)
        if resp.get("status") != "success":
            self.c.cquit(status, f"could not GetSanitizedDocument: {resp.get('message', '')}")
        self.c.assert_eq(type(resp.get("message")), dict, "invalid response on GetSanitizedDocument", status)
        text = resp["message"].get("text")
        self.c.assert_eq(type(text), str, "invalid response on GetSanitizedDocument", status)

        return text
