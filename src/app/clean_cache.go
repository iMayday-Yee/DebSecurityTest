package app

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/jinzhu/gorm"
	"myFirstGoProject/src/structs"
	"net/http"
	"os/exec"
	"strings"
)

func CleanCache(c *gin.Context) {
	cmd := exec.Command("sh", "-c", "rm -rf ./apptest/results/*")
	output, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Println("[ERROR]", string(output))
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":  "ERROR",
			"message": string(output),
		})
		return
	}
	db, err := gorm.Open("mysql", "root:Yyy12345@(127.0.0.1:3306)/apptest?charset=utf8mb4&parseTime=True&loc=Local")
	if err != nil {
		fmt.Println("[ERROR]", err.Error())
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":  "ERROR",
			"message": err.Error(),
		})
		return
	}
	defer db.Close()
	db.AutoMigrate(&structs.Task{})
	db.Delete(structs.Task{})
	c.JSON(http.StatusOK, gin.H{
		"status":  "OK",
		"message": "Cache cleaned",
	})
}

func DiskUsage(c *gin.Context) {
	cmd := exec.Command("du", "-hd", "0", "./apptest/results")
	output, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Println("[ERROR]", string(output))
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":  "ERROR",
			"message": string(output),
		})
		return
	}
	diskUsage := strings.Split(string(output), "\t")[0]
	c.JSON(http.StatusOK, gin.H{
		"status":    "OK",
		"diskUsage": diskUsage,
	})
}
