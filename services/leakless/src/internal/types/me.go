package types

type EditCompanyForm struct {
	Name string `json:"name" validate:"required"`
}

type PutSecretForm struct {
	Secret string `json:"secret"`
}

type GetSelfCompanyResponse struct {
	ID          uint     `json:"id"`
	Login       string   `json:"login"`
	Name        string   `json:"name"`
	Secrets     []Secret `json:"secrets"`
	DocumentIDs []uint   `json:"documents"`
}

type GetSecretResponse struct {
	Secret string `json:"secret"`
}

type PutSecretResponse struct {
	ID uint `json:"id"`
}
