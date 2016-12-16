# encoding: UTF-8
# api: streamtuner2
# title: UbuntuUsers
# description: Static list of radio stations courtesy of the UbuntuUsers.de Wiki
# version: 0.2
# type: channel
# category: radio
# url: http://wiki.ubuntuusers.de/Internetradio/Stationen
# png:
#    iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAACJVBMVEUAAACjeUWif2/CeiGhWTvUewuhQRjPeRCfRyK1hEeWYkynQkOJREW0Dw+TICC3DAyXRES3DAzXzMewhlOsahqtaxu3DAytaxu4DAytaxqtIiKqeTyaR0eokHKk
#    h2SjayikZhmdbC+SdVaXVz2fQhufQxyhaVGjjYKsdjS2jmXBUSS2UimUXUaybBXCRA+MPx+vbR2+RhWLSCuhe0vBiEGrZUiDX0+TREWzP0CgQ0R1RUWcHByqFBSDKCifFxesMDGKUVGfFxfIsqng3tvBhz+khmDLdxCYYiDLdxGaYyKfFxfLdxGaYyKfFhbMdxCZYiCfNTW6gHzEjki+fCqdeEifZ2eWKSmVGhqTMTGXaWexkWWrbR+rbB2og1Oo
#    mYbWfhDefwjQexHXRgnXRgrziAP/jQDvhAC7jV/YTBT3SAD3SADthAT5iADngAG8kmfRTBfxRADwRADEhjm4h0nGuay0fGW/YTnAZD21ODq6PT7BQ0S9QEG2OTq2PD3KBATSAADSAADRAADSAADSAADSAADNAwPUAADUAADPAwPPDA3QDg/QDxDNAwPVAADRAAC2SUmzjIWsf3CugXLVAADJAADBgH3Hm1/eiBveiBzVAADIAADAf3rMizb+iwD9
#    iwDIAADAf3rMjDb8iwD7iwDNAwPVAADIAADAf3rMjDb7iwDOAwPXAADJAADBf3vMizb9iwD9jAC6EBC/CQm0ERLggArggAr///+cj9kUAAAAX3RSTlMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAZGJiK1ZiYlkJps315xim5xim5xh0+rQNdPq0DabnGKbnGKbnGOcY5xjnGKbnGKbnGKbN9ecYQGRiYitWYmJZCevlG38AAAABYktH
#    RLaqBwvxAAAAB3RJTUUH3wQMETciyGk1tQAAAHlJREFUGFd1jTESQUEQBbtnd+cXJxBwDiQSN3EwV5F+ZxC6hUAJlvIVJuya7ie48nWXOxVivtbRjaPRQWu6U4sBFaIMXSgGBEQ5Z2Zm1vr8qKaq9aXU/UT5avwCQG+E/gW0KWizheot39FUHT5Xjh5sBgjLbV9VT1ceE5sL4EiAe2YAAAAASUVORK5CYII=
# config: -
# priority: extra
# extraction-method: regex
#
# Short user-collected list of internet radio stations
# on UbuntuUsers.de wiki. Only provides a single category,
# but stations are grouped by country already.
#


import re
from config import *
from channels import *
import ahttp
import itertools


# UU Wiki radio list
class ubuntuusers (ChannelPlugin):

    # description
    has_search = False
    listformat = "srv"
    titles = dict(playing=False, listeners=False, bitrate=False)
    base = {
       "stations": "http://wiki.ubuntuusers.de/Internetradio/Stationen/a/export/raw/",
       "tv": "https://wiki.ubuntuusers.de/Internet-TV/Stationen/a/export/raw/",
    }
    categories = ["stations", "tv"]


    # Nope
    def update_categories(self):
        pass


    # Fetches wiki page, extracts from raw markup.
    # Which has a coherent formatting of entries like:
    #
    #   == Pi-Radio (Berlin) ==
    #   [http://www.piradio.de] {de}
    #   {{{
    #   http://ice.rosebud-media.de:8000/88vier-ogg1.ogg
    #   }}}
    #
    def update_streams(self, cat, search=None):

        # fetch page
        wiki = ahttp.get(self.base[cat], verify=False)
        f = "audio/mpeg" if cat == "stations" else "video/mp4"
        
        # split on headlines
        r = []
        for src in re.split("^==+", wiki, 0, re.M):
            r += self.join(src, f)
        return r


    # Extract individual stations
    def join(self, src, f):
    
        # regexp lists out, just one srv url per entry
        ls = re.findall(r"""
           ^\s*([\w\s.-]+)\s*==+\s+
           (?: ^\[(http[^\s\]]+) .*? \{(\w+)\} )?
           .*?
           ^\{\{\{
           .*?
           (\w+://[^"'\s\}\)\]]+)
        """, src, re.X|re.S|re.M)
        
        # pack into row list
        return [
           dict(genre=g, title=t, url=u, homepage=h, bitrate=0, listeners=0, format=f, listformat="href")
           for t,h,g,u in ls
        ]

