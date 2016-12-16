# api: streamtuner2
# title: Soundcloud streams
# description: Convert soundcloud links from reddit to streamable tracks
# version: 0.3
# type: filter
# category: audio
# depends: python:soundcloud, action >= 1.1, reddit >= 0.8
# priority: rare
#
# Hooks into action.play() function to convert soundcloud URLs
# to track/streaming address.  Disables the reddit filter for
# walled gardens, and overrides any custom player configured
# for "audio/soundcloud" in settings.


import copy
import re
import soundcloud
from config import *
import ahttp
import action

fmt = "audio/soundcloud"
rx_url = re.compile("^https?://(www\.)?soundcloud\.com/[\w-]+/[\w-]+$")
conn = None

        
# API connect
def client():
    global conn
    if not conn:
        conn = soundcloud.Client(client_id="f0aea6e0484043f6638cb5bf35d43312")
    return conn

# Capture play events for faux MIME type
def sndcl_convert(row={}, audioformat="audio/mpeg", source="pls", assoc={}):
    if audioformat==fmt or rx_url.match(url):

        # find streaming address
        try:
            url = row["url"]
            log.DATA_CONVERT_SOUNDCLOUD(url)
            track = client().get('/resolve', url=url)
            track_str = "/tracks/{}/stream".format(track.id)
            url = client().get(track_str, allow_redirects=False).location

            # override attributes
            row = copy.copy(row)  # Throw away afterwards; tokens time out.
            row["url"] = url
            row["format"] = "audio/mpeg"
            audioformat = "audio/mpeg"
            source = "srv"

        except Exception as e:
            log.ERR_SOUNDCLOUD("URL resolving failed:", e)
            
            # let web browser run
            audioformat = "url/http"
    
    # let primary handler take over
    if audioformat != fmt:
        return action.run_fmt_url(row, audioformat, source, assoc)


# Hook up custom action.handler for soundcloud URLs
#
# Still somewhat hodgepodge. The action module just lets .play() params
# rewrite by above handler. Should turn faux "audio/soundcloud" URL into
# plain/longwinded MP3 streaming address.
#
# Would need more generalized processing of custom URL schemes. But so
# far only the reddit module uses them anyway.
#
class url_soundcloud(object):
    module = 'url_soundcloud'

    # override action.play() with wrapper
    def __init__(self, parent, *a, **kw):
        conf.play[fmt] = "false / convert"
        #conf.filter_walledgardens = False
        action.handler[fmt] = sndcl_convert

