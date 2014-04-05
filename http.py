#
# encoding: UTF-8
# api: streamtuner2
# type: functions
# title: http download / methods
# description: http utility
# version: 1.3
#
#  Provides a http GET method with gtk.statusbar() callback.
#  And a function to add trailings slashes on http URLs.
#
#  The latter code is pretty much unreadable. But let's put the
#  blame on urllib2, the most braindamaged code in the Python
#  standard library.
#
            

import urllib2
from urllib import urlencode
import config
from channels import __print__



#-- url download                            ---------------------------------------------



#-- chains to progress meter and status bar in main window
feedback = None

# sets either text or percentage, so may take two parameters
def progress_feedback(*args):

  # use reset values if none given
  if not args:
     args = ["", 1.0]

  # send to main win
  if feedback:
    try: [feedback(d) for d in args]
    except: pass




#-- GET
def get(url, maxsize=1<<19, feedback="old"):
    __print__("GET", url)

    # statusbar info
    progress_feedback(url, 0.0)
    
    # read
    content = ""
    f = urllib2.urlopen(url)
    max = 222000  # mostly it's 200K, but we don't get any real information
    read_size = 1
    
    # multiple steps
    while (read_size and len(content) < maxsize):
    
        # partial read
        add = f.read(8192)
        content = content + add
        read_size = len(add)

        # set progress meter
        progress_feedback(float(len(content)) / float(max))

    # done
    
    # clean statusbar
    progress_feedback()
        
    # fin
    __print__(len(content))
    return content





#-- fix invalid URLs
def fix_url(url):
    if url is None:
        url = ""
    if len(url):
        # remove whitespace
        url = url.strip()
        # add scheme
        if (url.find("://") < 0):
            url = "http://" + url
        # add mandatory path
        if (url.find("/", 10) < 0):
            url = url + "/"
    return url




# default HTTP headers for AJAX/POST request
default_headers = {
    "User-Agent": "streamtuner2/2.1 (X11; U; Linux AMD64; en; rv:1.5.0.1) like WinAmp/2.1 but not like Googlebot/2.1", #"Mozilla/5.0 (X11; U; Linux x86_64; de; rv:1.9.2.6) Gecko/20100628 Ubuntu/10.04 (lucid) Firefox/3.6.6",
    "Accept": "*/*;q=0.5, audio/*, url/*",
    "Accept-Language": "en-US,en,de,es,fr,it,*;q=0.1",
    "Accept-Encoding": "gzip,deflate",
    "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.1",
    "Keep-Alive": "115",
    "Connection": "keep-alive",
   #"Content-Length", "56",
   #"Cookie": "s_pers=%20s_getnr%3D1278607170446-Repeat%7C1341679170446%3B%20s_nrgvo%3DRepeat%7C1341679170447%3B; s_sess=%20s_cc%3Dtrue%3B%20s_sq%3Daolshtcst%252Caolsvc%253D%252526pid%25253Dsht%25252520%2525253A%25252520SHOUTcast%25252520Radio%25252520%2525257C%25252520Search%25252520Results%252526pidt%25253D1%252526oid%25253Dfunctiononclick%25252528event%25252529%2525257BshowMoreGenre%25252528%25252529%2525253B%2525257D%252526oidt%25253D2%252526ot%25253DDIV%3B; aolDemoChecked=1.849061",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}



# simulate ajax calls
def ajax(url, post, referer=""):
    
    # request
    headers = default_headers
    headers.update({
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": (referer if referer else url),
    })
    if type(post) == dict:
        post = urlencode(post)
    request = urllib2.Request(url, post, headers)
    
    # open url
    __print__( vars(request) )
    progress_feedback(url, 0.2)
    r = urllib2.urlopen(request)
    
    # get data
    __print__( r.info() )
    progress_feedback(0.5)
    data = r.read()
    progress_feedback()
    return data



# http://techknack.net/python-urllib2-handlers/    
from gzip import GzipFile
from StringIO import StringIO
class ContentEncodingProcessor(urllib2.BaseHandler):
  """A handler to add gzip capabilities to urllib2 requests """

  # add headers to requests
  def http_request(self, req):
    req.add_header("Accept-Encoding", "gzip, deflate")
    return req

  # decode
  def http_response(self, req, resp):
    old_resp = resp
    # gzip
    if resp.headers.get("content-encoding") == "gzip":
        gz = GzipFile(
                    fileobj=StringIO(resp.read()),
                    mode="r"
                  )
        resp = urllib2.addinfourl(gz, old_resp.headers, old_resp.url, old_resp.code)
        resp.msg = old_resp.msg
    # deflate
    if resp.headers.get("content-encoding") == "deflate":
        gz = StringIO( deflate(resp.read()) )
        resp = urllib2.addinfourl(gz, old_resp.headers, old_resp.url, old_resp.code)  # 'class to add info() and geturl() methods to an open file.'
        resp.msg = old_resp.msg
    return resp

# deflate support
import zlib
def deflate(data):   # zlib only provides the zlib compress format, not the deflate format;
  try:               # so on top of all there's this workaround:
    return zlib.decompress(data, -zlib.MAX_WBITS)
  except zlib.error:
    return zlib.decompress(data)







#-- init for later use
if urllib2:

    # config 1
    handlers = [None, None, None]
    
    # base
    handlers[0] = urllib2.HTTPHandler()
    if config.conf.debug:
        handlers[0].set_http_debuglevel(3)
        
    # content-encoding
    handlers[1] = ContentEncodingProcessor()
    
    # store cookies at runtime
    import cookielib
    cj = cookielib.CookieJar()
    handlers[2] = urllib2.HTTPCookieProcessor( cj )
    
    # inject into urllib2
    urllib2.install_opener( urllib2.build_opener(*handlers) )




# alternative function names
AJAX=ajax
POST=ajax
GET=get
URL=fix_url


