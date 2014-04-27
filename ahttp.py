#
# encoding: UTF-8
# api: streamtuner2
# type: functions
# title: http download / methods
# description: http utility
# version: 1.4
#
#  Provides a http GET method with gtk.statusbar() callback.
#  And a function to add trailings slashes on http URLs.
#
#


from compat2and3 import urllib2, urlencode, urlparse, cookielib, StringIO, xrange, PY3
from gzip import GzipFile
from config import conf, __print__, dbg
import requests
import copy



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




# default HTTP headers for AJAX/POST request
default_headers = {
    "User-Agent": "streamtuner2/2.1 (X11; U; Linux AMD64; en; rv:1.5.0.1) like WinAmp/2.1 but not like Googlebot/2.1", #"Mozilla/5.0 (X11; U; Linux x86_64; de; rv:1.9.2.6) Gecko/20100628 Ubuntu/10.04 (lucid) Firefox/3.6.6",
    "Accept": "*/*;q=0.5, audio/*, url/*",
    "Accept-Language": "en-US,en,de,es,fr,it,*;q=0.1",
    "Accept-Encoding": "gzip,deflate",
    "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.1",
    "Keep-Alive": "115",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}



#-- GET
def get(url, params={}, referer="", post=0, ajax=0, binary=0):
    __print__( dbg.HTTP, "GET", url)

    # statusbar info
    progress_feedback(url, 0.1)
    
    # combine headers
    headers = copy.copy(default_headers)
    if ajax:
        headers["X-Requested-With"] = "XMLHttpRequest"
    if referer:
        headers["Referer"] = (referer if referer else url)
    
    # read
    if post:
        __print__("POST")
        r = requests.post(url, params=params, headers=headers)
    else:    
        __print__("GET")
        r = requests.get(url, params=params, headers=headers)
        
    # result
    progress_feedback(0.9)
    content = (r.content if binary else r.text)
    
    # finish, clean statusbar
    progress_feedback()
    __print__( dbg.INFO, "Content-Length", len(content) )
    return content




# simulate ajax calls
def ajax(url, params, referer="", binary=0):
    get(url, params, referer, binary, ajax=1)



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




