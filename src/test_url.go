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
	var result = testResult{0, "DON'T PASS"}
	oldDir, err := os.Getwd()
	if err != nil {
		fmt.Println("[ERROR]", err.Error())
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":  "ERROR",
			"message": err.Error(),
		})
		return
	}
	if strings.Contains(oldDir, "apptest") == false {
		err = os.Chdir("./apptest")
		if err != nil {
			fmt.Println("[ERROR]", err.Error())
			c.JSON(http.StatusInternalServerError, gin.H{
				"status":  "ERROR",
				"message": err.Error(),
			})
			return
		}
	}
	//切换完成后再切换回来
	defer os.Chdir(oldDir)
	//获取id和deb文件
	debUrl := c.PostForm("debUrl")
	id := c.PostForm("id")
	//下载deb文件
	cmd := exec.Command("wget", debUrl)
	_, err = cmd.CombinedOutput()
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
	err = os.Rename(debName, id+".deb")
	if err != nil {
		fmt.Println("ERROR", err.Error())
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":  "ERROR",
			"message": err.Error(),
		})
		return
	}
	//执行测试
	result.Score, err = appTest(id, id+".deb")
	if err != nil {
		fmt.Println("ERROR", err.Error())
		c.JSON(http.StatusInternalServerError, gin.H{
			"status":  "ERROR",
			"message": err.Error(),
		})
		return
	}
	//判断是否通过
	if result.Score >= 70 {
		result.Info = "PASS"
	}
	//返回结果
	c.JSON(http.StatusOK, result)
}
