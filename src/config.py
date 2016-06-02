#!/usr/bin/env python
#coding:utf-8

from configobj import ConfigObj

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

#read config file
install_path=r'/usr/local/listen'
try:
    configfilename = install_path + '/conf/listen.conf'
    yonconfig = ConfigObj(configfilename, encoding="utf8")
except IOError, e:
    print "Read yonserver.conf Error:"+str(e)
    sys.exit()


#defind Expires type
ExpiresTypes = {
    "d"	: 86400,
	"h"	: 3600,
	"m"	: 60,
}

#defind http mime.types
contentTypes=[]
for m in yonconfig['contentTypes']:
    tmp=[]
    tmp.append(m)
    tmp.append(yonconfig['contentTypes'][m])
    contentTypes.append(tmp)
contentTypes=dict(contentTypes)


#set web server version
server_version = yonconfig['version']['server_version']
sys_version = yonconfig['version']['sys_version']

#bind webserver ip
bind_ip=yonconfig['server']['bind_ip']

#bind webserver port
port=int(yonconfig['server']['port'])

#set python version
#sys_version = yonconfig['sys_version']

#set http protocol version
protocol_version = yonconfig['Http-version']['protocol_version']

#set gzip on/off
gzip=yonconfig['gzip']['gzip']
#set compress level(1~9)
compresslevel=int(yonconfig['gzip']['compresslevel'])

#set ssl(on/off)
ssl=yonconfig['ssl']['ssl']
privatekey=yonconfig['ssl']['privatekey']
certificate=yonconfig['ssl']['certificate']

#set file Expires(d/h/m).
Expires=yonconfig['cache']['Expires']

#Multithreading support
Multithreading=yonconfig['work']['Multithreading']

#Multiprocess support
Multiprocess=yonconfig['work']['Multiprocess']

#set document_root
DocumentRoot=yonconfig['root']['DocumentRoot']

#set 404 page
page404=yonconfig['root']['page404']

#directory list
Indexes=yonconfig['root']['Indexes']

#set default page
indexpage=yonconfig['root']['indexpage']

#set access log
Logfile=yonconfig['log']['Logfile']

#set error log
errorfile=yonconfig['log']['errorfile']

#set cgi(on/off)
cgi_moudle=yonconfig['cgi']['cgi_moudle']
cgi_path=yonconfig['cgi']['cgi_path']
cgi_pwd=yonconfig['cgi']['cgi_pwd']
cgi_extensions=eval(yonconfig['cgi']['cgi_extensions'], dict(__builtins__=None))
