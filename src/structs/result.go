package structs

type ResultReturned struct {
	Status string `json:"status"`
	Data   Data   `json:"data"`
}

type Data struct {
	Score int    `json:"score"`
	Info  string `json:"info"`
	Id    string `json:"id"`
}

type Task struct {
	ID         string
	Status     string
	Score      uint
	Info       string
	ResultFile string
	Error      string
}
