package main

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"os"
	"os/exec"
	"strings"
)

func appTestByUrl(c *gin.Context) {
	var result = testResult{Status: "ERROR", Data: data{Score: 0, Info: "DON'T PASS", Id: "0000"}}
	//获取id和deb文件
	debUrl := c.PostForm("debUrl")
	id := c.PostForm("id")
	//下载deb文件
	cmd := exec.Command("wget", debUrl)
	cmd.Dir = "./apptest"
	_, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Println("ERROR", err.Error())
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":  "ERROR",
			"message": err.Error(),
		})
		return
	}
	//修改文件名为id.deb
	debName := debUrl[strings.LastIndex(debUrl, "/")+1:]
	err = os.Rename("apptest/"+debName, "apptest/"+id+".deb")
	if err != nil {
		fmt.Println("ERROR", err.Error())
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":  "ERROR",
			"message": err.Error(),
		})
		return
	}
	//执行测试
	result.Data.Score, err = appTest(id, id+".deb")
	if err != nil {
		fmt.Println("ERROR", err.Error())
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
