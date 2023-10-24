#!/usr/bin/env python3
import os
import random
import re
import sys
import tempfile

import checklib
import requests
import textract
from checklib import *
from checklib import status

import restmenu_lib


class Checker(BaseChecker):
    vulns: int = 1
    timeout: int = 15
    uses_attack_data: bool = True

    def __init__(self, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)
        self.cm = restmenu_lib.CheckMachine(self)
        self.id_regexp = re.compile(r'^[0-9A-Za-z]{1,40}$')

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except requests.exceptions.ConnectionError:
            self.cquit(Status.DOWN, 'Connection error', 'Got requests connection error')

    def random_rest_name(self):
        options = [
            'City Sizzle Grill',
            'Sunset Breeze Cafe',
            'Gourmet Oasis',
            'Spice Haven Kitchen',
            'Fresh Harvest Bistro',
            'Sea Salt Serenity',
            'The Hungry Palette',
            'Flavors of Elegance',
            'Garden Grove Dining',
            'Culinary Canvas Café',
            'Tarra Gril',
            'Eazy Gril',
            'Shake Poke',
            'Harbour Kebab',
            'Shoe Lane',
            'StartBucks',
        ]
        return random.choice(options) + checklib.rnd_string(2)

    def random_rest_category(self):
        options = [
            'Main',
            'Dishes',
            'Lunch',
            'Dinner',
            'Drinks',
        ]
        return random.choice(options)

    def random_item_name(self):
        options = [
            'pizza',
            'steak',
            'pasta',
            'ale',
            'stout',
            'beer',
            'coffee',
            'oats',
            'fish and chips',
            'chicken',
            'churros'
        ]
        return random.choice(options) + checklib.rnd_string(2)

    def random_description(self):
        return 'Really delicious' + checklib.rnd_string(12)

    def get_image_paths(self):
        webm_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
        return [os.path.join(webm_dir, x) for x in os.listdir(webm_dir) if not x.startswith('.')]

    def random_image(self):
        return random.choice(self.get_image_paths())

    def validate_mid(self, mid):
        self.assert_eq(bool(self.id_regexp.fullmatch(mid)), True, 'Invalid id format')

    def extract_text(self, content):
        ntf = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        ntf.write(content)
        ntf.close()
        data = textract.process(ntf.name, encoding='utf-8')
        os.unlink(ntf.name)
        return data

    def check(self):
        sess = get_initialized_session()
        u = rnd_username(10)
        p = rnd_password(10)

        self.cm.register(sess, u, p)
        self.cm.login(sess, u, p, status=status.Status.MUMBLE)

        name = self.random_rest_name()
        menu = self.cm.create_menu(sess, name)

        img = self.random_image()
        file_id = self.cm.upload_file(sess, img)
        self.assert_in(file_id, self.cm.get_uploaded_files(sess).get('files'), 'Failed to find uploaded user file')

        menu = self.cm.get_menu(sess, menu.get('id'))
        category = self.random_rest_category()
        item = self.random_item_name()
        description = self.random_description()
        price = random.randint(0, 1000)
        menu['categories'] = [

            {'name': category, 'items': [
                {'name': item, 'price': price, 'description': description,
                 'image': file_id,
                 },
            ]}
        ]
        menu['shared'] = True
        updated_menu = self.cm.update_menu(sess, menu)

        new_sess = get_initialized_session()
        su = rnd_username(10)
        sp = rnd_password(10)
        self.cm.register(new_sess, su, sp)

        fetched_menu = self.cm.get_menu(new_sess, updated_menu.get('id'))
        self.assert_eq(name, fetched_menu.get('name'), 'Failed to get the menu')
        cat = fetched_menu.get('categories')[0] if len(fetched_menu.get('categories')) > 0 else {}
        self.assert_eq(category, cat.get('name'), 'Failed to get the menu')
        it = cat.get('items')[0] if len(cat.get('items')) > 0 else {}
        self.assert_eq(item, it.get('name'), 'Failed to get the menu')
        self.assert_eq(price, it.get('price'), 'Failed to get the menu')
        self.assert_eq(description, it.get('description'), 'Failed to get the menu')
        self.assert_eq(file_id, it.get('image'), 'Failed to get the menu')

        for to_check in [name, category, item, price, description, file_id]:
            self.assert_in(str(to_check), fetched_menu['markdown'], 'Failed to get the menu')

        extracted_from_pdf = self.extract_text(self.cm.render_menu(new_sess, fetched_menu.get('id')))
        for to_check in [name, category, item, price, description]:
            self.assert_in(str(to_check).encode(), extracted_from_pdf, 'Failed to render the menu')

        self.cquit(Status.OK)

    def put(self, flag_id: str, flag: str, vuln: str):
        sess = get_initialized_session()
        u = rnd_username(10)
        p = rnd_password(10)

        self.cm.register(sess, u, p)
        self.cm.login(sess, u, p, status=status.Status.MUMBLE)

        name = self.random_rest_name()
        menu = self.cm.create_menu(sess, name)

        menu_id = menu.get('id')
        self.validate_mid(menu_id)

        menu['categories'] = [
            {'name': self.random_rest_category(), 'items': [
                {'name': self.random_item_name(), 'price': random.randint(1, 10) * 1337, 'description': flag,
                 },
            ]}
        ]
        self.cm.update_menu(sess, menu)

        self.cquit(Status.OK, menu_id, f"{u}:{p}:{menu_id}")

    def get(self, flag_id: str, flag: str, vuln: str):
        s = get_initialized_session()
        username, password, menu_id = flag_id.split(':')

        self.cm.login(s, username, password, status=status.Status.CORRUPT)

        menu = self.cm.get_menu(s, menu_id)
        cat = menu.get('categories')[0] if len(menu.get('categories')) > 0 else {}
        it = cat.get('items')[0] if len(cat.get('items')) > 0 else {}

        self.assert_eq(flag, it.get('description'), 'Failed to get the user menu', status=status.Status.CORRUPT)

        extracted_from_pdf = self.extract_text(self.cm.render_menu(s, menu_id))

        self.assert_in(flag.encode(), extracted_from_pdf, 'Failed to render the user menu',
                       status=status.Status.CORRUPT)

        self.cquit(Status.OK)


if __name__ == '__main__':
    c = Checker(sys.argv[2])

    try:
        c.action(sys.argv[1], *sys.argv[3:])
    except c.get_check_finished_exception():
        cquit(Status(c.status), c.public, c.private)
