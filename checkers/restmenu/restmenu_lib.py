import requests
from typing import Optional
from checklib import *

WEB_PORT = 8080


class CheckMachine:
    @property
    def url(self):
        return f'http://{self.c.host}:{self.web_port}'

    def __init__(self, checker: BaseChecker):
        self.c = checker
        self.web_port = WEB_PORT

    def register(self, session: requests.Session, username: str, password: str):
        resp = session.post(self.url + '/signup', json={'username': username, 'password': password})
        self.c.assert_eq(resp.status_code, 200, 'Failed to register')

    def login(self, session: requests.Session, username: str, password: str, status: Status):
        resp = session.post(self.url + '/login', json={'username': username, 'password': password})
        self.c.assert_eq(resp.status_code, 200, 'Failed to login', status=status)

    def upload_file(self, sessions: requests.Session, file_path: str) -> str:
        files = {'upload_file': open(file_path, 'rb')}
        resp = sessions.post(self.url + '/file/upload', files=files)
        self.c.assert_eq(resp.status_code, 200, 'Failed to upload file')
        return get_json(resp, "Failed to upload file: invalid JSON returned").get("id")

    def get_uploaded_files(self, session: requests.Session):
        resp = session.get(self.url + '/file')
        self.c.assert_eq(resp.status_code, 200, 'Failed to get user uploaded files')
        return get_json(resp, 'Failed to get user uploaded files: invalid JSON returned')

    def create_menu(self, session: requests.Session, name: str):
        resp = session.post(self.url + '/create', json={'name': name})
        self.c.assert_eq(resp.status_code, 200, 'Failed to create the menu')
        menu_json = get_json(resp, 'Failed to create menu: invalid JSON returned')
        self.c.assert_eq(type(menu_json), dict, 'Failed to create menu: invalid JSON returned')
        return menu_json

    def get_menu(self, session: requests.Session, menu_id: str, token: Optional[str] = None):
        params = {}
        if token:
            params['shareToken'] = token
        resp = session.get(self.url + f'/get/{menu_id}', params=params)
        self.c.assert_eq(resp.status_code, 200, 'Failed to get the menu')
        menu_json = get_json(resp, 'Failed to get menu: invalid JSON returned')
        self.c.assert_eq(type(menu_json), dict, 'Failed to get menu: invalid JSON returned')
        return menu_json

    def update_menu(self, session: requests.Session, updated: dict):
        resp = session.post(self.url + '/update', json={'menu': updated})
        self.c.assert_eq(resp.status_code, 200, f'Failed to update the menu')
        menu_json = get_json(resp, 'Failed to update menu: invalid JSON returned')
        self.c.assert_eq(type(menu_json), dict, 'Failed to update menu: invalid JSON returned')
        return menu_json

    def render_menu(self, session: requests.Session, menu_id: str, token: Optional[str] = None):
        params = {}
        if token:
            params['shareToken'] = token
        resp = session.get(self.url + f'/render/{menu_id}', params=params)
        self.c.assert_eq(resp.status_code, 200, 'Failed to render the menu')
        return resp.content
