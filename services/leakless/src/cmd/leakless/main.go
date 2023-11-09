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

	api := app.Group("api")

	api.Post("/register", routes.Register)
	api.Post("/login", routes.Login)

	api.Get("/me", middleware.Auth, routes.GetSelfCompany)
	api.Post("/me/edit", middleware.Auth, routes.EditCompany)
	api.Get("/me/secret/:secret_id", middleware.Auth, routes.GetSecret)
	api.Put("/me/secret", middleware.Auth, routes.PutSecret)
	api.Delete("/me/secret/:secret_id", middleware.Auth, routes.DeleteSecret)

	api.Get("/company/:company_id", routes.GetCompany)
	api.Post("/query_company", routes.QueryCompany)
	api.Get("/companies", routes.GetCompanies)
	api.Get("/company/:company_id/hashes", routes.GetHashes)
	api.Put("/company/:company_id/doc", routes.PutDoc)

	api.Get("/doc/:document_id", middleware.Auth, routes.GetDocument)
	api.Get("/doc/:document_id/sanitized", routes.GetSanitizedDocument)

	api.Use(func(c *fiber.Ctx) error {
		return util.Fail(c, fiber.StatusNotFound, "not found")
	})


	app.Static("/css", "front/css")
	app.Static("/js", "front/js")

	app.Get("/favicon.ico", func (ctx *fiber.Ctx) error {
		return ctx.SendFile("front/favicon.ico")
	})
	app.Get("/*", func (ctx *fiber.Ctx) error {
		return ctx.SendFile("front/index.html")
	})

	// app.Use(filesystem.New(filesystem.Config{
	// 	Root:         http.Dir("/front"),
	// 	Browse:       false,
	// 	Index:        "index.html",
	// 	NotFoundFile: "404.html",
	// 	MaxAge:       3600,
	// }))

	log.Fatal(app.Listen(":2112"))
}
