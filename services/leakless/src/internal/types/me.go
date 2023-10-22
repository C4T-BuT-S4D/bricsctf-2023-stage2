package types

type GetSelfCompanyResponse struct {
	ID          uint     `json:"id"`
	Login       string   `json:"login" validate:"required"`
	Name        string   `json:"name" validate:"required,min=3"`
	Secrets     []Secret `json:"secrets"`
	DocumentIDs []uint   `json:"documents"`
}

type EditCompanyForm struct {
	Name string `json:"name" validate:"required"`
}

type PutSecretForm struct {
	Secret string `json:"secret"`
}

type GetSecretResponse struct {
	Secret string `json:"secret"`
}

type PutSecretResponse struct {
	ID uint `json:"id"`
}
