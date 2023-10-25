#!/usr/bin/env python3

import sys
import requests
import time
import copy

from checklib import *

argv = copy.deepcopy(sys.argv)

from notes_lib import *


class Checker(BaseChecker):
    vulns: int = 1
    timeout: int = 5
    uses_attack_data: bool = False

    def __init__(self, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)
        self.mch = CheckMachine(self)

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except requests.exceptions.ConnectionError:
            self.cquit(Status.DOWN, 'Connection error', 'Got requests connection error')

    def check(self):
        self.mch.connection()
        user1, pass1 = rnd_username(), rnd_password()

        self.mch.register(user1, pass1, Status.MUMBLE)
        self.mch.login(user1, pass1, Status.MUMBLE)

        note1_name = rnd_string(10)
        note1_info = rnd_string(20)

        self.mch.add_note(note1_name, note1_info, Status.MUMBLE)

        notes = self.mch.list_notes()
        self.assert_in(True, [note1_name.encode() in note for note in notes], 'Can\'t list notes1')
        for note in notes:
            if note1_name.encode() in note:
                self.assert_(note.split(b'.')[0].isdigit(), 'Can\'t get note_id from notes list', Status.MUMBLE)
                note1_id = int(note.split(b'.')[0])
                break
        
        resp = self.mch.show_note(note1_id)
        self.assert_eq(resp[0], note1_name, 'Note1 name is invalid', Status.MUMBLE)
        self.assert_eq(resp[1], note1_info, 'Note1 info is invalid', Status.MUMBLE)

        self.mch.logout('n', Status.MUMBLE)

        user2, pass2 = rnd_username(), rnd_password()
        self.mch.register(user2, pass2, Status.MUMBLE)
        self.mch.login(user2, pass2, Status.MUMBLE)
        
        note2_name = rnd_string(10)
        note2_info = rnd_string(20)

        self.mch.add_note(note2_name, note2_info, Status.MUMBLE)
        self.mch.share_note(user1, 0, Status.MUMBLE)

        self.mch.logout('y', Status.MUMBLE)

        self.mch.login(user1, pass1, Status.MUMBLE)

        notes = self.mch.list_shared_notes()
        self.assert_in(True, [note2_name.encode() in note for note in notes], 'Can\'t list shared notes')
        for note in notes:
            if note2_name.encode() in note:
                self.assert_(note.split(b'.')[0].isdigit(), 'Can\'t get note_id from shared notes list', Status.MUMBLE)
                note2_id = int(note.split(b'.')[0])
                break
        resp = self.mch.show_shared_note(note2_id)
        self.assert_eq(resp[0], note2_name, 'Note2 name is invalid', Status.MUMBLE)
        self.assert_eq(resp[1], note2_info, 'Note2 info is invalid', Status.MUMBLE)

        self.mch.delete_shared_note(note2_id, Status.MUMBLE)
        notes = self.mch.list_shared_notes()
        self.assert_nin(True, [note2_name.encode() in note for note in notes], 'Can\'t delete shared note')

        self.mch.delete_note(note1_id, Status.MUMBLE)
        notes = self.mch.list_shared_notes()
        self.assert_nin(True, [note1_name.encode() in note for note in notes], 'Can\'t delete note')

        self.mch.logout('n', Status.MUMBLE)

        self.mch.login_without_password(user2, Status.MUMBLE)

        note3_name = rnd_string(10)
        note3_info = rnd_string(20)
        self.mch.add_note(note3_name, note3_info, Status.MUMBLE)

        secret_note = rnd_string(20)
        key = rnd_bytes(20)
        self.mch.add_secret_note(secret_note, key, Status.MUMBLE)

        self.mch.safe_close_connection()

        time.sleep(0.1)

        self.mch.connection()
        self.mch.login(user2, pass2, Status.MUMBLE)

        notes = self.mch.list_notes()
        self.assert_in(True, [note3_name.encode() in note for note in notes], 'Can\'t list notes3')
        for note in notes:
            if note3_name.encode() in note:
                self.assert_(note.split(b'.')[0].isdigit(), 'Can\'t get note_id from notes list', Status.MUMBLE)
                note3_id = int(note.split(b'.')[0])
                break
        
        resp = self.mch.show_note(note3_id)
        self.assert_eq(resp[0], note3_name, 'Note3 name is invalid', Status.MUMBLE)
        self.assert_eq(resp[1], note3_info, 'Note3 info is invalid', Status.MUMBLE)

        note = self.mch.show_secret_note()
        self.assert_(secret_note == note, 'Secret note is invalid', Status.MUMBLE)

        self.mch.safe_close_connection()

        self.cquit(Status.OK)

    def put(self, flag_id: str, flag: str, vuln: str):
        self.mch.connection()
        username, password = rnd_username(), rnd_password()

        self.mch.register(username, password, Status.MUMBLE)
        self.mch.login(username, password, Status.MUMBLE)

        key = rnd_bytes(len(flag))
        self.mch.add_secret_note(flag, key, Status.MUMBLE)

        self.mch.safe_close_connection()

        self.cquit(Status.OK, key.hex(), f'{username}:{password}')

    def get(self, flag_id: str, flag: str, vuln: str):
        self.mch.connection()
        username, password = flag_id.split(':')

        self.mch.login(username, password, Status.CORRUPT)
        value = self.mch.show_secret_note()

        self.assert_eq(value, flag, "Note value is invalid", Status.CORRUPT)

        self.mch.safe_close_connection()

        self.cquit(Status.OK)


if __name__ == '__main__':
    c = Checker(argv[2])

    try:
        c.action(argv[1], *argv[3:])
    except c.get_check_finished_exception():
        cquit(Status(c.status), c.public, c.private)