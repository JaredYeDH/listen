#!/usr/bin/env python
#coding:utf-8
import logging
import string,cgi,time,os,socket,sys
from SocketServer import BaseServer
from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn,ForkingMixIn
from CGIHTTPServer import CGIHTTPRequestHandler
import urllib
import shutil
from OpenSSL import SSL
from optparse import OptionParser
import select,errno
import pubutil
import config
#check path
def check():
    if config.ssl=="on":
        if not pubutil.checkfile(config.privatekey):
            print "Error: privatekey \""+config.privatekey+"\" No such file or directory."
            sys.exit()
    
        if not pubutil.checkfile(config.certificate):
            print "Error: certificate \""+config.certificate+"\" No such file or directory."
            sys.exit()
    
    if not pubutil.checkpath(config.DocumentRoot):
        print "Error: DocumentRoot \""+config.DocumentRoot+"\" No such file or directory."
        sys.exit()
    
    if not pubutil.checkfile(config.Logfile):
        print "Error: Logfile \""+config.Logfile+"\" No such file or directory."
        sys.exit()
    
    if not pubutil.checkfile(config.errorfile):
        print "Error: errorfile \""+config.errorfile+"\" No such file or directory."
        sys.exit()
    
    if config.cgi_moudle=="on":
        if len(config.cgi_path)==0:
            print "Error: cgi_path is null? please set."
            sys.exit()
        for _path in config.cgi_path:
            if not pubutil.checkpath(pubutil.cur_file_dir()+'/'+_path):
                print "Error: cgi_path \""+pubutil.cur_file_dir()+'/'+_path+"\" No such file or directory."
                sys.exit()
bind_ip=config.bind_ip
port=config.port
#system logs
try:
    logger=logging.getLogger()
    handler=logging.FileHandler(config.errorfile)
    logger.addHandler(handler)
    logger.setLevel(logging.NOTSET)
except IOError, e:
    print "+"+str(e)+"+"


class SecureHTTPServer(HTTPServer):
    def __init__(self, server_address, HandlerClass):
        BaseServer.__init__(self, server_address, HandlerClass)
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.use_privatekey_file (config.privatekey)
        ctx.use_certificate_file(config.certificate)
        self.socket = SSL.Connection(ctx, socket.socket(self.address_family,self.socket_type))
        self.server_bind()
        self.server_activate()

class ServerHandler(CGIHTTPRequestHandler):

    #webserver info
    server_version=config.server_version
    sys_version=config.sys_version
    protocol_version=config.protocol_version
    CGIHTTPRequestHandler.cgi_directories = config.cgi_path

    def handle_one_request(self):
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(414)
                return

            if not self.raw_requestline:
                self.close_connection = 1
                return
            if not self.parse_request():
                return

            mname = 'do_' + self.command
            if not hasattr(self, mname):
                self.send_error(501, "Unsupported method (%r)" % self.command)
                return
            method = getattr(self, mname)
            method()

            if not self.wfile.closed:
                self.wfile.flush() #actually send the response if not already done.

        except socket.timeout, e:
            logger.error(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))+"-"+str(e))
            self.close_connection = 1
            return

    def setup(self):
        self.connection = self.request
        self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
        self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)

    def do_GET(self):
        try:
            #go to deault page.
            if self.path.endswith("/") or self.path =="":
                if config.Indexes=="on":
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    f= self.list_directory(DocumentRoot+self.path)
                    self.copyfile(f, self.wfile)
                    f.close()
                    return
                elif config.indexpage=="":
                    self.send_response(302)
                    self.send_header("Location", indexpage)
                    self.end_headers()
                    return
                else:
                    self.send_response(404)
                self.path="/index.html"

            if self.path=='/favicon.ico':
                return
            path_parts = self.path.split('.')
            try:
                content_type=config.contentTypes[path_parts[-1]]
            except:
                if config.page404=="":
                    self.send_response(404)
                else:
                    self.send_response(302)
                    self.send_header("Location",config.page404)
                self.end_headers()


            if config.cgi_moudle=="on" and self.path.endswith(config.cgi_extensions):
                return CGIHTTPRequestHandler.do_GET(self)

            else:

                #do static content
                f = open(config.DocumentRoot + sep + self.path) #self.path has /test.html
                #note that this potentially makes every file on your computer readable by the internet
                fs = os.fstat(f.fileno())


                Expirestype=config.Expires[-1:]
                Expirenum=config.Expires[:-1]

                #set Expires
                expiration = pubutil.get_http_expiry(Expirestype,int(Expirenum))

                #set max-age
                CACHE_MAX_AGE=pubutil.secs_from_days(config.ExpiresTypes[Expirestype],int(Expirenum))
                cache_control = 'public; max-age=%d' % (CACHE_MAX_AGE, )

                client_cache_cc = self.headers.getheader('Cache-Control')
                client_cache_p = self.headers.getheader('Pragma')
                Modified_Since= self.headers.getheader('If-Modified-Since')
                if client_cache_cc=='no-cache' or client_cache_p=='no-cache' or \
                  (client_cache_cc==None and client_cache_p==None and Modified_Since==None):
                    client_modified=None
                else:
                    try:
                        client_modified = Modified_Since.split(';')[0]
                    except:
                        client_modified=None
                file_last_modified=self.date_time_string(fs.st_mtime)

                if client_modified==file_last_modified:
                    self.send_response(304)
                    self.end_headers()
                else:
                    if config.gzip=="on":
                        compressed_content = pubutil.compressBuf(f.read(),config.compresslevel)
                    else:
                        compressed_content = f.read()
                    self.send_response(200)
                    self.send_header('Last-Modified', file_last_modified)
                    self.send_header('Cache-Control', cache_control)
                    self.send_header('Expires', expiration)
                    self.send_header('Content-type',content_type)
                    if config.gzip=="on":
                        self.send_header('Content-Encoding','gzip')
                    self.send_header ("Content-Length", str(len(compressed_content)))
                    self.end_headers()
                    self.wfile.write(compressed_content)
                f.close()
                return

            return
        except IOError, e:
            logger.error(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))+"-"+str(e))


    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_POST(self):
        global rootnode
        try:
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                query=cgi.parse_multipart(self.rfile, pdict)
            self.send_response(200)
            self.end_headers()
            upfilecontent = query.get('upfile')
            print "filecontent", upfilecontent[0]
            self.wfile.write("<HTML>POST OK.<BR><BR>");
            self.wfile.write(upfilecontent[0]);

        except :
            pass

    def list_directory(self, path):

        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory");
            return None
        list.sort(lambda a, b: cmp(a.lower(), b.lower()))
        f = StringIO()
        f.write("<h2>Directory listing for %s</h2>\n" % self.path)
        f.write("<hr>\n<ul>\n")
        f.write('<li><a href="%s">Parent Directory</a>\n' % (pubutil.parent_dir(self.path)))
        for name in list:
            fullname = os.path.join(path, name)
            displayname = name = cgi.escape(name)
            if os.path.islink(fullname):
                displayname = name + "@"
            elif os.path.isdir(fullname):
                displayname = name + "/"
                name = name + os.sep
            f.write('<li><a href="%s">%s</a>\n' % (name, displayname))
        f.write("</ul>\n<hr>\n")
        f.seek(0)
        return f

    def copyfile(self, source, outputfile):
        try:
            shutil.copyfileobj(source, outputfile)
        except KeyboardInterrupt,e:
            pass

    def log_message(self, format, *args):
        open(config.Logfile, "a").write("%s - - [%s] %s\n" %(self.address_string(),self.log_date_time_string(),format%args))

#mul-processsupport.
class ProcessHTTPServer(ForkingMixIn, HTTPServer):
    pass

#mul-thread support.
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

def main(HandlerClass = ServerHandler,ServerClass = SecureHTTPServer):
    try:
        try:
            if config.ssl=="on":
                server = (bind_ip, port)
            elif config.Worker=='Multiprocess':
                server = ProcessHTTPServer((bind_ip, port), ServerHandler)
            elif config.Worker=='Multithreading':
                server = ThreadedHTTPServer((bind_ip, port), ServerHandler)
            elif config.Worker=='select':
                pass
            elif onfig.Worker=='epoll':
                pass
            else:
                server = HTTPServer((bind_ip, port), ServerHandler)
        except Exception,e:
            print str(e)
            logger.error(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))+"-"+str(e))
            return
        if config.ssl=="on":
            httpd = ServerClass(server, ServerHandler)
            httpd.serve_forever()
        else:
            server.serve_forever()
    except KeyboardInterrupt,e:
        print '^C received, shutting down server'
        if config.ssl=="on":
            httpd.socket.close()
        else:
            server.socket.close()

if __name__ == '__main__':
    #定义命令行参数
    MSG_USAGE = "Yon [-v][-h]"
    parser = OptionParser(MSG_USAGE)

    parser.add_option("-v","--version", action="store_true", dest="verbose",
            help="view yorserver version info.")

    opts, args = parser.parse_args()

    if opts.verbose:
        print "listen V1.0.1 beta."
        sys.exit();
    main()
