# leakless

leakless was the simplest service this ctf, it allowed:

- register a company
- add secrets for a company
- publish a document for a company
- the secrets in that document would then be sensored or the document could be viewed in full by the company
- get polynomial hashes of all secrets of a company

## Exploit

A polynomial hash is a hash where `h(s) = q ** 0 * s[-1] + q ** 1 * s[-2] + q ** 2 * s[-3] + ... (mod p)` (where `s[-i]` means `i-1`th last element). In the service the parameter `q` was not randomized, but `p` was, meaning the values under the modulus were the same, so there if we got enought hashes we had a system of equations form `poly = h_i (mod p_i)`, which we could solve using CRT to obtain `poly (mod p)` and from there simply compute remainders modulo `q` to get the flag. Later on participants figured out how to use LLL to find the secret even when both parametrs were randomized.
