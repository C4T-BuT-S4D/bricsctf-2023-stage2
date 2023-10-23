import requests
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
        self.c.assert_eq(resp.status_code, 200, 'Failed to register new user: {}, {}'.format(username, password))

    def login(self, session: requests.Session, username: str, password: str, status: Status):
        resp = session.post(self.url + '/login', json={'username': username, 'password': password})
        self.c.assert_eq(resp.status_code, 200, 'Failed to login using web', status=status)

    def upload_file(self, sessions: requests.Session, file_path: str) -> str:
        files = {'upload_file': open(file_path, 'rb')}
        resp = sessions.post(self.url + '/file/upload', files=files)
        self.c.assert_eq(resp.status_code, 200, 'Failed to upload file')
        return get_json(resp, "Failed to upload file: invalid JSON returned").get("id")

    def get_uploaded_files(self, session: requests.Session):
        resp = session.get(self.url + '/file')
        self.c.assert_eq(resp.status_code, 200, 'Failed to get user indexed files')
        return get_json(resp, 'Failed to get user uploaded files: invalid JSON returned')

    def create_menu(self, session: requests.Session, name: str):
        resp = session.post(self.url + '/create', json={'name': name})
        self.c.assert_eq(resp.status_code, 200, 'Failed to create the menu')
        return get_json(resp, 'Failed to create menu: invalid JSON returned')

    def get_menu(self, session: requests.Session, menu_id):
        resp = session.get(self.url + f'/get/{menu_id}')
        self.c.assert_eq(resp.status_code, 200, 'Failed to get the menu')
        return get_json(resp, 'Failed to get menu: invalid JSON returned')

    def update_menu(self, session: requests.Session, updated: dict):
        resp = session.post(self.url + '/update', json={'menu': updated})
        self.c.assert_eq(resp.status_code, 200, f'Failed to update the menu')
        return get_json(resp, 'Failed to update menu: invalid JSON returned')

    def render_menu(self, session: requests.Session, menu_id: str):
        resp = session.get(self.url + f'/render/{menu_id}')
        self.c.assert_eq(resp.status_code, 200, 'Failed to render the menu')
        return resp.content