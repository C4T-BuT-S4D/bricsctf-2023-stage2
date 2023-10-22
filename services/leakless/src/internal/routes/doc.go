package routes

import (
	"github.com/gofiber/fiber/v2"
	"gorm.io/gorm"

	"errors"
	"leakless/internal/db"
	"leakless/internal/hash"
	"leakless/internal/models"
	"leakless/internal/types"
	"leakless/internal/util"
	"strconv"
)

func GetDocument(c *fiber.Ctx) error {
	company, ok := c.Locals("company").(models.Company)

	if !ok {
		return errors.New("invalid jwt")
	}

	documentIDStr := c.Params("document_id")
	documentID, err := strconv.Atoi(documentIDStr)
	if err != nil {
		return util.Fail(c, fiber.StatusBadRequest, "invalid document_id")
	}

	var document models.Document
	q := db.DB.Take(&document, "id = ?", documentID)
	if q.Error != nil && !errors.Is(q.Error, gorm.ErrRecordNotFound) {
		return q.Error
	}
	if errors.Is(q.Error, gorm.ErrRecordNotFound) {
		return util.Fail(c, fiber.StatusNotFound, "document not found")
	}

	if document.CompanyID != company.ID {
		return util.Fail(c, fiber.StatusUnauthorized, "you do not have access to this document")
	}

	return util.Success(c, fiber.StatusOK, types.DocumentResponse{
		Text: document.Text,
	})
}

func GetSanitizedDocument(c *fiber.Ctx) error {
	documentIDStr := c.Params("document_id")
	documentID, err := strconv.Atoi(documentIDStr)
	if err != nil {
		return util.Fail(c, fiber.StatusBadRequest, "invalid document_id")
	}

	var document models.Document
	q := db.DB.Find(&document, "id = ?", documentID)
	if q.Error != nil && !errors.Is(q.Error, gorm.ErrRecordNotFound) {
		return q.Error
	}
	if errors.Is(q.Error, gorm.ErrRecordNotFound) {
		return util.Fail(c, fiber.StatusNotFound, "document not found")
	}

	var company models.Company
	q = db.DB.Preload("Secrets").Take(&company, "id = ?", document.CompanyID)
	if q.Error != nil && !errors.Is(q.Error, gorm.ErrRecordNotFound) {
		return q.Error
	}
	if errors.Is(q.Error, gorm.ErrRecordNotFound) {
		return util.Fail(c, fiber.StatusInternalServerError, "document not found")
	}

	return util.Success(c, fiber.StatusOK, types.DocumentResponse{
		Text: hash.GenHashes(util.GetCompanySecrets(&company)).SanitizeSecrets(document.Text),
	})
}
