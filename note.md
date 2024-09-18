# 这里记录一些开发中遇到的问题和解决方案
## 1. Python中使用subprocess.Popen执行shell命令

```python
p = subprocess.Popen(
    "echo " + passwd + "|sudo -S dpkg -i " + self.deb,
    shell=True,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)
```

这里如果shell=True，那么命令会被解释为一个字符串，然后传递给shell执行。
如果shell=False，那么命令会被解释为一个列表，列表的第一个元素是命令，后面的元素是参数。
并且如果不特别支出或者shell=False，那么命令中的管道、重定向、通配符等shell特性是不会被解释的。

同时，这里的stdout和stderr是用来重定向标准输出和标准错误的。
在开发过程中发现有时候如果将其重定向到`subprocess.PIPE`，那么会导致程序卡住，原因是子进程的输出缓冲区满了，导致程序阻塞。
因此如果不需要输出，可以将其重定向到`subprocess.DEVNULL`。


## 2. Golang中使用exec.Command和command.CombinedOutput执行shell命令

```go
cmd := exec.Command("python3", "./app_test.py", "-f", fileDst)
out, err := cmd.CombinedOutput()
```

这里和上面说的Python中shell设置为False的情况类似。
如果不特别指出，那么命令会被解释为一个列表，列表的第一个元素是命令，后面的元素是参数。
因此像这个例子中，如果按照下面的方式自己将命令拼接成一个完整的字符串提供给Command函数从而给cmd赋值：

```go
cmd := exec.Command("python3 "+"./app_test.py "+"-f "+fileDst)
```

那么会报错（代码本身不会报错，但是命令无法执行），因为这样传递的是一个字符串，而不是一个列表。

## 3. Golang程序运行目录问题

一般来说，Golang程序运行时的目录是程序所在的目录。
但是如果使用了`go run`命令，那么程序运行时的目录是当前终端所在的目录。
如果是用Goland新建的项目，那么程序运行时的目录是项目的根目录。
如果在程序中想要临时更改工作目录，比如这个项目中对软件进行测试的整个过程都是在apptest目录下进行的，
那么可以使用`os.Chdir`函数来更改工作目录。

```go
oldDir, _ := os.Getwd()
_ = os.Chdir("./apptest")
defer os.Chdir(oldDir)
```

但是不要忘记在函数结束时将工作目录改回来，否则会影响到其他函数的执行。
这里为了避免遗忘，可以在更改工作目录之后使用`defer`关键字来延迟执行恢复工作目录的操作。