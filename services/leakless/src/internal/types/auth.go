package types

type LoginForm struct {
	Login    string `json:"login" validate:"required"`
	Password string `json:"password" validate:"required,password"`
}

type RegisterForm struct {
	LoginForm
	Name string `json:"name" validate:"required,min=3"`
}

type JwtResponse struct {
	Jwt string `json:"jwt"`
}
