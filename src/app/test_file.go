package app

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/jinzhu/gorm"
	"myFirstGoProject/src/app/apptest"
	"myFirstGoProject/src/structs"
	"net/http"
)

func TestByFile(c *gin.Context) {
	//获取id和deb文件
	id := c.PostForm("id")
	file, err := c.FormFile("debFile")
	if err != nil {
		fmt.Println("[ERROR]", err.Error())
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":  "ERROR",
			"message": err.Error(),
		})
		return
	}
	//连接数据库
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
	taskToCheckId := structs.Task{}
	resultCheckId := db.First(&taskToCheckId, id)
	if resultCheckId.RowsAffected != 0 {
		fmt.Println("[ERROR] ID already exists")
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":  "ERROR",
			"message": "ID already exists",
		})
		return
	}

	//修改文件名并保存
	fileDst := fmt.Sprintf("./apptest/%s.deb", id)
	err = c.SaveUploadedFile(file, fileDst)
	if err != nil {
		fmt.Println("[ERROR]", err.Error())
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":  "ERROR",
			"message": err.Error(),
		})
		return
	}

	go func(id string) {
		db.AutoMigrate(&structs.Task{})
		task := structs.Task{ID: id, Status: "Running"}
		db.Create(&task)
		defer db.Close()
		//执行测试
		score, err := apptest.AppTest(id, id+".deb")
		if err != nil {
			fmt.Println("ERROR", err.Error())
			db.Model(&task).Update("Status", "Error")
			db.Model(&task).Update("Error", err.Error())
			return
		}
		info := "DON'T PASS"
		//判断是否通过
		if score >= 70 {
			info = "PASS"
		}
		db.Model(&task).Update("Status", "Finished")
		db.Model(&task).Update("Score", score)
		db.Model(&task).Update("Info", info)
		db.Model(&task).Update("ResultFile", id+".csv")
	}(id)

	c.JSON(http.StatusOK, gin.H{
		"status":  "OK",
		"message": "Test submitted",
	})
}
