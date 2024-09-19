package main

import (
	"github.com/gin-gonic/gin"
	"net/http"
	"os"
)

func appTestResult(c *gin.Context) {
	id := c.Query("id")
	//判断文件是否存在
	_, err := os.Stat("./apptest/results/" + id + ".csv")
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"status":  "ERROR",
			"message": "File not found",
		})
		return
	}
	c.File("./apptest/results/" + id + ".csv")
}
