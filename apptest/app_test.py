import os
import subprocess
import re
import json
import requests
import csv
import time
import io
import shutil
from optparse import OptionParser
'''
1.安装cppcheck:
sudo apt install cppcheck
2.安装clamav:
sudo apt install clamav
更新病毒库：
sudo service clamav-freshclam stop
sudo freshclam
sudo service clamav-freshclam start
3.安装checksec
sudo apt install checksec
4.输入当前用户的密码passwd
5.安装yara
sudo apt install yara
6.填写yara规则路径,默认为当前路径下的rules目录
7.安装die
sudo apt install biz.ntinfo.die

yara-rules来源:
https://github.com/Neo23x0/signature-base/tree/master/yara
https://github.com/Neo23x0/signature-base/tree/master/yara

使用方法：
安装应用后执行:python3 apptest.py -f test.dep -s ./test -c 1.json
-f 指定测试的deb包。
-s 指定应用源码目录。
-c 应用组件json文件,例:{"git":"1:2.20.1-2+deb10u1","curl":"7.64.0-4+deb10u3"}
-d 批量测试目录
-p 指定进程pid
'''

passwd = 'passwd'
rules_path= 'rules'
blacklist=[
                '/usr/share/ca-certificates/deepin/',
                '/etc/ssl/certs/',
                '/usr/local/share/ca-certificates/',
                '/var/lib/deepin/developer-mode/',
                '/sys/kernel/security/',
                '/etc/',
                '/var/lib/',
                '/var/cache/',
                '/usr/'
            ]

servicelist=[
                '/usr/share/dbus-1/system.d/',
                '/usr/share/dbus-1/services/',
                '/usr/share/dbus-1/system-services/',
                '/etc/systemd/system/',
                '/usr/lib/systemd/system/',
            ]

installlist=[
                'postinst',
                'postrm',
                'preinst',
                'prerm',
            ]

whitelist=[ '/etc/systemd/user/','/usr/share/icons/','/usr/share/applications/','/usr/share/doc/']

TEST_RESULT_SUCCESS = '测试通过'
TEST_RESULT_FIAL = '测试失败'

test_item_dict = {
    "应用网络通信检测" : "20001",
    "应用安全功能检测" : "20002",
    "应用能力特权检测" : "20003",
    "应用安全保护机制检测" : "20004",
    "应用文件权限检测" : "20005",
    "应用权限检测" : "20006",
    "应用木马病毒扫描" : "20007",
    "应用静态代码扫描" : "20008",
    "应用漏洞扫描" : "20009",
    "应用安装脚本检测" : "20010",
    "应用检测总分" : "20011",
    "测试结论" : "20012"
}

def obj_build(name, result = TEST_RESULT_SUCCESS):
         result_obj = {}
         result_obj['name']=name
         result_obj['result']=result

         return result_obj

def write_json(dic, pjson = "results/apptest_result.json"):
    directory = os.path.dirname(pjson)
    if not os.path.exists(directory):
        os.makedirs(directory)

    try:
        with open(pjson, "w", encoding="utf-8") as f:
            json.dump(dic, f, indent=4, ensure_ascii=False)
    except BaseException as e:
        print("写入json文件报错:", e)

def init_resdic(self):
    for test_item, test_code in test_item_dict.items():
        self.resdic[test_code] = obj_build(test_item, TEST_RESULT_SUCCESS)
    write_json(self.resdic)

class App:
    def __init__(self, deb, pid):
        self.resdic={}
        init_resdic(self)
        self.score = 100
        self.deb = deb
        self.service = False
        if '/' in self.deb:
            self.file = self.deb.split('/')[-1].rstrip('.deb')
        else:
            self.file = self.deb.rstrip('.deb')
        if os.path.exists(self.file + '.csv'):
            os.remove(self.file + '.csv')
        with open(self.file + ".csv", 'a+', newline='') as f:
            write = csv.writer(f, dialect='excel')
            write.writerow(["检测项", "问题类型", "扣除分数"])
        os.system("dpkg -x " + self.deb + " " + self.file)
        self.pkgname = os.popen("dpkg-deb -W " + self.deb).read().strip().split('\t')[0]
        whitelist.append('/etc/'+self.pkgname)
        whitelist.append('/var/lib/'+self.pkgname)
        whitelist.append('/var/cache/'+self.pkgname)
        whitelist.append('/usr/'+self.pkgname)
        self.paths = os.popen("dpkg-deb -c " + self.deb).readlines()
        if not os.path.exists(self.file):
            os.mkdir(self.file)
        self.pid = pid
        if self.pid == '':
            self.elf, self.pid = self.install()
        else:
            r = os.popen("ps -aux |grep " + self.pid + " |grep -v grep").readline().split(' ')
            self.elf = list(filter(None, r))[10]
            if not os.path.exists(self.elf):
                self.elf = ''
        if self.elf == 1:
            self.elf = ''
            self.inst = True
        elif self.elf:
            self.inst = True
        else:
            self.inst = False
        if self.pid:
            self.network_check()
            self.features_check()
            os.system("sudo kill -9 " + self.pid)
            if os.path.exists("test.out"):
                os.remove("test.out")
        self.perl_check()
        self.service_check()
        self.cap_check()
        self.checksec()
        self.power_chech()
        self.virus_check()
        if opt.source:
            self.cpp_check()
        if opt.composition:
            self.get_cve()
        self.uninstall()


    def install(self):
        try:
            print('安装应用:' + self.file)
            p = subprocess.Popen("echo " + passwd + "|sudo -S dpkg -i " + self.deb, shell=True, stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            p.wait()
            print('安装完成')
            subprocess.getstatusoutput("sudo apt-get -f install -y")
            #subprocess.getstatusoutput("sudo dpkg -E -i " + self.deb)
            files = os.popen("dpkg -c " + self.deb).readlines()
            for file in files:
                file = file.strip()
                if file.startswith('-'):
                    file = file.split('./')[-1]
                    if os.path.exists('/' + file):
                        print("安装成功")
                        break
                    else:
                        print("安装失败：请手动安装应用，并运行应用，使用 -p 指定应用进程pid")
                        return "", ""
            r = os.popen("dpkg -c " + self.deb + " |grep '\.desktop'").readlines()
            if r:
                if len(r) > 1:
                    for i in r:
                        if 'autostart' in i:
                            desktop = i
                            break
                        if 'entries/applications' in i:
                            desktop = i
                            break
                    if not desktop:
                        desktop = r[0]
                else:
                    desktop = r[0]
                desktop = desktop.strip().split(' ')[-1].strip('.')
                # print(desktop)
                execs = os.popen("cat " + desktop + " |grep Exec=").readlines()
                for Exec in execs:
                    if Exec.startswith('Exec='):
                        Exec = Exec.strip().lstrip('Exec=')
                        break
                if '/' not in Exec:
                    ELF = os.popen("which " + Exec).read().strip()
                    Exec = ELF
                elif ' ' in Exec:
                    ELF = Exec.split(' ')[0]
                else:
                    ELF = Exec
                ELF = ELF.strip("\"")
                # print(Exec)
                # if os.path.exists(ELF):
                #     print('安装成功')
                # else:
                #     ELF = ''
            else:
                print("未发现可执行文件")
                return 1, ''
        except Exception as e:
            print('安装失败:请手动安装应用，并运行应用，使用 -p 指定应用进程pid')
            print(e)
            return '', ''
        try:
            print("后台运行应用....")
            os.system("sudo ldconfig")
            if 'autostart' not in desktop:
                p = subprocess.Popen("nohup " + Exec + " >test.out 2>&1 &", shell=True,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, bufsize=-1)
                pid = p.pid
                p.wait(3)
            else:
                if ELF:
                    r = os.popen("ps -aux|grep " + ELF + " |grep -v grep").readline()
                    if r:
                        pid = list(filter(None, r.split(' ')))[1]
                    else:
                        p = subprocess.Popen("nohup " + Exec + " >test.out 2>&1 &", shell=True,
                                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, bufsize=-1)
                        p.wait(3)
                        pid = p.pid

            r = os.popen('ps -aux |grep ' + str(pid) + ' |grep -v grep').read()
            if r:
                print("运行成功,pid=" + str(pid))
                return ELF, str(pid)
            elif ELF:
                r2 = os.popen('ps -aux |grep ' + ELF + ' |grep -v grep').readline()
                if r2:
                    pid = list(filter(None, r2.split(' ')))[1]
                    print("运行成功,pid=" + str(pid))
                    return ELF, str(pid)
                # else:
                else:
                    print('运行失败:请手动安装应用，并运行应用，使用 -p 指定应用进程pid')
                    return ELF, ''
            else:
                print('运行失败:请手动安装应用，并运行应用，使用 -p 指定应用进程pid')
                return ELF, ''
        except Exception as e:
            print(e)
            print('运行失败:请手动安装应用，并运行应用，使用 -p 指定应用进程pid')
            return ELF, ''

    def uninstall(self):
        print('卸载应用......')
        try:
            p = subprocess.Popen("echo " + passwd + "|sudo -S apt-get purge -y " + self.pkgname, shell=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, bufsize=-1)
            p.wait()
        except Exception as e:
            print('卸载失败')

    def save(self, data):
        # 保存结果
        with open(self.file + ".csv", 'a+', newline='') as f:
            write = csv.writer(f, dialect='excel')
            write.writerow(data)

    def perl_check(self):
        test_item = '应用安装脚本检测'
        des = ""
        print(test_item + '......')
        p=subprocess.Popen("/usr/bin/dpkg-deb -e "+self.deb,shell=True,stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, bufsize=-1)
        p.wait()
        file=os.listdir('DEBIAN')
        for i in installlist:
            if i in file:
                less=5
                self.score = self.score - less
                des += "包内存在安装脚本" + i + ":\n"
                # 查看脚本是否存在chmod，记录第几行出现chmod存在des中
                with open('DEBIAN/' + i, 'r') as f:
                    linenum = 0
                    lines = f.readlines()
                    for line in lines:
                        linenum += 1
                        if 'chmod' in line:
                            less=100
                            self.score = self.score - less
                            des += "该脚本中第" + str(linenum) + "行存在chmod:" + line
                            break
                print('[*]' + des)
        if des:
             self.resdic[test_item_dict[test_item]] = obj_build(test_item, des)
             self.save([test_item, des, less])
        shutil.rmtree('DEBIAN')


    def cap_check(self):
        test_item = '应用能力特权检测'
        print(test_item + '......')
        try:
            if self.elf and 'ELF' in os.popen('file ' + '"' + self.elf + '"').read():
                r = os.popen('getcap ' + '"' + self.elf + '"').read()
                if r:
                    less = 100
                    self.score = self.score - less
                    des = "应用存在能力权限问题,请验证是否可提权：" + self.elf
                    print('[*]' + des)
                    self.resdic[test_item_dict[test_item]] = obj_build(test_item, des)
                    self.save([test_item, des, less])
            else:
                for path in self.paths:
                    path = path.strip()
                    if not path.startswith('-'):
                        continue
                    path = self.file + '/' + path.split(' ./')[-1]
                    if 'ELF' not in os.popen('file ' + '"' + path + '"').read():
                        continue
                    r = os.popen('getcap ' + '"' + path + '"').read()
                    if r:
                        less = 100
                        self.score = self.score - less
                        des = "应用存在能力权限问题,请验证是否可提权：" + path
                        print('[*]' + des)
                        self.resdic[test_item_dict[test_item]] = obj_build(test_item, des)
                        self.save([test_item, des, less])
        except Exception as e:
            print(e)

    def checksec(self):
        test_item = "应用安全保护机制检测"
        # die_path="/opt/apps/biz.ntinfo.die/files/bin/diec.sh"
        # if not os.path.exists(die_path):
        #     print('请安装die工具，sudo apt install biz.ntinfo.die')
        #     return
        print(test_item + '......')
        try:
            # print(self.elf)
            if self.elf and 'ELF' in os.popen('file ' + '"' + self.elf + '"').read():
                # r=os.popen(die_path+" "+self.elf).read()
                # if 'packer:' in r:
                #     self.score=self.score+5
                #     print("应用使用了加壳保护，加5分")
                p = subprocess.Popen("sudo checksec -f " + self.elf, shell=True,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1)
                p.wait()
                # str_out=str(io.TextIOWrapper(p.stdout,encoding='utf-8').read())
                str_err = str(io.TextIOWrapper(p.stderr, encoding='utf-8').read())
                str_out = str(io.TextIOWrapper(p.stdout, encoding="utf-8").read())
                if 'No RELRO' or "No canary found" or "NX disabled" in str_out:
                    less = 0
                    self.score = self.score - less
                    des = "应用无安全保护机制：" + self.elf
                    print('[*]' + des)
                    self.resdic[test_item_dict[test_item]] = obj_build(test_item, des)
                    self.save([test_item, des, less])
                    return
            else:
                for path in self.paths:
                    path = path.strip()
                    if not path.startswith('-'):
                        continue
                    path = self.file + '/' + path.split(' ./')[-1]
                    r = os.popen('file ' + '"' + path + '"').read()
                    if 'ELF' in r:
                        p = subprocess.Popen("sudo checksec -f " + self.elf, shell=True,
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1)
                        p.wait()
                        str_err = str(io.TextIOWrapper(p.stderr, encoding='utf-8').read())
                        str_out = str(io.TextIOWrapper(p.stdout, encoding="utf-8").read())
                        if 'No RELRO' or "No canary found" or "NX disabled" in str_out:
                            less = 0
                            self.score = self.score - less
                            des = "应用无安全保护机制：" + path
                            print('[*]' + des)
                            self.resdic[test_item_dict[test_item]] = obj_build(test_item, des)
                            self.save([test_item, des, less])
                            return
        except Exception as e:
            print(e)

    def network_check(self):
        test_item = "应用网络通信检测"
        print(test_item + '......')
        try:
            r = os.popen("sudo netstat -anpt |grep " + self.pid + "/").read()
            if r:
                less = 100
                des = "应用存在端口监听，请对端口服务进行安全测试"
                self.score = self.score - less
                print('[*]' + des)
                self.resdic[test_item_dict[test_item]] = obj_build(test_item, des)
                self.save([test_item, des, less])
        except Exception as e:
            print(e)

    def features_check(self):
        test_item = "应用安全功能检测"
        print(test_item + '......')
        less = 3
        des = ""
        try:
            if os.path.exists("/proc/" + self.pid + "/status"):
                seccomp = os.popen("cat /proc/" + self.pid + "/status |grep Seccomp").read()
                if '0' in seccomp:
                    self.score = self.score - less
                    des += "应用未使用seccomp;"
                    print('[*]' + des)
                namespace = os.popen("sudo ls -la /proc/" + self.pid + "/ns").read()
                if not namespace:
                    self.score = self.score - less
                    des += "应用未使用namespace;"
                    print('[*]' + des)
                path = os.popen("ps -aux |grep " + self.pid).readline().split(' ')
                path = list(filter(None, path))[10]
                if '/' not in path:
                    path = os.popen("which " + path).read().strip()
                if 'ELF' in os.popen('file ' + '"' + path + '"').read():
                    r = os.popen("readelf -d " + path).read()
                    if 'PATH' not in r:
                        self.score = self.score - less
                        des += "应用未使用RPATH/RUNPATH"
                        print('[*]' + des)
            else:
                print("进程中断...")

            if des:
                self.resdic[test_item_dict[test_item]] = obj_build(test_item, des.strip())
                self.save([test_item, des.strip(), less])
        except Exception as e:
            print(e)

    def power_chech(self):
        test_item = "应用文件权限检测"
        print(test_item + '......')
        root=False
        write=False
        PATH=False
        white=False
        des = ""
        try:
            if self.inst:
                for path in self.paths:
                    if PATH:
                        break
                    else:
                        path = path.strip()
                        if not path.startswith('-'):
                            continue
                        path = '/' + path.split(' ./')[-1]
                        for i in whitelist:
                            if i in path:
                                white=True
                        if not white:
                            for j in blacklist:
                                if PATH:
                                    break
                                # elif j in path:
                                elif path.startswith(j):
                                    less=10
                                    self.score=self.score - less
                                    des += "非法路径:" + path
                                    print('[*]' + des)
                                    PATH=True
                                    break

                    if 'ELF' not in os.popen('file ' + '"' + path + '"').read():
                        continue
                    if os.path.exists(path):    
                        r = os.popen('sudo ls -la ' + '"' + path + '"').read()
                        if 'root' in r:
                            if 'rws' in r and 'sandbox' not in r:
                                less=100
                                self.score=self.score - less
                                des += "应用文件存在suid权限:" + r
                                print('[*]' + des)

                            if not write:
                                if re.findall(r"^-.......w.", r):
                                    less = 100
                                    self.score = self.score - less
                                    des += "应用存在文件权限过高问题，请验证是否可提权:" + r
                                    print('[*]' + des)
                                    write=True
                        elif not root:
                            if not path.endswith('desktop'):
                                if self.service:
                                    less=100
                                    self.score=self.score-less
                                    des += "文件权限不为root:root " + '\n'
                                    # 运行file命令查看文件类型，存在des中
                                    des += os.popen("file \"" + self.file + path + "\"").read()
                                    print('[*]' + des)
                                    root=True
                                else:
                                    less=10
                                    self.score=self.score-less
                                    des += "文件权限不为root:root " + '\n'
                                    # 运行file命令查看文件类型，存在des中
                                    des += os.popen("file \"" + self.file + path + "\"").read()
                                    print('[*]' + des)
                                    root=True

            else:
                for path in self.paths:
                    if PATH:
                        break
                    else:
                        path = path.strip()
                        if not path.startswith('-'):
                            continue
                        if 'root/root' in path:
                            if 'rws' in path and 'sandbox' not in path:
                                less=100
                                self.score=self.score - less
                                des += "应用文件存在suid权限:" + path
                                print('[*]' + des)

                            if not write:
                                if re.findall(r"^-.......w.", path):
                                    less = 100
                                    self.score = self.score - less
                                    des += "应用存在文件权限过高问题，请验证是否可提权:" + path
                                    print('[*]' + des)
                                    write=True
                        elif not root:
                            if not path.endswith('desktop'):
                                path = '/' + path.split(' ./')[-1]
                                if self.service:
                                    less=100
                                    self.score=self.score-less
                                    des += "文件权限不为root:root " + '\n'
                                    # 运行file命令查看文件类型，存在des中
                                    des += os.popen("file \"" + self.file + path + "\"").read()
                                    print('[*]' + des)
                                    root=True
                                else:
                                    less=10
                                    self.score=self.score-less
                                    des += "文件权限不为root:root " + '\n'
                                    # 运行file命令查看文件类型，存在des中
                                    des += os.popen("file \"" + self.file + path + "\"").read()
                                    print('[*]' + des)
                                    root=True

                        path = '/' + path.split(' ./')[-1]
                        for i in whitelist:
                            if i in path:
                                white=True
                        if not white:
                            for j in blacklist:
                                if PATH:
                                    break
                                # elif j in path:
                                elif path.startswith(j):
                                    less=10
                                    self.score=self.score - less
                                    des += "非法路径:" + path
                                    print('[*]' + des)
                                    PATH=True
                                    break

                    # if os.path.exists(path):    
                    #     r = os.popen("sudo ls -la " + "'" + path + "'").read()
                    #     if 'root' in r:
                    #         if 'rws' in r:
                    #             less=100
                    #             self.score=self.score - less
                    #             des="应用文件存在suid权限:" + r
                    #             print('[*]' + des)
                    #             self.save([test_item, des, less])

                    #         if not write:
                    #             if re.findall(r"-.......w.", r):
                    #                 less = 40
                    #                 self.score = self.score - less
                    #                 des = "应用存在文件权限过高问题，请验证是否可提权:" + r
                    #                 print('[*]' + des)
                    #                 self.save([test_item, des, less])
                    #                 write=True
                    #     elif not root:
                    #         if not path.endswith('desktop'):
                    #             less=40
                    #             self.score=self.score-less
                    #             des="文件权限不为root:root " + path
                    #             print('[*]' + des)
                    #             self.save([test_item, des, less])
                    #             root=True
            if des:
                self.resdic[test_item_dict[test_item]] = obj_build(test_item, des.strip())
                self.save([test_item, des.strip(), less])

        except Exception as e:
            print(e)

    def service_check(self):
        test_item = '应用权限检测'
        print(test_item + '......')
        try:
            for i in servicelist:
                if i in str(self.paths):
                    less = 100
                    self.score = self.score - less
                    des = '应用存在root权限的服务'
                    self.service = True
                    print('[*]' + des)
                    self.resdic[test_item_dict[test_item]] = obj_build(test_item, des)
                    self.save([test_item, des, less])
                    break
        except Exception as e:
            print(e)

    def virus_check(self):
        test_item = "应用木马病毒扫描"
        virus_list=[]
        print(test_item + '......')
        try:
            r1 = os.popen("clamscan -r -i " + self.file + " |grep FOUND").read().strip()
            if r1:
                less = 100
                self.score = self.score - less
                des = "应用存在木马病毒:\n" + r1
                print('[*]' + des)
                self.resdic[test_item_dict[test_item]] = obj_build(test_item, des)
                self.save([test_item, des, less])
            rules=os.listdir(rules_path)
            # print(rules)
            for rule in rules:
                rule=rules_path+'/'+rule
                #print(rule)
                try:
                    p = subprocess.Popen("yara "+rule+" -p 100 -r "+self.file, shell=True,
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1)
                    p.wait()
                    str_err = str(io.TextIOWrapper(p.stderr, encoding='utf-8').read())
                    str_out = str(io.TextIOWrapper(p.stdout, encoding="utf-8").read().strip())
                    if str_out:
                        virus_list.append(str_out)
                except Exception as e:
                    print(e)
            if len(virus_list)>0:
                virus=','.join(virus_list)
                less=100
                self.score = self.score - less
                des = "应用存在木马病毒:" + virus
                print('[*]' + des)
                self.resdic[test_item_dict[test_item]] = obj_build(test_item, des)
                self.save([test_item, des, less])
            os.system("rm -rf " + self.file)
        except Exception as e:
            print(e)

    def cpp_check(self):
        test_item = "应用静态代码扫描"
        print(test_item + '......')
        try:
            os.system("cppcheck " + opt.source +
                      " --force --xml --xml-version=2 2>" + self.file + ".xml")
            if os.popen("cat " + self.file + ".xml |grep severity").read():
                less = '0-100'
                des = "应用源代码存在安全问题，请检查" + self.file + ".xml"
                print('[*]' + des)
                self.resdic[test_item_dict[test_item]] = obj_build(test_item, des)
                self.save([test_item, des, less])
            else:
                os.remove(self.file + '.xml')
        except Exception as e:
            print(e)

    def get_cve(self):
        # 对比应用版本，获取应用组件存在的CVE漏洞
        test_item = "应用漏洞扫描"
        print(test_item + '......')
        url = "https://security-tracker.debian.org/tracker/data/json"
        try:
            r = requests.get(url)
            data = json.loads(r.text)
            # print(data)
            with open(opt.composition, "r") as f:
                j = json.load(f)
                for name in j:
                    version = j[name]
                    for i in data[name]:
                        if data[name][i]['releases']['buster']['status'] == 'resolved':
                            if data[name][i]['releases']['buster']['repositories']['buster-security']:
                                fix_version = data[name][i]['releases']['buster']['repositories']['buster-security']
                            else:
                                fix_version = data[name][i]['releases']['buster']['repositories']['buster']
                            cmd = "dpkg --compare-versions {} ge {} && echo 1".format(
                                version, fix_version)
                            output = os.popen(cmd).read()
                            if output:
                                continue
                            else:
                                vul_level = self.get_level(i)
                        else:
                            vul_level = self.get_level(i)
                        if vul_level == 'CRITICAL':
                            less = 40
                            self.score = self.score - less
                            des = name + '版本' + version + '小于' + fix_version + "存在" + i + "漏洞,等级为严重,请确认是否存在PoC/EXP"
                        if vul_level == 'HIGH':
                            less = 40
                            self.score = self.score - less
                            des = name + '版本' + version + '小于' + fix_version + "存在" + i + "漏洞,等级为高危,请确认是否存在PoC/EXP"
                        if vul_level == 'MEDIUM':
                            less = 5
                            self.score = self.score - less
                            des = name + '版本' + version + '小于' + fix_version + "存在" + i + "漏洞,等级为中危"
                        if vul_level == 'LOW':
                            less = 3
                            self.score = self.score - less
                            des = name + '版本' + version + '小于' + fix_version + "存在" + i + "漏洞,等级为低危"
                        if vul_level == '':
                            less = 0
                            self.score = self.score - less
                            des = name + '版本' + version + '小于' + fix_version + "存在" + i + "漏洞,等级未知"
                        print('[*]' + des)
                        self.resdic[test_item_dict[test_item]] = obj_build(test_item, des)
                        self.save([test_item, des, less])
                        time.sleep(5)
        except Exception as e:
            print(e)

    def get_level(self, i):
        # 从vul获取漏洞等级
        url = "https://services.nvd.nist.gov/rest/json/cves/2.0?cveId=" + i
        try:
            r = requests.get(url)
            if r.text:
                data = json.loads(r.text)
                if 'cvssMetricV31' in r.text:
                    level = data['vulnerabilities'][0]['cve']['metrics']['cvssMetricV31'][0]['cvssData']['baseSeverity']
                elif 'cvssMetricV2' in r.text:
                    level = data['vulnerabilities'][0]['cve']['metrics']['cvssMetricV2'][0]['cvssData']['baseSeverity']
                else:
                    level = ''
                return level
        except Exception as e:
            print(e)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-f', '--file', dest='file', help="目标deb安装包")
    parser.add_option('-s', '--source', dest='source', help="目标源码路径")
    parser.add_option('-c', '--composition', dest='composition', help="目标组件信息路径")
    parser.add_option('-d', '--dir', dest="dir", help="批量扫描目录")
    parser.add_option('-p', '--pid', dest='pid', help="应用进程pid")
    # parser.add_option("--install",default=False,action='store_true',help="检测安装脚本")
    # parser.add_option("--service",default=False,action='store_true',help="检测服务")
    (opt, args) = parser.parse_args()

    try:
        subprocess.check_call(["sudo", "-n", "true"])
        print("已设置sudo免密")
    except subprocess.CalledProcessError:
        if not passwd:
            print("请在42行配置sudo密码")
            exit(0)
  
    if opt.pid:
        pid = opt.pid
    else:
        pid = ''
    if opt.file:
        a = App(opt.file, pid)
        status = ""
        if a.score<0:
            a.score=0
        if a.score>=70:
            status = "通过"
            print(a.file + ' 当前分数为:' + str(a.score))
            print('测试结果：通过')
            print('测试报告：'+a.file + '.csv')
        else:
            status = "未通过"
            print(a.file + ' 当前分数为:' + str(a.score))
            print('测试结果：未通过')
            print('测试报告：'+a.file + '.csv')
        a.save(['总分',str(a.score),''])
        a.resdic[test_item_dict["应用检测总分"]] = obj_build("应用检测总分", a.score)
        a.resdic[test_item_dict["测试结论"]] = obj_build("测试结论", status)
        write_json(a.resdic)

    elif opt.dir:
        pkgs = os.listdir(opt.dir)
        #pkgs = pkgs[180:]
        for pkg in pkgs:
            deb = opt.dir + pkg
            a = App(deb, pid)
            status = ""
            if a.score<0:
                a.score=0
            if a.score>=70:
                status = "通过"
                print(a.file + ' 当前分数为:' + str(a.score))
                print('测试结果：通过')
                print('测试报告：'+a.file + '.csv')
            else:
                status = "未通过"
                print(a.file + ' 当前分数为:' + str(a.score))
                print('测试结果：未通过')
                print('测试报告：'+a.file + '.csv')
            a.save(['总分',str(a.score),''])
            a.resdic[test_item_dict["应用检测总分"]] = obj_build("应用检测总分", a.score)
            a.resdic[test_item_dict["测试结论"]] = obj_build("测试结论", status)
            write_json(a.resdic)
            print('----------------------------------')
            # time.sleep(3)
    else:
        print(parser.usage)
