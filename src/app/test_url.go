package app

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"github.com/jinzhu/gorm"
	_ "github.com/jinzhu/gorm/dialects/mysql"
	"myFirstGoProject/src/app/apptest"
	"myFirstGoProject/src/structs"
	"net/http"
	"os"
	"os/exec"
	"strings"
)

func TestByUrl(c *gin.Context) {
	//获取id和deb文件
	debUrl := c.PostForm("debUrl")
	id := c.PostForm("id")
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
	//创建任务
	go func(debUrl string, id string) {
		db.AutoMigrate(&structs.Task{})
		task := structs.Task{ID: id, Status: "RUNNING"}
		db.Create(&task)
		defer db.Close()
		//下载deb文件
		cmd := exec.Command("wget", debUrl)
		cmd.Dir = "./apptest"
		_, err = cmd.CombinedOutput()
		if err != nil {
			fmt.Println("ERROR", err.Error())
			db.Model(&task).Update("Status", "ERROR")
			db.Model(&task).Update("Error", err.Error())
			return
		}
		//修改文件名为id.deb
		debName := debUrl[strings.LastIndex(debUrl, "/")+1:]
		err = os.Rename("apptest/"+debName, "apptest/"+id+".deb")
		if err != nil {
			fmt.Println("ERROR", err.Error())
			db.Model(&task).Update("Status", "ERROR")
			db.Model(&task).Update("Error", err.Error())
			return
		}
		//执行测试
		score, err := apptest.AppTest(id, id+".deb")
		if err != nil {
			fmt.Println("ERROR", err.Error())
			db.Model(&task).Update("Status", "ERROR")
			db.Model(&task).Update("Error", err.Error())
			return
		}
		info := "DON'T PASS"
		//判断是否通过
		if score >= 70 {
			info = "PASS"
		}
		db.Model(&task).Update("Status", "FINISHED")
		db.Model(&task).Update("Score", score)
		db.Model(&task).Update("Info", info)
		db.Model(&task).Update("ResultFile", id+".deb")
	}(debUrl, id)

	c.JSON(http.StatusOK, gin.H{
		"status":  "OK",
		"message": "Test submitted",
	})
}
