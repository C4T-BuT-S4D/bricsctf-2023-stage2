package jwt

import (
	"crypto/rand"
	"errors"
	"fmt"
	"log"
	"strconv"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

var jwtKey []byte

func InitJWT() {
	var randBytes [32]byte

	_, err := rand.Read(randBytes[:])

	if err != nil {
		log.Fatal(err)
	}

	jwtKey = randBytes[:]
}

func Generate(id uint) (*string, error) {
	t := jwt.NewWithClaims(jwt.SigningMethodHS256, jwt.MapClaims{
		"exp": time.Now().Add(time.Minute * 10).Unix(),
		"ID":  strconv.FormatUint(uint64(id), 10),
	})

	token, err := t.SignedString(jwtKey)

	if err != nil {
		return nil, err
	}

	return &token, nil
}

func Verify(token string) (*uint, error) {
	parsed, err := jwt.Parse(token, func(t *jwt.Token) (interface{}, error) {
		if _, ok := t.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", t.Header["alg"])
		}

		return jwtKey, nil
	})

	if err != nil {
		return nil, err
	}

	claims, ok := parsed.Claims.(jwt.MapClaims)
	if !ok {
		return nil, errors.New("jwt error")
	}

	idStr, ok := claims["ID"].(string)
	if !ok {
		return nil, errors.New("jwt error")
	}

	signedID, err := strconv.Atoi(idStr)
	if err != nil {
		return nil, err
	}

	id := uint(signedID)

	return &id, nil
}
