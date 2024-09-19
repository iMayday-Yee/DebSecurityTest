package main

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"os/exec"
)

func cleanCache(c *gin.Context) {
	cmd := exec.Command("sh", "-c", "rm -rf ./apptest/results/*")
	_, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Println("[ERROR]", err.Error())
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":  "ERROR",
			"message": err.Error(),
		})
		return
	}
	c.JSON(http.StatusOK, gin.H{
		"status":  "OK",
		"message": "Cache cleaned",
	})
}
