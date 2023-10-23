package types

import (
	"log"

	"github.com/go-playground/validator/v10"
)

func Validate(payload interface{}) error {
	validate := validator.New()

	err := validate.RegisterValidation("password", func(fl validator.FieldLevel) bool {
		l := len(fl.Field().String())

		return l >= 8 && l < 60
	})
	if err != nil {
		log.Fatal(err)
	}

	err = validate.Struct(payload)
	if err != nil {
		return err
	}

	return nil
}
