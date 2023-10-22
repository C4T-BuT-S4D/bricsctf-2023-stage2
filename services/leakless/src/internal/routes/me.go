package routes

import (
	"errors"
	"leakless/internal/db"
	"leakless/internal/models"
	"leakless/internal/types"
	"leakless/internal/util"
	"strconv"

	"github.com/gofiber/fiber/v2"
	"gorm.io/gorm"
)

func GetSelfCompany(c *fiber.Ctx) error {
	company, ok := c.Locals("company").(models.Company)
	if !ok {
		return errors.New("invalid jwt")
	}

	if err := db.DB.Model(&company).Association("Secrets").Find(&company.Secrets); err != nil {
		return err
	}

	if err := db.DB.Model(&company).Association("Documents").Find(&company.Documents); err != nil {
		return err
	}

	secrets := make([]types.Secret, len(company.Secrets))
	for i, s := range company.Secrets {
		secrets[i] = types.Secret{
			Secret: s.Secret,
			ID:     s.ID,
		}
	}

	return util.Success(c, fiber.StatusOK, types.GetSelfCompanyResponse{
		ID:          company.ID,
		Login:       company.Login,
		Name:        company.Name,
		Secrets:     secrets,
		DocumentIDs: util.GetCompanyDocumentIDs(&company),
	})
}

func EditCompany(c *fiber.Ctx) error {
	company, ok := c.Locals("company").(models.Company)
	if !ok {
		return errors.New("invalid jwt")
	}

	var body types.EditCompanyForm
	if err := util.ParseBodyAndValidate(c, &body); err != nil {
		return util.Fail(c, fiber.StatusBadRequest, "invalid body")
	}

	company.Name = body.Name

	if q := db.DB.Save(&company); q.Error != nil {
		return q.Error
	}

	return util.Success(c, fiber.StatusOK, "ok")
}

func GetSecret(c *fiber.Ctx) error {
	company, ok := c.Locals("company").(models.Company)
	if !ok {
		return errors.New("invalid jwt")
	}

	secretIDStr := c.Params("secret_id")
	secretID, err := strconv.Atoi(secretIDStr)
	if err != nil {
		return util.Fail(c, fiber.StatusBadRequest, "invalid secret_id")
	}

	var secret models.Secret
	q := db.DB.Take(&secret, "id = ?", secretID)
	if q.Error != nil && !errors.Is(q.Error, gorm.ErrRecordNotFound) {
		return q.Error
	}
	if errors.Is(q.Error, gorm.ErrRecordNotFound) {
		return util.Fail(c, fiber.StatusNotFound, "secret not found")
	}

	if secret.CompanyID != company.ID {
		return util.Fail(c, fiber.StatusUnauthorized, "you do not have permission to access this secret")
	}

	return util.Success(c, fiber.StatusOK, &types.GetSecretResponse{
		Secret: secret.Secret,
	})
}

func PutSecret(c *fiber.Ctx) error {
	company, ok := c.Locals("company").(models.Company)
	if !ok {
		return errors.New("invalid jwt")
	}

	var body types.PutSecretForm
	if err := util.ParseBodyAndValidate(c, &body); err != nil {
		return util.Fail(c, fiber.StatusBadRequest, "invalid body")
	}

	secret := models.Secret{
		Secret:    body.Secret,
		CompanyID: company.ID,
	}

	if q := db.DB.Save(&secret); q.Error != nil {
		return q.Error
	}

	return util.Success(c, fiber.StatusOK, &types.PutSecretResponse{
		ID: secret.ID,
	})
}

func DeleteSecret(c *fiber.Ctx) error {
	company, ok := c.Locals("company").(models.Company)
	if !ok {
		return errors.New("invalid jwt")
	}

	secretIDStr := c.Params("secret_id")
	secretID, err := strconv.Atoi(secretIDStr)
	if err != nil {
		return util.Fail(c, fiber.StatusBadRequest, "invalid secret_id")
	}

	var secret models.Secret
	q := db.DB.Find(&secret, "id = ?", secretID)
	if q.Error != nil && !errors.Is(q.Error, gorm.ErrRecordNotFound) {
		return q.Error
	}
	if errors.Is(q.Error, gorm.ErrRecordNotFound) {
		return util.Fail(c, fiber.StatusNotFound, "secret not found")
	}

	if secret.CompanyID != company.ID {
		return util.Fail(c, fiber.StatusUnauthorized, "you do not have permission to access this secret")
	}

	db.DB.Delete(&secret)

	return util.Success(c, fiber.StatusOK, "ok")
}
