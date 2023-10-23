package hash

import (
	"math/rand"
)

const ReplaceChar = '*'

type Hasher struct {
	P uint64 `json:"p"`
	Q uint64 `json:"q"`
}

type SecretHash struct {
	Hash   uint64 `json:"hash"`
	secret string
}

type SecretHashes struct {
	Hasher
	Hashes []SecretHash `json:"hashes"`
}

type Interval struct {
	L int
	R int
}

func (hs *Hasher) hash(secret []byte) uint64 {
	h := uint64(0)
	for _, c := range secret {
		h = (h * hs.Q) % hs.P
		h = (h + uint64(c)) % hs.P
	}
	return h
}

func GenHashes(secrets []string) *SecretHashes {
	sh := &SecretHashes{}

	sh.P = uint64(rand.Uint32())
	sh.Q = 31337

	for _, s := range secrets {
		sh.Hashes = append(sh.Hashes, SecretHash{
			Hash:   sh.hash([]byte(s)),
			secret: s,
		})
	}

	return sh
}

func powmod(base, exp, mod uint64) (res uint64) {
	res = 1
	for exp != 0 {
		if exp%2 == 1 {
			res = (res * base) % mod
		}
		base = (base * base) % mod
		exp /= 2
	}
	return
}

func (sh *SecretHashes) FindSecrets(text string) (secretIntervals []Interval) {
	prefixHashes := make([]uint64, len(text)+1)

	prefixHashes[0] = 0

	h := uint64(0)
	for i, c := range []byte(text) {
		h = (h * sh.Q) % sh.P
		h = (h + uint64(c)) % sh.P
		prefixHashes[i+1] = h
	}

	secretsByLen := make(map[int]map[uint64][]SecretHash)
	for _, s := range sh.Hashes {
		if secretsByLen[len(s.secret)] == nil {
			secretsByLen[len(s.secret)] = make(map[uint64][]SecretHash)
		}

		secretsByLen[len(s.secret)][s.Hash] = append(secretsByLen[len(s.secret)][s.Hash], s)
	}

	for l, secretMap := range secretsByLen {
		for i := 0; i < len(prefixHashes)-l; i++ {
			h := (sh.P + prefixHashes[i+l] - (prefixHashes[i] * powmod(sh.Q, uint64(l), sh.P) % sh.P)) % sh.P

			if secretList, found := secretMap[h]; found {
				for _, s := range secretList {
					if text[i:i+l] == s.secret {
						secretIntervals = append(secretIntervals, Interval{
							L: i,
							R: i + l,
						})
						break
					}
				}
			}
		}
	}

	return
}

func (sh *SecretHashes) SanitizeSecrets(text string) string {
	sanitized := []byte(text)
	for _, interval := range sh.FindSecrets(text) {
		for i := interval.L; i < interval.R; i++ {
			sanitized[i] = ReplaceChar
		}
	}

	return string(sanitized)
}
