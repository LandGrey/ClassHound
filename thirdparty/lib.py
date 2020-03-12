#!/usr/bin/env python
# coding: utf-8
# Build By LandGrey

import os
import sys
import random
import string
import platform

try:
    from urlparse import urlparse
except ImportError:
    from urllib.request import urlparse

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

# 首次尝试下载的文件
init_travel_files_without_prefix = [
    # WEB-INF 直系目录 xml
    'WEB-INF/web.xml',
    'WEB-INF/spring.xml',
    'WEB-INF/config.xml',
    'WEB-INF/ehcache.xml',
    'WEB-INF/weblogic.xml',
    'WEB-INF/springmvc.xml',
    'WEB-INF/spring-mvc.xml',
    'WEB-INF/mybatis.cfg.xml',
    'WEB-INF/springMVC-mvc.xml',
    'WEB-INF/spring-config.xml',
    'WEB-INF/struts-config.xml',
    'WEB-INF/mybatis-config.xml',
    'WEB-INF/spring-service.xml',
    'WEB-INF/spring-mvc-base.xml',
    'WEB-INF/spring-resource.xml',
    'WEB-INF/spring-context-ws.xml',
    'WEB-INF/spring-context-web.xml',
    'WEB-INF/spring-mvc-servlet.xml',
    'WEB-INF/applicationContext.xml',
    'WEB-INF/dispatcher-servlet.xml',
    'WEB-INF/spring-context-dev.xml',
    'WEB-INF/spring-context-app.xml',
    'WEB-INF/spring-context-prd.xml',
    'WEB-INF/spring-context-prod.xml',
    'WEB-INF/spring-context-main.xml',
    'WEB-INF/spring-context-base.xml',
    'WEB-INF/spring-context-cache.xml',
    'WEB-INF/spring-context-common.xml',
    'WEB-INF/spring-context-public.xml',
    'WEB-INF/spring-context-mybatis.xml',
    'WEB-INF/spring-context-servlet.xml',
    'WEB-INF/spring-context-datasource.xml',
    'WEB-INF/spring-context-production.xml',
    'WEB-INF/spring-context-development.xml',

    # WEB-INF/classes 目录 xml
    'WEB-INF/classes/web.xml',
    'WEB-INF/classes/spring.xml',
    'WEB-INF/classes/config.xml',
    'WEB-INF/classes/ehcache.xml',
    'WEB-INF/classes/weblogic.xml',
    'WEB-INF/classes/springmvc.xml',
    'WEB-INF/classes/spring-mvc.xml',
    'WEB-INF/classes/mybatis.cfg.xml',
    'WEB-INF/classes/springMVC-mvc.xml',
    'WEB-INF/classes/spring-config.xml',
    'WEB-INF/classes/struts-config.xml',
    'WEB-INF/classes/mybatis-config.xml',
    'WEB-INF/classes/spring-service.xml',
    'WEB-INF/classes/spring-mvc-base.xml',
    'WEB-INF/classes/spring-resource.xml',
    'WEB-INF/classes/spring-context-ws.xml',
    'WEB-INF/classes/spring-context-web.xml',
    'WEB-INF/classes/spring-mvc-servlet.xml',
    'WEB-INF/classes/applicationContext.xml',
    'WEB-INF/classes/dispatcher-servlet.xml',
    'WEB-INF/classes/spring-context-dev.xml',
    'WEB-INF/classes/spring-context-app.xml',
    'WEB-INF/classes/spring-context-prd.xml',
    'WEB-INF/classes/spring-context-prod.xml',
    'WEB-INF/classes/spring-context-main.xml',
    'WEB-INF/classes/spring-context-base.xml',
    'WEB-INF/classes/spring-context-cache.xml',
    'WEB-INF/classes/spring-context-common.xml',
    'WEB-INF/classes/spring-context-public.xml',
    'WEB-INF/classes/spring-context-mybatis.xml',
    'WEB-INF/classes/spring-context-servlet.xml',
    'WEB-INF/classes/spring-context-datasource.xml',
    'WEB-INF/classes/spring-context-production.xml',
    'WEB-INF/classes/spring-context-development.xml',

    # WEB-INF 其他目录 xml
    'WEB-INF/classes/spring/spring.xml',
    'WEB-INF/classes/spring/springmvc.xml',
    'WEB-INF/classes/spring/spring-dao.xml',
    'WEB-INF/classes/spring/spring-web.xml',
    'WEB-INF/classes/spring/spring-mvc.xml',
    'WEB-INF/classes/spring/spring-config.xml',
    'WEB-INF/classes/spring/spring-service.xml',
    'WEB-INF/classes/spring/spring-resource.xml',
    'WEB-INF/classes/mybatis/mybatis-config.xml',

    # WEB-INF 直系目录 properties
    'WEB-INF/db.properties',
    'WEB-INF/app.properties',
    'WEB-INF/jdbc.properties',
    'WEB-INF/config.properties',
    'WEB-INF/spring.properties',
    'WEB-INF/database.properties',
    'WEB-INF/fckeditor.properties',
    'WEB-INF/properties.properties',
    'WEB-INF/application.properties',

    # WEB-INF/classes 目录 properties
    'WEB-INF/classes/db.properties',
    'WEB-INF/classes/app.properties',
    'WEB-INF/classes/jdbc.properties',
    'WEB-INF/classes/config.properties',
    'WEB-INF/classes/spring.properties',
    'WEB-INF/classes/database.properties',
    'WEB-INF/classes/fckeditor.properties',
    'WEB-INF/classes/properties.properties',
    'WEB-INF/classes/application.properties',

    # WEB-INF/config 目录 properties
    'WEB-INF/config/db.properties',
    'WEB-INF/config/app.properties',
    'WEB-INF/config/jdbc.properties',
    'WEB-INF/config/config.properties',
    'WEB-INF/config/spring.properties',
    'WEB-INF/config/database.properties',
    'WEB-INF/config/properties.properties',
    'WEB-INF/config/application.properties',

    # WEB-INF/properties 目录 properties
    'WEB-INF/properties/db.properties',
    'WEB-INF/properties/app.properties',
    'WEB-INF/properties/jdbc.properties',
    'WEB-INF/properties/config.properties',
    'WEB-INF/properties/spring.properties',
    'WEB-INF/properties/database.properties',
    'WEB-INF/properties/properties.properties',
    'WEB-INF/properties/application.properties',

    # WEB-INF 其他目录 properties
    'WEB-INF/classes/META-INF/properties/database.properties',
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

    '/ch/qos/',
    '/jxl/write/',
    '/jcifs/http/',
    '/de/innosystec/',

    '/org/jcp/',
    '/org/omg/',
    '/org/w3c/',
    '/org/xml/',
    '/org/json/',
    '/org/jdom/',
    '/org/jasig',
    '/org/slf4j/',
    '/org/dom4j/',
    '/org/jfree/',
    '/org/tuckey/',
    '/org/quartz/',
    '/org/apache/',
    '/org/mybatis/',
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
    '/com/mchange/'
    '/com/aliyuncs/',
    '/com/baidubce/',
    '/com/microsoft/',
]


def get_root_path():
    try:
        root_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0]))).encode('utf-8').decode() \
            if int(platform.python_version()[0]) == 3 \
            else os.path.dirname(os.path.abspath(sys.argv[0])).decode('utf-8')
    except:
        root_path = None
        exit("\n[-] Please ensure directory path name is full english characters\n")
    return root_path


def get_workspace(_url):
    hostname = urlparse(_url).netloc
    return os.path.join(get_root_path(), hostname.replace(":", "+"))


def get_random_string(length=8, prefix="", suffix=""):
    middle = "".join(random.sample(string.ascii_lowercase, length))
    return prefix + middle + suffix


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


def walk_file_paths(directory):
    file_paths = []
    for root_path, subdir_name, file_names in os.walk(directory):
        file_paths.extend([os.path.abspath(os.path.join(root_path, _)) for _ in file_names])
    return file_paths


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
