package main

import (
	"github.com/gin-gonic/gin"
	"myFirstGoProject/src/app"
	"net/http"
)

func CORSMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Credentials", "true")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, Content-Length, Authorization")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS, GET, PUT")
		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(http.StatusNoContent)
			return
		}
		c.Next()
	}
}

func main() {
	r := gin.Default()
	r.Use(CORSMiddleware())
	r.POST("/appTestByUrl", app.TestByUrl)
	r.POST("/appTestByFile", app.TestByFile)
	r.GET("/appTestResult", app.TestResult)
	r.GET("/cleanCache", app.CleanCache)
	r.GET("/diskUsage", app.DiskUsage)
	r.GET("/showTasks", app.ShowTasks)
	_ = r.Run(":12345")
}
