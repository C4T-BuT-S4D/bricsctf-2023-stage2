#!/usr/bin/env python3
import userlib


saved_users = []
user = None

def get_username():
    username = input('Username: ')
    if not userlib.is_valid_string(username):
        print('Error: username doesn\'t match regex [a-zA-Z0-9]{5,31}')
        return ''

    if not userlib.user_exists(username):
        print('Error: user doesn\'t exist')
        return ''

    return username


def register():
    username = input('Username: ')
    password = input('Password: ')
    if not userlib.validate_creds(username, password):
        print('Error: username or password doesn\'t match regex [a-zA-Z0-9]{5,31}')
        return
    if userlib.user_exists(username):
        print('Error: user exists')
        return
    userlib.store_new_user(username, password)
    print('Success')


def login():
    global user
    username = get_username()
    if username == '':
        return

    for u in saved_users:
        if u.username == username:
            user = u
            print('Success')
            return

    password  = input('Password: ')
    if not userlib.is_valid_string(password):
        print('Error: password doesn\'t match regex [a-zA-Z0-9]{5,31}')
        return
    if not userlib.check_password(username, password):
        print('Error: wrong password')
        return
    user = userlib.User(username)
    print('Success')


def unauth_menu():
    print('0. exit\n1. register\n2. login')
    try:
        c = int(input('> '))
    except:
        print("Invalid choice")
        return
    
    if c == 0:
        return -1
    if c == 1:
        register()
        return
    if c == 2:
        login()
        return


def logout():
    global user
    c = input('Keep user in cache? (you won\'t need to enter password again in current session) [y/n]: ').strip()
    if c == 'y':
        if user not in saved_users:
            saved_users.append(user)
            if len(saved_users) > 10: saved_users.pop(0)
    else:
        i = 0
        while i < len(saved_users):
            if saved_users[i] == user:
                saved_users.pop(i)
                break
            i += 1
    user = None
    print('Success')


def add_note():
    try:
        note = input('Note: ').strip()
        additional_info = input('Additional info: ').strip()
        user.add_note(note, additional_info)
        print('Success')
    except:
        print('Error: invalid input or storage is full')


def add_secret_note():
    try:
        note = input('Secret note: ').encode()
        key = bytearray.fromhex(input('Key (hex): '))
        if len(key) == 0:
            raise ValueError()
        while len(key) < len(note):
            key = key * 2
        if len(key) > len(note):
            key = key[:len(note)]
        secret_note = bytearray([x ^ y for x, y in zip(key, note)])
        user.add_secret_note(secret_note, key)
        print('Success')
    except:
        print('Error: invalid input')


def show_secret_note():
    try:
        print(user.show_secret_note())
    except:
        print('Error: secret note is empty')


def list_notes():
    notes = user.notes
    for i in range(len(notes)):
        print(f'{i}. {notes[i]}')


def show_note():
    try:
        note_id = int(input('Note id: '))
        note, info = user.get_note(note_id)
        print(note)
        print(info)
    except:
        print('Error: invalid id')


def delete_note():
    try:
        note_id = int(input('Note id: '))
        user.delete_note(note_id)
        print('Success')
    except:
        print('Error: invalid id')


def list_shared_notes():
    notes = user.shared_notes
    for i in range(len(notes)):
        print(f'{i}. {notes[i]}')


def show_shared_note():
    try:
        note_id = int(input('Note id: '))
        note, info = user.get_shared_note(note_id)
        print(note)
        print(info)
    except:
        print('Error: invalid id')


def delete_shared_note():
    try:
        note_id = int(input('Note id: '))
        user.delete_shared_note(note_id)
        print('Success')
    except:
        print('Error: invalid id')


def share_note():
    username = get_username()
    if username == '':
        return
    try:
        note_id = int(input('Note id: '))
        for u in saved_users:
            if u.username == username:
                user.share_note(note_id, u)
                return
        user.share_note(note_id, userlib.User(username))
        print('Success')
    except:
        print('Error: invalid id or storage is full')


def auth_menu():
    print('\n0. exit\n1. logout\n2. add note\n3. add secret note\n4. list notes\n5. show note\n6. delete note\n7. list shared notes\n8. show shared note\n9. delete shared note\n10. share note\n11. show secret note')
    try:
        c = int(input('> '))
    except:
        print("Invalid")
        return 1
    
    if c == 0:
        return -1
    if c == 1:
        logout()
        return
    if c == 2:
        add_note()
        return
    if c == 3:
        add_secret_note()
        return
    if c == 4:
        list_notes()
        return
    if c == 5:
        show_note()
        return
    if c == 6:
        delete_note()
        return
    if c == 7:
        list_shared_notes()
        return
    if c == 8:
        show_shared_note()
        return
    if c == 9:
        delete_shared_note()
        return
    if c == 10:
        share_note()
        return
    if c == 11:
        show_secret_note()
        return


if __name__ == '__main__':
    while (1):
        if not user:
            c = unauth_menu()
        else:
            c = auth_menu()

        if c == -1:
            break
