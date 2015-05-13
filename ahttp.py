#
# encoding: UTF-8
# api: streamtuner2
# type: functions
# title: http download / methods
# description: http utility
# version: 1.5
#
# Utility code for HTTP requests, used by all channel plugins.
#
# Provides a http "GET" method, but also does POST and AJAX-
# simulating requests too. Hooks into mains gtk.statusbar().
# And can normalize URLs to always carry a trailing slash
# after the domain name.


from config import *
import requests


#-- hooks to progress meter and status bar in main window
feedback = None

# Sets either text or percentage of main windows' status bar.
#
# Can either take a float parameter (e.g. 0.99 for % indicator)
# or text message. Alternatively two parameters to update both.
def progress_feedback(*args, **kwargs):

  # use reset values if none given
  if not args:
     args = ["", 1.0]
  timeout = kwargs.get("timeout", 50)

  # send to main win
  if feedback:
    try: [feedback(d, timeout=timeout) for d in args]
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
def get(
       url, params={}, referer="", post=0, ajax=0,
       binary=0, content=True, encoding=None, verify=False,
       statusmsg=None, timeout=9.25, quieter=0
    ):

    # statusbar info
    if not quieter:
        progress_feedback(url, timeout=timeout/1.5)
    
    # combine headers
    headers = {}
    if ajax:
        headers["X-Requested-With"] = "XMLHttpRequest"
    if referer:
        headers["Referer"] = (referer if referer else url)

#ifdef BLD_DEBUG
#srcout    raise Exception("Simulated HTTP error")
#endif
    
    # read
    if post:
        log.HTTP("POST", url, params)
        r = session.post(url, params=params, headers=headers, timeout=timeout)
    else:    
        log.HTTP("GET"+(" AJAX" if ajax else ""), url, params )
        r = session.get(url, params=params, headers=headers, verify=verify, timeout=timeout)

    if not quieter:
        log.HTTP(">>>", r.request.headers );
        log.HTTP("<<<", r.headers );
            
    # result
    log.INFO("Content-Length", len(r.content) )
    statusmsg and progress_feedback(statusmsg)
    if not content:
        return r
    elif binary:
        r = r.content
    else:
        # Manually decode charset
        if encoding:
            r.encoding = encoding
            r = r.content.decode(encoding, errors='replace')
        # See requests isse #2359, automatic charset detection can be awfully slow
        else:
            r = r.text
    # clean statusbar
    statusmsg and progress_feedback()
    return r


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

