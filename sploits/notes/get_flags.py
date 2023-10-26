import os

for filename in os.listdir('./storage'):
    with open('./storage/'+filename, 'rb') as f:
        x = int.from_bytes(f.read(4), 'little')
        f.read(x)
        note_len = int.from_bytes(f.read(4), 'little')
        if note_len == 0: continue
        s = f.read(note_len)
        key_len = int.from_bytes(f.read(4), 'little')
        k = f.read(key_len)
        n = bytes([x ^ y for x, y in zip(s, k)])
        print(n)
