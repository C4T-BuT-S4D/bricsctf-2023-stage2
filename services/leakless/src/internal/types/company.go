package types

type Secret struct {
	Secret string `json:"secret"`
	ID     uint   `json:"id"`
}

type QueryCompanyForm struct {
	Login *string `json:"login"`
	Name  *string `json:"name"`
}

type PutDocForm struct {
	Text string `json:"text" validate:"required"`
}

type GetCompanyResponse struct {
	ID          uint   `json:"id"`
	Login       string `json:"login"`
	Name        string `json:"name"`
	DocumentIDs []uint `json:"documents"`
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
