from pwn import *
from checklib import *

context.log_level = 'CRITICAL'

PORT = 4985

DEFAULT_RECV_SIZE = 4096
TCP_CONNECTION_TIMEOUT = 5
TCP_OPERATIONS_TIMEOUT = 7

class CheckMachine:

    def __init__(self, checker: BaseChecker):
        self.c = checker
        self.port = PORT

    def connection(self) -> remote:
        io = remote(self.c.host, self.port, timeout=TCP_CONNECTION_TIMEOUT)
        io.settimeout(TCP_OPERATIONS_TIMEOUT)
        return io

    def exit_(self, io: remote) -> None:
        io.sendlineafter(b'> ', b'0')

    def register(self, io: remote, username: str, password: str, status: Status) -> None:
        io.sendlineafter(b'> ', b'1')
        io.sendlineafter(b': ', username.encode())
        io.sendlineafter(b': ', password.encode())
        resp = io.recvline()[:-1]
        self.c.assert_eq(resp, b'Success', 'Invalid responce on register', status)

    def login(self, io: remote, username: str, password: str, status: Status) -> None:
        io.sendlineafter(b'> ', b'2')
        io.sendlineafter(b': ', username.encode())
        io.sendlineafter(b': ', password.encode())
        resp = io.recvline()[:-1]
        self.c.assert_eq(resp, b'Success', 'Invalid responce on login', status)

    def login_without_password(self, io: remote, username: str, status: Status) -> None:
        io.sendlineafter(b'> ', b'2')
        io.sendlineafter(b': ', username.encode())
        resp = io.recvline()[:-1]
        self.c.assert_eq(resp, b'Success', 'Can\'t login without password', status)

    def logout(self, io: remote, choice: str, status: Status) -> None:
        io.sendlineafter(b'> ', b'1')
        io.sendlineafter(b': ', choice.encode())
        resp = io.recvline()[:-1]
        self.c.assert_eq(resp, b'Success', 'Invalid responce on logout', status)
    
    def add_note(self, io: remote, note_name: str, note_info: str, status: Status) -> None:
        io.sendlineafter(b'> ', b'2')
        io.sendlineafter(b': ', note_name.encode())
        io.sendlineafter(b': ', note_info.encode())
        resp = io.recvline()[:-1]
        self.c.assert_eq(resp, b'Success', 'Invalid responce on add_note', status)

    def list_notes(self, io: remote) -> list[bytes]:
        io.sendlineafter(b'> ', b'4')
        notes = []
        while (line := io.recvline()) != b'\n':
            notes.append(line)
        return notes

    def show_note(self, io: remote, note_id: int) -> tuple[bytes, bytes]:
        io.sendlineafter(b'> ', b'5')
        io.sendlineafter(b': ', str(note_id).encode())
        note, note_info = io.recvline()[:-1], io.recvline()[:-1]
        return note, note_info

    def delete_note(self, io: remote, note_id: int, status: Status) -> None:
        io.sendlineafter(b'> ', b'6')
        io.sendlineafter(b': ', str(note_id).encode())
        resp = io.recvline()[:-1]
        self.c.assert_eq(resp, b'Success', 'Invalid responce on delete_note', status)

    def add_secret_note(self, io: remote, note: str, key: bytes, status: Status) -> None:
        io.sendlineafter(b'> ', b'3')
        io.sendlineafter(b': ', note.encode())
        io.sendlineafter(b': ', key.hex().encode())
        resp = io.recvline()[:-1]
        self.c.assert_eq(resp, b'Success', 'Invalid responce on add_secret_note', status)

    def list_shared_notes(self, io: remote) -> list[bytes]:
        io.sendlineafter(b'> ', b'7')
        notes = []
        while (line := io.recvline()) != b'\n':
            notes.append(line)
        return notes

    def show_shared_note(self, io: remote, note_id: int) -> tuple[bytes, bytes]:
        io.sendlineafter(b'> ', b'8')
        io.sendlineafter(b': ', str(note_id).encode())
        note, note_info = io.recvline()[:-1], io.recvline()[:-1]
        return note, note_info

    def delete_shared_note(self, io: remote, note_id: int, status: Status) -> None:
        io.sendlineafter(b'> ', b'9')
        io.sendlineafter(b': ', str(note_id).encode())
        resp = io.recvline()[:-1]
        self.c.assert_eq(resp, b'Success', 'Invalid responce on delete_shared_note', status)

    def share_note(self, io: remote, username: str, note_id: int, status: Status) -> None:
        io.sendlineafter(b'> ', b'10')
        io.sendlineafter(b': ', username.encode())
        io.sendlineafter(b': ', str(note_id).encode())
        resp = io.recvline()[:-1]
        self.c.assert_eq(resp, b'Success', 'Invalid responce on share_note', status)
    
    def show_secret_note(self, io: remote) -> bytes:
        io.sendlineafter(b'> ', b'11')
        resp = io.recvline()[:-1]
        return resp
