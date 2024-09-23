package app

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/jinzhu/gorm"
	_ "github.com/jinzhu/gorm/dialects/mysql"
	"myFirstGoProject/src/structs"
	"net/http"
)

func ShowTasks(c *gin.Context) {
	db, err := gorm.Open("mysql", "root:Yyy12345@(127.0.0.1:3306)/apptest?charset=utf8mb4&parseTime=True&loc=Local")
	if err != nil {
		fmt.Println("[ERROR]", err.Error())
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":  "ERROR",
			"message": err.Error(),
		})
		return
	}
	db.AutoMigrate(&structs.Task{})
	//查询所有任务并以json格式返回
	var tasks []structs.Task
	db.Find(&tasks)
	c.JSON(http.StatusOK, tasks)
	defer db.Close()
}
