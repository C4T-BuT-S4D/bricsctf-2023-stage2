package models

import "gorm.io/gorm"

type Company struct {
	gorm.Model

	Name     string `gorm:"uniqueIndex"`
	Login    string `gorm:"uniqueIndex"`
	Password []byte

	Secrets   []Secret   `gorm:"foreignKey:CompanyID"`
	Documents []Document `gorm:"foreignKey:CompanyID"`
}

type Secret struct {
	gorm.Model

	CompanyID uint
	Secret    string
}

type Document struct {
	gorm.Model

	CompanyID uint
	Text      string
}
