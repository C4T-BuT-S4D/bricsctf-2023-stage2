package db

import (
	"log"

	"leakless/internal/models"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

var DB *gorm.DB

// connectDb
func InitDB() {
	dsn := "host=postgres user=leakless password=leakless dbname=leakless port=5432 sslmode=disable"

	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
		Logger: logger.Default.LogMode(logger.Info),
	})

	if err != nil {
		log.Fatal("Failed to connect to database. \n", err)
	}

	log.Println("connected to database")
	db.Logger = logger.Default.LogMode(logger.Info)

	log.Println("running migrations")
	err = db.AutoMigrate(&models.Company{}, &models.Document{}, &models.Secret{})
	if err != nil {
		log.Fatal(err)
	}

	DB = db
}
