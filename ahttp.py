#
# encoding: UTF-8
# api: streamtuner2
# type: functions
# title: http download / methods
# description: http utility
# version: 1.4
#
# Utility code for HTTP requests, used by all channel plugins.
#
# Provides a http "GET" method, but also does POST and AJAX-
# simulating requests too. Hooks into mains gtk.statusbar().
# And can normalize URLs to always carry a trailing slash
# after the domain name.


from config import conf, __print__, dbg
import requests


#-- hooks to progress meter and status bar in main window
feedback = None

# Sets either text or percentage of main windows' status bar.
#
# Can either take a float parameter (e.g. 0.99 for % indicator)
# or text message. Alternatively two parameters to update both.
def progress_feedback(*args):

  # use reset values if none given
  if not args:
     args = ["", 1.0]

  # send to main win
  if feedback:
    try: [feedback(d) for d in args]
    except: pass


# prepare default query object
session = requests.Session()
# default HTTP headers for requests
session.headers.update({
    "User-Agent": "streamtuner2/2.1 (X11; Linux amd64; rv:33.0) like WinAmp/2.1",
    "Accept": "*/*",
    "Accept-Language": "en-US,en,de,es,fr,it,*;q=0.1",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Charset": "UTF-8, ISO-8859-1;q=0.5, *;q=0.1",
})


#-- Retrieve data via HTTP
#
#  Well, it says "get", but it actually does POST and AJAXish GET requests too.
#
def get(url, params={}, referer="", post=0, ajax=0, binary=0, feedback=None, content=True):
    __print__( dbg.HTTP, "GET", url, params )

    # statusbar info
    progress_feedback(url)
    
    # combine headers
    headers = {}
    if ajax:
        headers["X-Requested-With"] = "XMLHttpRequest"
    if referer:
        headers["Referer"] = (referer if referer else url)
    
    # read
    if post:
        r = session.post(url, params=params, headers=headers, timeout=7.5)
    else:    
        r = session.get(url, params=params, headers=headers, timeout=9.75)

    __print__( dbg.HTTP, r.request.headers );
    __print__( dbg.HTTP, r.headers );
            
    # finish, clean statusbar
    #progress_feedback(0.9)
    #progress_feedback("")

    # result
    __print__( dbg.INFO, "Content-Length", len(r.content) )
    if not content:
        return r
    elif binary:
        return r.content
    else:
        return r.text


#-- Append missing trailing slash to URLs
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

