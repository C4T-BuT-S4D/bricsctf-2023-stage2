package util

import (
	"leakless/internal/hash"
	"leakless/internal/models"
	"leakless/internal/types"

	"github.com/gofiber/fiber/v2"
)

func ParseBodyAndValidate(c *fiber.Ctx, body interface{}) error {
	if err := c.BodyParser(body); err != nil {
		return fiber.ErrBadRequest
	}

	return types.Validate(body)
}

func GetCompanySecrets(company *models.Company) []string {
	secrets := make([]string, len(company.Secrets))

	for i, s := range company.Secrets {
		secrets[i] = s.Secret
	}

	return secrets
}

func GetCompanyDocumentIDs(company *models.Company) []uint {
	documentIDs := make([]uint, len(company.Documents))
	for i, d := range company.Documents {
		documentIDs[i] = d.ID
	}

	return documentIDs
}

func GetRawHashes(sh *hash.SecretHashes) []uint64 {
	hashes := make([]uint64, len(sh.Hashes))
	for i, h := range sh.Hashes {
		hashes[i] = h.Hash
	}

	return hashes
}

func Fail(c *fiber.Ctx, code int, message interface{}) error {
	return c.Status(code).JSON(&types.Status{
		Code:    code,
		Status:  "error",
		Message: message,
	})
}

func Success(c *fiber.Ctx, code int, message interface{}) error {
	return c.Status(code).JSON(&types.Status{
		Code:    code,
		Status:  "success",
		Message: message,
	})
}

func ErrorHandler(c *fiber.Ctx, err error) error {
	return Fail(c, fiber.StatusInternalServerError, err.Error())
}
