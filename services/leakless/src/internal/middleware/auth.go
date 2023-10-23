package middleware

import (
	"errors"
	"leakless/internal/db"
	"leakless/internal/jwt"
	"leakless/internal/models"
	"leakless/internal/util"
	"strings"

	"github.com/gofiber/fiber/v2"
	"gorm.io/gorm"
)

func Auth(c *fiber.Ctx) error {
	h := c.Get("Authorization")

	if h == "" {
		return util.Fail(c, fiber.StatusUnauthorized, "no bearer token provided")
	}

	// Authorization must be of the form "Bearer <jwt>"
	chunks := strings.Split(h, " ")

	if len(chunks) < 2 || chunks[0] != "Bearer" {
		return util.Fail(c, fiber.StatusUnauthorized, "invalid token form")
	}

	companyID, err := jwt.Verify(chunks[1])

	if err != nil {
		return util.Fail(c, fiber.StatusUnauthorized, err.Error())
	}

	var company models.Company

	q := db.DB.Take(&company, "id = ?", companyID)
	if q.Error != nil && !errors.Is(q.Error, gorm.ErrRecordNotFound) {
		return q.Error
	}
	if errors.Is(q.Error, gorm.ErrRecordNotFound) {
		return errors.New("jwt company_id not found")
	}

	c.Locals("company", company)

	return c.Next()
}
