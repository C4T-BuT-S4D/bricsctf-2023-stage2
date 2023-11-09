#!/usr/bin/env python3

from typing import Iterable, Tuple, List
from math import gcd

import sys
import requests

PORT = 2112
Q = 31337
FLAG_LENGTH = 32

def chinese_rem_theorem(it: Iterable[Tuple[int, int]]) -> Tuple[int, int]:
    """
    chinese_rem_theorem([(remainder, modulo), ...])
    The resulting remainder and modulo of the Chinese Remainder Theorem for rema, modulo in iterable.
    https://en.wikipedia.org/wiki/Chinese_remainder_theorem
    """
    M = 1
    result = 0
    for r, m in it:
        while gcd(M, m) != 1:
            m = m // gcd(M, m)
        r = r % m
        result = (pow(M, -1, m) * M * r + pow(m, -1, M) * m * result) % (M * m)
        M *= m
    return result, M

def recover_hash_from_remainders(it: Iterable[Tuple[int, int]]):
    h, _ = chinese_rem_theorem(it)
    b = []
    while h != 0:
        b.append(h % Q)
        h //= Q

    return bytes(b[::-1])

def main():
    host = sys.argv[1]
    hint = sys.argv[2]

    url = f"http://{host}:{PORT}/api"

    flag_hashes: List[List[Tuple[int, int]]] = []
    for _ in range((Q ** (FLAG_LENGTH * 2)).bit_length() // 32):
        hashes = requests.get(f"{url}/company/{hint}/hashes").json()["message"]
        for i, hash in enumerate(hashes["hashes"]):
            while len(flag_hashes) <= i:
                flag_hashes.append([])
            flag_hashes[i].append((hash["hash"], hashes["p"]))

    for possible_flag_hash in flag_hashes:
        print(recover_hash_from_remainders(possible_flag_hash), flush=True)

if __name__ == "__main__":
    main()
