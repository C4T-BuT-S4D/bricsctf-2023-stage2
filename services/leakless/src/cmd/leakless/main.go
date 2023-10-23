package main

import (
	"log"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"

	"leakless/internal/db"
	"leakless/internal/jwt"
	"leakless/internal/middleware"
	"leakless/internal/routes"
	"leakless/internal/util"
)

func main() {
	db.InitDB()
	jwt.InitJWT()

	app := fiber.New(fiber.Config{
		ErrorHandler: util.ErrorHandler,
	})
	app.Use(cors.New())

	app.Post("/register", routes.Register)
	app.Post("/login", routes.Login)

	app.Get("/me", middleware.Auth, routes.GetSelfCompany)
	app.Get("/me/edit", middleware.Auth, routes.EditCompany)
	app.Get("/me/secret/:secret_id", middleware.Auth, routes.GetSecret)
	app.Put("/me/secret", middleware.Auth, routes.PutSecret)
	app.Delete("/me/secret/:secret_id", middleware.Auth, routes.DeleteSecret)

	app.Get("/company/:company_id", routes.GetCompany)
	app.Post("/query_company", routes.QueryCompany)
	app.Get("/companies", routes.GetCompanies)
	app.Get("/company/:company_id/hashes", routes.GetHashes)
	app.Put("/company/:company_id/doc", routes.PutDoc)

	app.Get("/doc/:document_id", middleware.Auth, routes.GetDocument)
	app.Get("/doc/:document_id/sanitized", routes.GetSanitizedDocument)

	app.Use(func(c *fiber.Ctx) error {
		return c.SendStatus(404)
	})

	log.Fatal(app.Listen(":2112"))
}
