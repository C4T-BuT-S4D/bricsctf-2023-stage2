package types

type Secret struct {
	Secret string `json:"secret"`
	ID     uint   `json:"id"`
}

type GetCompanyResponse struct {
	ID          uint   `json:"id"`
	Login       string `json:"login" validate:"required"`
	Name        string `json:"name" validate:"required,min=3"`
	DocumentIDs []uint `json:"documents"`
}

type QuearyCompanyForm struct {
	Login *string `json:"login"`
	Name  *string `json:"name"`
}

type PutDocForm struct {
	Text string `json:"text" validate:"required"`
}

type GetCompaniesResponse struct {
	Companies []GetCompanyResponse `json:"companies"`
}

type PutDocumentResponse struct {
	ID uint `json:"id"`
}

type HashesResponse struct {
	P      uint64   `json:"p"`
	Q      uint64   `json:"q"`
	Hashes []uint64 `json:"hashes"`
}
