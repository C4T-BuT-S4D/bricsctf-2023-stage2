import pwnlib.tubes.remote
from checklib import *

PORT = 4985

class CheckMachine:
    @property
    def url(self):
        return f'http://{self.c.host}:{self.port}'

    def __init__(self, checker: BaseChecker):
        self.c = checker
        self.port = PORT

    def register(self, io: pwnlib.tubes.remote.remote, username: str, password: str, status: Status):
        io.sendlineafter(b'> ', b'1')
        io.sendlineafter(b': ', username.encode())
        io.sendlineafter(b': ', password.encode())
        resp = io.recvline()[:-1].decode()
        self.c.assert_eq(resp, 'Success', 'Invalid responce on register', status)

    def login(self, io: pwnlib.tubes.remote.remote, username: str, password: str, status: Status):
        io.sendlineafter(b'> ', b'2')
        io.sendlineafter(b': ', username.encode())
        io.sendlineafter(b': ', password.encode())
        resp = io.recvline()[:-1].decode()
        self.c.assert_eq(resp, 'Success', 'Invalid responce on login', status)
    
    def login_without_password(self, io: pwnlib.tubes.remote.remote, username: str, status: Status):
        io.sendlineafter(b'> ', b'2')
        io.sendlineafter(b': ', username.encode())
        resp = io.recvline()[:-1].decode()
        self.c.assert_eq(resp, 'Success', 'Can\'t login without password', status)

    def logout(self, io: pwnlib.tubes.remote.remote, choice: str, status: Status):
        io.sendlineafter(b'> ', b'1')
        io.sendlineafter(b': ', choice.encode())
        resp = io.recvline()[:-1].decode()
        self.c.assert_eq(resp, 'Success', 'Invalid responce on logout', status)

    def add_note(self, io: pwnlib.tubes.remote.remote, note_name: str, note_info: str, status: Status):
        io.sendlineafter(b'> ', b'2')
        io.sendlineafter(b': ', note_name.encode())
        io.sendlineafter(b': ', note_info.encode())
        resp = io.recvline()[:-1].decode()
        self.c.assert_eq(resp, 'Success', 'Invalid responce on add_note', status)

    def list_notes(self, io: pwnlib.tubes.remote.remote):
        io.sendlineafter(b'> ', b'4')
        notes = []
        while (line := io.recvline()) != b'\n':
            notes.append(line)
        return notes
    
    def show_note(self, io: pwnlib.tubes.remote.remote, note_id: int):
        io.sendlineafter(b'> ', b'5')
        io.sendlineafter(b': ', str(note_id).encode())
        note, note_info = io.recvline()[:-1].decode(), io.recvline()[:-1].decode()
        return note, note_info

    def delete_note(self, io: pwnlib.tubes.remote.remote, note_id: int, status: Status):
        io.sendlineafter(b'> ', b'6')
        io.sendlineafter(b': ', str(note_id).encode())
        resp = io.recvline()[:-1].decode()
        self.c.assert_eq(resp, 'Success', 'Invalid responce on delete_note', status)

    def add_secret_note(self, io: pwnlib.tubes.remote.remote, note: str, key: bytes, status: Status):
        io.sendlineafter(b'> ', b'3')
        io.sendlineafter(b': ', note.encode())
        io.sendlineafter(b': ', key.hex().encode())
        resp = io.recvline()[:-1].decode()
        self.c.assert_eq(resp, 'Success', 'Invalid responce on add_secret_note', status)

    def list_shared_notes(self, io: pwnlib.tubes.remote.remote):
        io.sendlineafter(b'> ', b'7')
        notes = []
        while (line := io.recvline()) != b'\n':
            notes.append(line)
        return notes

    def show_shared_note(self, io: pwnlib.tubes.remote.remote, note_id: int):
        io.sendlineafter(b'> ', b'8')
        io.sendlineafter(b': ', str(note_id).encode())
        note, note_info = io.recvline()[:-1].decode(), io.recvline()[:-1].decode()
        return note, note_info

    def delete_shared_note(self, io: pwnlib.tubes.remote.remote, note_id: int, status: Status):
        io.sendlineafter(b'> ', b'9')
        io.sendlineafter(b': ', str(note_id).encode())
        resp = io.recvline()[:-1].decode()
        self.c.assert_eq(resp, 'Success', 'Invalid responce on delete_shared_note', status)

    def share_note(self, io: pwnlib.tubes.remote.remote, username: str, note_id: int, status: Status):
        io.sendlineafter(b'> ', b'10')
        io.sendlineafter(b': ', username.encode())
        io.sendlineafter(b': ', str(note_id).encode())
        resp = io.recvline()[:-1].decode()
        self.c.assert_eq(resp, 'Success', 'Invalid responce on share_note', status)
    
    def show_secret_note(self, io: pwnlib.tubes.remote.remote):
        io.sendlineafter(b'> ', b'11')
        resp = io.recvline()[:-1].decode()
        return resp
