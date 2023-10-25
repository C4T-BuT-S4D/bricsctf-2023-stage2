
from pwn import *
from checklib import *

context.log_level = 'CRITICAL'

PORT = 4985

DEFAULT_RECV_SIZE = 4096
TCP_CONNECTION_TIMEOUT = 5
TCP_OPERATIONS_TIMEOUT = 7

class CheckMachine:
    sock = None

    def __init__(self, checker: BaseChecker):
        self.c = checker
        self.port = PORT

    def connection(self):
        try:
            self.sock = remote(self.c.host, self.port, timeout=TCP_CONNECTION_TIMEOUT)
        except:
            self.sock = None
            self.c.cquit( Status.DOWN, 'Connection error', 'CheckMachine.connection(): timeout connection!')

        self.sock.settimeout(TCP_OPERATIONS_TIMEOUT)

    def close_connect(self):
        try:
            self.sock.close()
            self.sock = None
        except:
            self.sock = None

    def safe_close_connection(self):
        try:
            self.sock.sendlineafter(b'> ', b'0')
            self.sock.close()
            self.sock = None
        except:
            self.sock = None

    def register(self, username: str, password: str, status: Status):
        try:
            self.sock.sendlineafter(b'> ', b'1')
            self.sock.sendlineafter(b': ', username.encode())
            self.sock.sendlineafter(b': ', password.encode())
            resp = self.sock.recvline()[:-1].decode()
            self.c.assert_eq(resp, 'Success', 'Invalid responce on register', status)
        except:
            self.close_connect()
            self.c.cquit(Status.MUMBLE, 'Can\'t register')

    def login(self, username: str, password: str, status: Status):
        try:
            self.sock.sendlineafter(b'> ', b'2')
            self.sock.sendlineafter(b': ', username.encode())
            self.sock.sendlineafter(b': ', password.encode())
            resp = self.sock.recvline()[:-1].decode()
            self.c.assert_eq(resp, 'Success', 'Invalid responce on login', status)
        except:
            self.close_connect()
            self.c.cquit(Status.MUMBLE, 'Can\'t login')

    def login_without_password(self, username: str, status: Status):
        try:
            self.sock.sendlineafter(b'> ', b'2')
            self.sock.sendlineafter(b': ', username.encode())
            resp = self.sock.recvline()[:-1].decode()
            self.c.assert_eq(resp, 'Success', 'Can\'t login without password', status)
        except:
            self.close_connect()
            self.c.cquit(Status.MUMBLE, 'Can\'t login without password')

    def logout(self, choice: str, status: Status):
        try:
            self.sock.sendlineafter(b'> ', b'1')
            self.sock.sendlineafter(b': ', choice.encode())
            resp = self.sock.recvline()[:-1].decode()
            self.c.assert_eq(resp, 'Success', 'Invalid responce on logout', status)
        except:
            self.close_connect()
            self.c.cquit(Status.MUMBLE, 'Can\'t logout')

    def add_note(self, note_name: str, note_info: str, status: Status):
        try:
            self.sock.sendlineafter(b'> ', b'2')
            self.sock.sendlineafter(b': ', note_name.encode())
            self.sock.sendlineafter(b': ', note_info.encode())
            resp = self.sock.recvline()[:-1].decode()
            self.c.assert_eq(resp, 'Success', 'Invalid responce on add_note', status)
        except:
            self.close_connect()
            self.c.cquit(Status.MUMBLE, 'Can\'t add note')

    def list_notes(self):
        try:
            self.sock.sendlineafter(b'> ', b'4')
            notes = []
            while (line := self.sock.recvline()) != b'\n':
                notes.append(line)
            return notes
        except:
            self.close_connect()
            self.c.cquit(Status.MUMBLE, 'Can\'t list notes')

    def show_note(self, note_id: int):
        try:
            self.sock.sendlineafter(b'> ', b'5')
            self.sock.sendlineafter(b': ', str(note_id).encode())
            note, note_info = self.sock.recvline()[:-1].decode(), self.sock.recvline()[:-1].decode()
            return note, note_info
        except:
            self.close_connect()
            self.c.cquit(Status.MUMBLE, 'Can\'t show note')

    def delete_note(self, note_id: int, status: Status):
        try:
            self.sock.sendlineafter(b'> ', b'6')
            self.sock.sendlineafter(b': ', str(note_id).encode())
            resp = self.sock.recvline()[:-1].decode()
            self.c.assert_eq(resp, 'Success', 'Invalid responce on delete_note', status)
        except:
            self.close_connect()
            self.c.cquit(Status.MUMBLE, 'Can\'t delete note')

    def add_secret_note(self, note: str, key: bytes, status: Status):
        try:
            self.sock.sendlineafter(b'> ', b'3')
            self.sock.sendlineafter(b': ', note.encode())
            self.sock.sendlineafter(b': ', key.hex().encode())
            resp = self.sock.recvline()[:-1].decode()
            self.c.assert_eq(resp, 'Success', 'Invalid responce on add_secret_note', status)
        except:
            self.close_connect()
            self.c.cquit(Status.MUMBLE, 'Can\'t add secret note')

    def list_shared_notes(self):
        try:
            self.sock.sendlineafter(b'> ', b'7')
            notes = []
            while (line := self.sock.recvline()) != b'\n':
                notes.append(line)
            return notes
        except:
            self.close_connect()
            self.c.cquit(Status.MUMBLE, 'Can\'t list shared notes')

    def show_shared_note(self, note_id: int):
        try:
            self.sock.sendlineafter(b'> ', b'8')
            self.sock.sendlineafter(b': ', str(note_id).encode())
            note, note_info = self.sock.recvline()[:-1].decode(), self.sock.recvline()[:-1].decode()
            return note, note_info
        except:
            self.close_connect()
            self.c.cquit(Status.MUMBLE, 'Can\'t show shared note')

    def delete_shared_note(self, note_id: int, status: Status):
        try:
            self.sock.sendlineafter(b'> ', b'9')
            self.sock.sendlineafter(b': ', str(note_id).encode())
            resp = self.sock.recvline()[:-1].decode()
            self.c.assert_eq(resp, 'Success', 'Invalid responce on delete_shared_note', status)
        except:
            self.close_connect()
            self.c.cquit(Status.MUMBLE, 'Can\'t delete shared note')

    def share_note(self, username: str, note_id: int, status: Status):
        try:
            self.sock.sendlineafter(b'> ', b'10')
            self.sock.sendlineafter(b': ', username.encode())
            self.sock.sendlineafter(b': ', str(note_id).encode())
            resp = self.sock.recvline()[:-1].decode()
            self.c.assert_eq(resp, 'Success', 'Invalid responce on share_note', status)
        except:
            self.close_connect()
            self.c.cquit(Status.MUMBLE, 'Can\'t share note')
    
    def show_secret_note(self):
        try:
            self.sock.sendlineafter(b'> ', b'11')
            resp = self.sock.recvline()[:-1].decode()
            return resp
        except:
            self.close_connect()
            self.c.cquit(Status.MUMBLE, 'Can\'t show secret note')
