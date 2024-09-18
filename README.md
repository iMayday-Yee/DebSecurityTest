# Python 部分

## Python脚本执行环境和依赖 

1. 安装cppcheck:
```shell
sudo apt install cppcheck
```

2. 安装clamav:
```shell
sudo apt install clamav
```

3. 更新病毒库：
```shell
sudo service clamav-freshclam stop
sudo freshclam
sudo service clamav-freshclam start
```

4. 安装checksec
```shell
sudo apt install checksec
```

5. 安装yara
```shell
sudo apt install yara
```

6. 填写yara规则路径,默认为当前路径下的rules目录

```shell
# yara-rules来源:
# https://github.com/Neo23x0/signature-base/tree/master/yara
# https://github.com/Neo23x0/signature-base/tree/master/yara
```

7. 安装die
```shell
sudo apt install biz.ntinfo.die
```

## Python脚本单独使用方法

安装应用后执行:
```shell
python3 apptest.py -f test.dep -s ./test -c 1.json
# -f 指定测试的deb包。
# -s 指定应用源码目录。
# -c 应用组件json文件,例:{"git":"1:2.20.1-2+deb10u1","curl":"7.64.0-4+deb10u3"}
# -d 批量测试目录
# -p 指定进程pid
```

# Golang 部分

直接在src/目录下运行即可：
```go
go run main.go
```
