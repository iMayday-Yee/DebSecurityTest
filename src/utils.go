package main

import (
	"fmt"
	"github.com/gin-gonic/gin"
	"net/http"
	"os"
	"os/exec"
	"strconv"
	"strings"
)

type testResult struct {
	Score int    `json:"score"`
	Info  string `json:"info"`
}

func appTest(id string, fileDst string) (int, error) {
	//执行测试
	cmd := exec.Command("python3", "./app_test.py", "-f", fileDst)
	output, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Println("[ERROR]", string(output))
		return 0, err
	}
	//移动文件
	_ = os.Rename(fileDst, "./results/"+id+".deb")
	_ = os.Rename("./"+id+".csv", "./results/"+id+".csv")
	//解析结果
	lines := strings.Split(string(output), "\n")
	for _, line := range lines {
		if strings.Contains(line, "当前分数为:") {
			fields := strings.Split(line, ":")
			scoreStr := fields[1]
			score, err := strconv.Atoi(scoreStr) //保存分数到result
			if err != nil {
				return 0, err
			}
			return score, nil
		}
	}
	return 0, nil
}

func appTestByFile(c *gin.Context) {
	//切换到apptest目录
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
	fileDst := fmt.Sprintf("./%s.deb", id)
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
	result.Score, err = appTest(id, fileDst)
	if err != nil {
		fmt.Println("[ERROR]", err.Error())
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

func appTestResult(c *gin.Context) {
	id := c.Query("id")
	c.File("./apptest/results/" + id + ".csv")
}

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
