package main

import (
	"github.com/gin-gonic/gin"
)

func main() {
	r := gin.Default()
	r.POST("/appTestByUrl", appTestByUrl)
	r.POST("/appTestByFile", appTestByFile)
	r.GET("/appTestResult", appTestResult)
	r.GET("/cleanCache", cleanCache)
	_ = r.Run()
}
