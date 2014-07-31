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
    "User-Agent": "streamtuner2/2.1 (X11; U; Linux AMD64; en; rv:1.5.0.1) like WinAmp/2.1",
    "Accept": "*/*",
    "Accept-Language": "en-US,en,de,es,fr,it,*;q=0.1",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Charset": "UTF-8, ISO-8859-1;q=0.5, *;q=0.1",
})



#-- Retrieve data via HTTP
#
#  Well, it says "get", but it actually does POST and AJAXish GET requests too.
#
def get(url, params={}, referer="", post=0, ajax=0, binary=0, feedback=None):
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
        r = session.post(url, params=params, headers=headers)
    else:    
        r = session.get(url, params=params, headers=headers)

    __print__( dbg.HTTP, r.request.headers );
    __print__( dbg.HTTP, r.headers );
            
    # result
    #progress_feedback(0.9)
    content = (r.content if binary else r.text)
    
    # finish, clean statusbar
    progress_feedback("")
    __print__( dbg.INFO, "Content-Length", len(content) )
    return content




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




