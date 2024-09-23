package app

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"myFirstGoProject/src/app/apptest"
	"myFirstGoProject/src/structs"
	"net/http"
)

func TestByFile(c *gin.Context) {
	//切换到apptest目录
	var result = structs.ResultReturned{Status: "ERROR", Data: structs.Data{Score: 0, Info: "DON'T PASS", Id: "0000"}}
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
	//执行测试
	result.Data.Score, err = apptest.AppTest(id, id+".deb")
	if err != nil {
		fmt.Println("[ERROR]", err.Error())
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":  "ERROR",
			"message": err.Error(),
		})
		return
	}
	result.Data.Id = id
	//判断是否通过
	if result.Data.Score >= 70 {
		result.Data.Info = "PASS"
	}
	result.Status = "OK"
	//返回结果
	c.JSON(http.StatusOK, result)
}
