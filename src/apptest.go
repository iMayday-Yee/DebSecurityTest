package main

import (
	"fmt"
	"os"
	"os/exec"
	"strconv"
	"strings"
)

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
