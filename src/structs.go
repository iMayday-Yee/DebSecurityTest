package main

type testResult struct {
	Status string `json:"status"`
	Data   data   `json:"data"`
}

type data struct {
	Score int    `json:"score"`
	Info  string `json:"info"`
	Id    string `json:"id"`
}
