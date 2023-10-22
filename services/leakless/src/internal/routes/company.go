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

func GetCompany(c *fiber.Ctx) error {
	companyIDStr := c.Params("company_id")

	companyID, err := strconv.Atoi(companyIDStr)

	if err != nil {
		return util.Fail(c, fiber.StatusBadRequest, "invalid company_id")
	}

	var company models.Company

	q := db.DB.Preload("Documents").Take(&company, "id = ?", companyID)
	if q.Error != nil && !errors.Is(q.Error, gorm.ErrRecordNotFound) {
		return q.Error
	}
	if errors.Is(q.Error, gorm.ErrRecordNotFound) {
		return util.Fail(c, fiber.StatusNotFound, "company not found")
	}

	return util.Success(c, fiber.StatusOK, types.GetCompanyResponse{
		ID:          company.ID,
		Login:       company.Login,
		Name:        company.Name,
		DocumentIDs: util.GetCompanyDocumentIDs(&company),
	})
}

func QueryCompany(c *fiber.Ctx) error {
	var body types.QuearyCompanyForm

	if err := util.ParseBodyAndValidate(c, &body); err != nil {
		return util.Fail(c, fiber.StatusBadRequest, err.Error())
	}

	var query []interface{}
	if body.Login != nil {
		query = append(query, "login = ?")
		query = append(query, body.Login)
	}

	if body.Name != nil {
		query = append(query, "name = ?")
		query = append(query, body.Name)
	}

	if len(query) != 2 {
		return util.Fail(c, fiber.StatusBadRequest, "must provide either name or login")
	}

	var company models.Company
	q := db.DB.Preload("Documents").Find(&company, query[0], query[0])
	if q.Error != nil && !errors.Is(q.Error, gorm.ErrRecordNotFound) {
		return q.Error
	}
	if errors.Is(q.Error, gorm.ErrRecordNotFound) {
		return util.Fail(c, fiber.StatusNotFound, "company not found")
	}

	return util.Success(c, fiber.StatusOK, types.GetCompanyResponse{
		Login:       company.Login,
		Name:        company.Name,
		DocumentIDs: util.GetCompanyDocumentIDs(&company),
	})
}

func GetCompanies(c *fiber.Ctx) error {
	offsetStr := c.Query("offset")
	offset, err := strconv.Atoi(offsetStr)
	if err != nil {
		return util.Fail(c, fiber.StatusBadRequest, "invalid offset")
	}

	limitStr := c.Query("limit")
	limit, err := strconv.Atoi(limitStr)
	if err != nil {
		return util.Fail(c, fiber.StatusBadRequest, "invalid limit")
	}

	var companies []models.Company
	if q := db.DB.Limit(limit).Offset(offset).Order("ID").Find(&companies); q.Error != nil {
		return q.Error
	}

	var response types.GetCompaniesResponse

	for _, company := range companies {
		response.Companies = append(response.Companies, types.GetCompanyResponse{
			Login:       company.Login,
			Name:        company.Name,
			DocumentIDs: util.GetCompanyDocumentIDs(&company),
		})
	}

	return util.Success(c, fiber.StatusOK, response)
}

func GetHashes(c *fiber.Ctx) error {
	companyIDStr := c.Params("company_id")
	companyID, err := strconv.Atoi(companyIDStr)
	if err != nil {
		return util.Fail(c, fiber.StatusBadRequest, "invalid company_id")
	}

	var company models.Company

	q := db.DB.Preload("Secrets").Take(&company, "id = ?", companyID)
	if q.Error != nil && !errors.Is(q.Error, gorm.ErrRecordNotFound) {
		return q.Error
	}
	if errors.Is(q.Error, gorm.ErrRecordNotFound) {
		return util.Fail(c, fiber.StatusNotFound, "company not found")
	}

	sh := hash.GenHashes(util.GetCompanySecrets(&company))
	return util.Success(c, fiber.StatusOK, types.HashesResponse{
		P:      sh.P,
		Q:      sh.Q,
		Hashes: util.GetRawHashes(sh),
	})
}

func PutDoc(c *fiber.Ctx) error {
	companyIDStr := c.Params("company_id")
	companyID, err := strconv.Atoi(companyIDStr)
	if err != nil {
		return util.Fail(c, fiber.StatusBadRequest, "invalid company_id")
	}

	var body types.PutDocForm
	if err := util.ParseBodyAndValidate(c, &body); err != nil {
		return util.Fail(c, fiber.StatusBadRequest, err.Error())
	}

	var company models.Company
	q := db.DB.Find(&company, "id = ?", companyID)
	if q.Error != nil && !errors.Is(q.Error, gorm.ErrRecordNotFound) {
		return q.Error
	}
	if errors.Is(q.Error, gorm.ErrRecordNotFound) {
		return util.Fail(c, fiber.StatusNotFound, "company not found")
	}

	document := models.Document{
		Text:      body.Text,
		CompanyID: company.ID,
	}

	if q := db.DB.Save(&document); q.Error != nil {
		return q.Error
	}

	return util.Success(c, fiber.StatusOK, &types.PutDocumentResponse{
		ID: document.ID,
	})
}
