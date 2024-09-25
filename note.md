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

更新：要注意下面问题4中多个请求同时到来的情况，因为这里使用的是`os.Chdir`函数并且参数使用的是相对路径，所以如果前一个请求更改了工作目录，
但是还没运行结束所以还没有把工作目录改回来，这时候又有一个请求到来，那么这个请求的工作目录就是前一个请求的工作目录，
即会尝试跳转到`./apptest/apptest/`，这样就会导致错误。可以在运行`os.Chdir`之前先获取当前工作目录，
然后在更改工作目录之前判断当前工作目录是否是预期的工作目录。

更新：上面更新中提到的方法还是会造成很大的影响，因为os.Chdir()是修改了全局的工作目录，由于现在想要将整个检测系统修改为提交任务的模式，
因此一定会出现并发的情况，这个时候如果使用os.Chdir()来修改工作目录，那么会使得整个程序工作目录十分混乱，尤其是之后如果要加入新的功能，
也不能每次都判断现在是否在`apptest/`目录下，因此这里应该避免使用os.Chdir()函数。代替方法是使用cmd.Dir来指定每一条命令的临时工作目录。
代码如下

```go
cmd := exec.Command("python3", "./app_test.py", "-f", fileDst)
cmd.Dir = "./apptest"
output, err := cmd.CombinedOutput()
```

## 4. Gin同时处理多个POST请求

因为本项目中`appTest`函数要执行很长时间，对于多个请求同时到来的情况，我本来是想使用goroutine来处理的。
即在`appTestByFile`和`appTestByUrl`函数调用`appTest`函数时，使用如下命令进行处理：

```go
// 使用goroutine来执行appTest
go func() {
    result, err := appTest(id, fileDst)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{
            "status":  "ERROR",
            "message": err.Error(),
        })
        return
    }
    // 判断是否通过
    if result.Score >= 70 {
        result.Info = "PASS"
    } else {
        result.Info = "DON'T PASS"
    }
    // 返回结果
    c.JSON(http.StatusOK, result)
}()
```

但是在测试的时候发现，这样容易让工作目录混乱，好像在进入goroutine之后就立刻执行了切换回原工作目录的操作。

同时，还会出现`Headers were already written`的错误，
问题可能是因为`gin.Context`在goroutine中使用时可能存在一些竞争条件或者生命周期管理上的问题。

1. `gin.Context`不适合在goroutine中长期持有和使用：Gin的文档中建议，`gin.Context`的使用应该局限在当前请求的生命周期内， 
并且不应该在异步goroutine中使用，除非你能确保上下文的安全使用。

2. 二次响应可能是由于请求的生命周期已经结束：如果请求的生命周期已经结束（可能由于超时等其他因素）， 
再调用`c.JSON`就会导致`Headers were already written`的错误。

而且最后发现Gin框架本身已经支持多请求的并发处理。Go的HTTP服务器（包括 Gin）在后台使用了`net/http`包，
该包本身就是并发处理的，每个请求都会在一个独立的goroutine中处理。

## 5.数据库连接

**本项目使用的是Gorm作为ORM框架。**

## clean_cache.go中diskUsage第一次使用会报错

因为最开始没有生成result目录，所以会找不到该目录


