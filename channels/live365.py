
# api: streamtunter2
# title: Live365
# description: Around 5000 categorized internet radio streams, some paid ad-free ones.
# version: 0.3
# type: channel
# category: radio
# url: http://www.live365.com/
# config: -
# priority: optional
# 
#
# We're currently extracting from the JavaScript;
#
#    stn.set("param", "value");
#
# And using a HTML5 player direct URL now:
#
#    /cgi-bin/play.pls?stationid=%s&direct=1&file=%s.pls
#


# streamtuner2 modules
from config import conf
from mygtk import mygtk
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
class live365(ChannelPlugin):

    # desc
    module = "live365"
    title = "Live365"
    homepage = "http://www.live365.com/"
    base_url = "http://www.live365.com/"
    has_search = True
    listformat = "url/http"
    mediatype = "audio/mpeg"
    has_search = False

    # content
    categories = ['Alternative', 'Blues', 'Classical', 'Country', 'Easy Listening', 'Electronic/Dance', 'Folk', 'Freeform', 'Hip-Hop/Rap', 'Inspirational', 'International', 'Jazz', 'Latin', 'Metal', 'New Age', 'Oldies', 'Pop', 'R&B/Urban', 'Reggae', 'Rock', 'Seasonal/Holiday', 'Soundtracks', 'Talk']
    current = "Alternative"
    default = "Pop"
    empty = None
    
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


    # inject session id etc. into direct audio url
    def UNUSED_play(self, row):
        if row.get("url"):

            # params
            id = row["id"]
            name = row["name"]

            # get mini.cgi station resource
            mini_url = "http://www.live365.com/cgi-bin/mini.cgi?version=3&templateid=xml&from=web&site=web" \
                 + "&caller=&tag=web&station_name=%s&_=%i111" % (name, time())
            mini_r = http.get(mini_url, content=False)
            mini_xml = parseString(mini_r.text).getElementsByTagName("LIVE365_PLAYER_WINDOW")[0]
            mini = lambda name: mini_xml.getElementsByTagName(name)[0].childNodes[0].data
            
            # authorize with play.cgi
            play_url = ""

            # mk audio url
            play =  "http://%s/play" % mini("STREAM_URL") \
                 + "?now=0&" \
                 + mini("NANOCASTER_PARAMS") \
                 + "&token=" + mini("TOKEN") \
                 + "&AuthType=NORMAL&lid=276006-deu&SaneID=178.24.130.71-1406763621701"
            
            # let's see what happens
            action.action.play(play, self.mediatype, self.listformat)


