package routes

import (
	"errors"

	"github.com/gofiber/fiber/v2"
	"gorm.io/gorm"

	"leakless/internal/db"
	"leakless/internal/jwt"
	"leakless/internal/models"
	"leakless/internal/types"
	"leakless/internal/util"
)

func Register(c *fiber.Ctx) error {
	var body types.RegisterForm

	if err := util.ParseBodyAndValidate(c, &body); err != nil {
		return err
	}

	company := models.Company{
		Name:     body.Name,
		Login:    body.Login,
		Password: body.Password,
	}

	if q := db.DB.Create(&company); q.Error != nil {
		return q.Error
	}

	jwt, err := jwt.Generate(company.ID)

	if err != nil {
		return err
	}

	return util.Success(c, fiber.StatusOK, &types.JwtResponse{
		Jwt: *jwt,
	})
}

func Login(c *fiber.Ctx) error {
	var body types.LoginForm

	if err := util.ParseBodyAndValidate(c, &body); err != nil {
		return util.Fail(c, fiber.StatusBadRequest, err.Error())
	}

	var company models.Company

	q := db.DB.Take(&company, "login = ?", body.Login)
	if q.Error != nil && !errors.Is(q.Error, gorm.ErrRecordNotFound) {
		return q.Error
	}
	if errors.Is(q.Error, gorm.ErrRecordNotFound) || company.Password != body.Password {
		return util.Fail(c, fiber.StatusNotFound, "login or password incorrect")
	}

	jwt, err := jwt.Generate(company.ID)

	if err != nil {
		return err
	}

	return util.Success(c, fiber.StatusOK, &types.JwtResponse{
		Jwt: *jwt,
	})
}
