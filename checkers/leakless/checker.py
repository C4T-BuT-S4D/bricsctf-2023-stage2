#!/usr/bin/env python3

import sys
import string
import itertools
import random
import time

import requests

from checklib import *
from example_lib import *

def rnd_fake_flag():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=31)) + '='

def rnd_document(flag):
    return  ' '.join(itertools.chain(
                        (rnd_string(random.randint(5, 10)) for _ in range(random.randint(10, 50))),
                        (flag, ),
                        (rnd_string(random.randint(5, 10)) for _ in range(random.randint(10, 50))),
                    ))

class Checker(BaseChecker):
    vulns: int = 1
    timeout: int = 5
    uses_attack_data: bool = True

    def __init__(self, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)
        self.mch = CheckMachine(self)

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except requests.exceptions.ConnectionError:
            self.cquit(Status.DOWN, 'Connection error', 'Got requests connection error')

    def check_unsanitized_document1(self):
        if random.randint(0, 4) == 0:
            secret1 = rnd_fake_flag()
        else:
            secret1 = rnd_string(20)
        if random.randint(0, 4) == 0:
            secret2 = rnd_fake_flag()
        else:
            secret2 = rnd_string(20)

        session = get_initialized_session()
        name, username, password = rnd_string(20), rnd_username(), rnd_password()

        self.mch.register(session, name, username, password, Status.MUMBLE)
        self.mch.put_secret(session, secret1, Status.MUMBLE)

        company = self.mch.get_self_company(session, Status.MUMBLE)
        self.assert_in(secret1, (s.secret for s in company.secrets), "secret missing", Status.MUMBLE)

        session2 = get_initialized_session()
        document = rnd_document(secret2)
        document_id = self.mch.put_document(session2, company.uid, document, Status.MUMBLE)

        sanitized_document = self.mch.get_sanitized_document(session2, document_id, Status.MUMBLE)
        self.assert_eq(sanitized_document, document, "document oversanitized", Status.MUMBLE)

        self.cquit(Status.OK)

    def check_unsanitized_document2(self):
        if random.randint(0, 4) == 0:
            secret1 = rnd_fake_flag()
        else:
            secret1 = rnd_string(20)
        if random.randint(0, 4) == 0:
            secret2 = rnd_fake_flag()
        else:
            secret2 = rnd_string(20)

        session = get_initialized_session()
        name, username, password = rnd_string(20), rnd_username(), rnd_password()

        self.mch.register(session, name, username, password, Status.MUMBLE)
        self.mch.put_secret(session, secret1, Status.MUMBLE)
        secret_id = self.mch.put_secret(session, secret2, Status.MUMBLE)

        company = self.mch.get_self_company(session, Status.MUMBLE)
        self.assert_in(secret1, (s.secret for s in company.secrets), "secret missing", Status.MUMBLE)
        self.assert_in(secret2, (s.secret for s in company.secrets), "secret missing", Status.MUMBLE)


        session2 = get_initialized_session()
        document = rnd_document(secret2)
        document_id = self.mch.put_document(session2, company.uid, document, Status.MUMBLE)

        sanitized_document = self.mch.get_sanitized_document(session2, document_id, Status.MUMBLE)
        self.assert_eq(sanitized_document, document.replace(secret2, "*" * len(secret2)), "document undersanitized", Status.MUMBLE)

        session2 = get_initialized_session()
        document = rnd_document(secret2)
        document_id = self.mch.put_document(session2, company.uid, document, Status.MUMBLE)

        self.mch.delete_secret(session, secret_id, Status.MUMBLE)

        sanitized_document = self.mch.get_sanitized_document(session2, document_id, Status.MUMBLE)
        self.assert_eq(sanitized_document, document, "document oversanitized", Status.MUMBLE)

        self.cquit(Status.OK)

    def check(self):
        random.choice((
            self.check_unsanitized_document1,
            self.check_unsanitized_document2,
            ))()

    def put(self, flag_id: str, flag: str, vuln: str):
        session = get_initialized_session()
        name, username, password = rnd_string(20), rnd_username(), rnd_password()

        self.mch.register(session, name, username, password, Status.MUMBLE)
        self.mch.put_secret(session, flag, Status.MUMBLE)
        company = self.mch.get_self_company(session, Status.MUMBLE)
        self.assert_in(flag, (s.secret for s in company.secrets), "secret missing", Status.MUMBLE)
        

        self.cquit(Status.OK, f"{company.uid}", f"{username}:{password}:{company.uid}")

    def get_self_company(self, flag_id: str, flag: str, vuln: str):
        session = get_initialized_session()
        username, password, company_id = flag_id.split(':')

        self.mch.login(session, username, password, Status.CORRUPT)

        company = self.mch.get_self_company(session, Status.MUMBLE)
        self.assert_in(flag, (s.secret for s in company.secrets), "secret missing", Status.CORRUPT)


        self.cquit(Status.OK)

    def get_hash(self, flag_id: str, flag: str, vuln: str):
        session = get_initialized_session()
        username, password, company_id = flag_id.split(':')

        hashes = self.mch.get_company_hashes(session, company_id, Status.CORRUPT)
        self.assert_eq(self.mch.string_in_hashes(hashes, flag), True, "secret hash missing", Status.CORRUPT)

        self.cquit(Status.OK)

    def get_document(self, flag_id: str, flag: str, vuln: str):
        session = get_initialized_session()
        username, password, company_id = flag_id.split(':')

        document = rnd_document(flag)
        document_id = self.mch.put_document(session, company_id, document, Status.MUMBLE)

        session2 = get_initialized_session()
        self.mch.login(session2, username, password, Status.MUMBLE)
        self.assert_eq(self.mch.get_document(session2, document_id, Status.MUMBLE), document, 'document failed to upload correctly', Status.MUMBLE)

        sanitized_document = self.mch.get_sanitized_document(session, document_id, Status.MUMBLE)
        self.assert_eq(sanitized_document, document.replace(flag, '*' * len(flag)), "document not sanitized properly", Status.CORRUPT)

        self.cquit(Status.OK)

    def get(self, flag_id: str, flag: str, vuln: str):
        random.choice((
            self.get_self_company,
            self.get_hash,
            self.get_document,
            ))(flag_id, flag, vuln)


if __name__ == '__main__':
    c = Checker(sys.argv[2])

    try:
        c.action(sys.argv[1], *sys.argv[3:])
    except c.get_check_finished_exception():
        cquit(Status(c.status), c.public, c.private)
