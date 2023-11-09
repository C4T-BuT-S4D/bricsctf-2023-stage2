#!/usr/bin/env python3

import sys
import time
import copy

from checklib import *

argv = copy.deepcopy(sys.argv)

from notes_lib import *


class Checker(BaseChecker):
    vulns: int = 1
    timeout: int = 10
    uses_attack_data: bool = False

    def __init__(self, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)
        self.mch = CheckMachine(self)

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except pwnlib.exception.PwnlibException:
            self.cquit(Status.DOWN, 'Connection error', 'Got requests connection error')

    def check(self):
        with self.mch.connection() as io:
            user1, pass1 = rnd_username(), rnd_password()

            self.mch.register(io, user1, pass1, Status.MUMBLE)

            io.sendlineafter(b'> ', b'2')
            io.sendlineafter(b': ', user1.encode())
            io.sendlineafter(b': ', rnd_password().encode())
            resp = io.recvline()[:-1]
            self.mch.c.assert_in(b'Error', resp, 'Can login with wrong password', Status.MUMBLE)

            self.mch.login(io, user1, pass1, Status.MUMBLE)

            note1_name = rnd_string(10)
            note1_info = rnd_string(20)

            self.mch.add_note(io, note1_name, note1_info, Status.MUMBLE)

            notes = self.mch.list_notes(io)
            self.assert_in(True, [note1_name.encode() in note for note in notes], 'Can\'t list notes1')
            for note in notes:
                if note1_name.encode() in note:
                    self.assert_(note.split(b'.')[0].isdigit(), 'Can\'t get note_id from notes list', Status.MUMBLE)
                    note1_id = int(note.split(b'.')[0])
                    break

            resp = self.mch.show_note(io, note1_id)
            self.assert_eq(resp[0], note1_name.encode(), 'Note1 name is invalid', Status.MUMBLE)
            self.assert_eq(resp[1], note1_info.encode(), 'Note1 info is invalid', Status.MUMBLE)

            self.mch.logout(io, 'n', Status.MUMBLE)

            user2, pass2 = rnd_username(), rnd_password()
            self.mch.register(io, user2, pass2, Status.MUMBLE)
            self.mch.login(io, user2, pass2, Status.MUMBLE)

            note2_name = rnd_string(10)
            note2_info = rnd_string(20)

            self.mch.add_note(io, note2_name, note2_info, Status.MUMBLE)
            self.mch.share_note(io, user1, 0, Status.MUMBLE)

            self.mch.logout(io, 'y', Status.MUMBLE)

            self.mch.login(io, user1, pass1, Status.MUMBLE)

            notes = self.mch.list_shared_notes(io)
            self.assert_in(True, [note2_name.encode() in note for note in notes], 'Can\'t list shared notes')
            for note in notes:
                if note2_name.encode() in note:
                    self.assert_(note.split(b'.')[0].isdigit(), 'Can\'t get note_id from shared notes list',
                                 Status.MUMBLE)
                    note2_id = int(note.split(b'.')[0])
                    break
            resp = self.mch.show_shared_note(io, note2_id)
            self.assert_eq(resp[0], note2_name.encode(), 'Note2 name is invalid', Status.MUMBLE)
            self.assert_eq(resp[1], note2_info.encode(), 'Note2 info is invalid', Status.MUMBLE)

            self.mch.delete_shared_note(io, note2_id, Status.MUMBLE)
            notes = self.mch.list_shared_notes(io)
            self.assert_nin(True, [note2_name.encode() in note for note in notes], 'Can\'t delete shared note')

            self.mch.delete_note(io, note1_id, Status.MUMBLE)
            notes = self.mch.list_shared_notes(io)
            self.assert_nin(True, [note1_name.encode() in note for note in notes], 'Can\'t delete note')

            self.mch.logout(io, 'n', Status.MUMBLE)

            self.mch.login_without_password(io, user2, Status.MUMBLE)

            note3_name = rnd_string(10)
            note3_info = rnd_string(20)
            self.mch.add_note(io, note3_name, note3_info, Status.MUMBLE)

            secret_note = rnd_string(20)
            key = rnd_bytes(20)
            self.mch.add_secret_note(io, secret_note, key, Status.MUMBLE)

            self.mch.exit_(io)

        time.sleep(0.1)

        with self.mch.connection() as io:
            self.mch.login(io, user2, pass2, Status.MUMBLE)

            notes = self.mch.list_notes(io)
            self.assert_in(True, [note3_name.encode() in note for note in notes], 'Can\'t list notes3')
            for note in notes:
                if note3_name.encode() in note:
                    self.assert_(note.split(b'.')[0].isdigit(), 'Can\'t get note_id from notes list', Status.MUMBLE)
                    note3_id = int(note.split(b'.')[0])
                    break

            resp = self.mch.show_note(io, note3_id)
            self.assert_eq(resp[0], note3_name.encode(), 'Note3 name is invalid', Status.MUMBLE)
            self.assert_eq(resp[1], note3_info.encode(), 'Note3 info is invalid', Status.MUMBLE)

            note = self.mch.show_secret_note(io)
            self.assert_(secret_note.encode() == note, 'Secret note is invalid', Status.MUMBLE)

            self.mch.exit_(io)

        self.cquit(Status.OK)

    def put(self, flag_id: str, flag: str, vuln: str):
        with self.mch.connection() as io:
            username, password = rnd_username(), rnd_password()

            self.mch.register(io, username, password, Status.MUMBLE)
            self.mch.login(io, username, password, Status.MUMBLE)

            key = rnd_bytes(len(flag))
            self.mch.add_secret_note(io, flag, key, Status.MUMBLE)

            self.mch.exit_(io)

        self.cquit(Status.OK, f'{username}:{password}', '')

    def get(self, flag_id: str, flag: str, vuln: str):
        with self.mch.connection() as io:
            username, password = flag_id.split(':')

            self.mch.login(io, username, password, Status.CORRUPT)
            value = self.mch.show_secret_note(io)

            self.assert_eq(value, flag.encode(), "Note value is invalid", Status.CORRUPT)

            self.mch.exit_(io)

        self.cquit(Status.OK)


if __name__ == '__main__':
    c = Checker(argv[2])

    try:
        c.action(argv[1], *argv[3:])
    except c.get_check_finished_exception():
        cquit(Status(c.status), c.public, c.private)
