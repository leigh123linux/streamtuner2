
# api: streamtunter2
# title: Live365
# description: Around 5000 categorized internet radio streams, some paid ad-free ones.
# version: 0.3
# type: channel
# category: radio
# url: http://www.live365.com/
# config: -
# priority: optional
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAzlJREFUOI1lk0tMXGUUx3/fvTP3zgyPGR5SKIQODdDGEtoCJdFopA9SJTFMjInGaJDEulWTGg2JApqoO+PShaAmdVEXQAxoCtgKNjYFWrQgMD6KDAylkde8Lnfunfu5IJii
#   Z3POSc7//M/i/AT/ichrbUE1NyckfN5WV0kpUjpYS4s4sdhAZnOrP9jTv/jgvHiw+ftSb5f2UEGnfuQYCIG9fg8pJa5AIdJIEf9hhNTkze5gz9ddexrXXrE1+E2v7/TZl9lcx/hxBCu5DUikzCDTFjiSrMYnyGp8vPOuaR+quNTXDqACRLve7cp5suV1YaSwpyewYts4
#   dgbhcuGprkFoOnZ0BTM8j9A85J576sQr96Pik4Xfr6l/nj8b9D7yaJ8rz8/O2FWctEXGTKP6/eQ924ZeUY21sowViSDTaaylJbSKSrCsplfNnS9cMiNC3ppayEhyX2wHAdt9l8k+cx6h68SGhzCmJ9CP1hAIPYdjGGQ21lF82cSHR0MuxzBbFU0js7FOOhzGU1tL9ulm
#   3IUHAMhtbsFbc5yd2TsAJEavIC0b78k6sGWrohUfxJybJzE8gpoXAMBeWwPAWAqTvD6Ou6QULXgYgOwzzRi3bpMcv47n4WMo6B4yWzHM+TDGz7suyN2k5x9Er6zCSSSIDQ6x+tabKD4f7tIynHgcK3oPZf3mDfSqStSCQnZmf91V2hmiFy9iLixgLa+wMTmIOTeHq6gY
#   AOuvCHp1NcmFMK6ERx0wEvGmou5OtLJSrJUV7n/wEWY4TOLKCHsnlfV8hq+hgc3eL4l9O4y7sYGErgyIofqaYEHdqbvljzWx+v6HaI5ERSCE2Pen0pE4Wh22NUXxOx1Exq+yOTVRobRMzSxGZqa6zUI/3uefYcOrsq0JEqokhcRAkhSSuBti+gw5F9qxSw+wuRrpbp6e
#   XVQBLi+vXatfngseeuGlE/5TjUQX7pCSNoZbkNIUUrqCWRCg8u0OKC9h/L2Oz0OjP73xP5g+PXeyq+R4Q+eR5qfJ8maz/ds8AIGqoySNBMs3xvhjbKT7wvfT/8K0bwHAxy31QcWRIaA1v/ww3kA+0V8mAQb8+UX9bV99tw/nfwAe2WTAAcikxQAAAABJRU5ErkJggg==
# 
# Live365 lists around 5000 radio stations. Some are paid
# entries and require a logon. This plugins tries to filter
# thoise out.


# streamtuner2 modules
from config import conf
from uikit import uikit
import ahttp as http
from channels import *
from config import __print__, dbg
import action

# python modules
import re
import xml.dom.minidom
from xml.sax.saxutils import unescape as entity_decode, escape as xmlentities
import gtk
import copy
import urllib
from itertools import groupby
from time import time
from xml.dom.minidom import parseString


# channel live365
#
# We're currently extracting from the JavaScript;
#
#    stn.set("param", "value");
#
# And using a HTML5 player direct URL now:
#
#    /cgi-bin/play.pls?stationid=%s&direct=1&file=%s.pls
#
class live365(ChannelPlugin):

    # control attributes
    base_url = "http://www.live365.com/"
    has_search = True
    listformat = "pls"
    mediatype = "audio/mpeg"
    has_search = False

    # content
    categories = ['Alternative', 'Blues', 'Classical', 'Country', 'Easy Listening', 'Electronic/Dance', 'Folk', 'Freeform', 'Hip-Hop/Rap', 'Inspirational', 'International', 'Jazz', 'Latin', 'Metal', 'New Age', 'Oldies', 'Pop', 'R&B/Urban', 'Reggae', 'Rock', 'Seasonal/Holiday', 'Soundtracks', 'Talk']
    
    # redefine
    streams = {}
    

    def __init__(self, parent=None):
    
        # override datamap fields  //@todo: might need a cleaner method, also: do we really want the stream data in channels to be different/incompatible?
        self.datamap = copy.deepcopy(self.datamap)
        self.datamap[5][0] = "Rating"
        self.datamap[5][2][0] = "rating"
        
        # superclass
        ChannelPlugin.__init__(self, parent)


    # fixed for now
    def update_categories(self):
        pass


    # extract stream infos
    def update_streams(self, cat):

        # Retrieve genere index pages    
        html = ""
        for i in [1, 17, 33, 49]:
            url = "http://www.live365.com/cgi-bin/directory.cgi?first=%i&site=web&mode=3&genre=%s&charset=UTF-8&target=content" % (i, cat.lower())
            html += http.get(url, feedback=self.parent.status)
        
        # Extract from JavaScript       
        rx = re.compile(r"""
                stn.set\(   " (\w+) ", \s+  " ((?:[^"\\]+|\\.)*) "\);  \s+
            """, re.X|re.I|re.S|re.M)

        # Group entries before adding them
        ls = []
        for i,row in groupby(rx.findall(html), self.group_by_station):
            row = dict(row)
            ls.append({
                "status": (None if row["listenerAccess"] == "PUBLIC" else gtk.STOCK_STOP),
                "deleted": row["status"] != "OK",
                "name": row["stationName"],
                "title": row["title"],
                "playing": "n/a",
                "id": row["id"],
                "access": row["listenerAccess"],
                "status": row["status"],
                "mode": row["serverMode"],
                "rating": int(row["rating"]),
                #"rating": row["ratingCount"],
                "listeners": int(row["tlh"]),
                "location": row["location"],
                "favicon": row["imgUrl"],
                "format": self.mediatype,
                "url": "%scgi-bin/play.pls?stationid=%s&direct=1&file=%s.pls" % (self.base_url, row["id"], row["stationName"])
            })
        return ls

    # itertools.groupby filter
    gi = 0
    def group_by_station(self, kv):
        if kv[0] == "stationName":
            self.gi += 1
        return self.gi



