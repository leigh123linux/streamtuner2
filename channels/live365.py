
# api: streamtunter2
# title: Live365
# description: Around 5000 categorized internet radio streams, some paid ad-free ones.
# type: channel
# category: radio
# version: 0.3
# priority: optional
#
# 2.1.2 broken,
# new URLs:
#
#   GET /cgi-bin/mini.cgi?version=3&templateid=xml&from=web&site=web&caller=&tag=web&station_name=bofbm&_=1404610275892
#      <NANOCASTER_PARAMS> (session id)
#
#   GET /play?now=59&membername=&session=1404610276-475426&tag=web&s=bofbm&d=LIVE365&r=0
#       &app_id=web%3ABROWSER&token=b99d7f579bacab06b9baa1502d53bedc-3101060080001248&AuthType=NORMAL
#       &lid=276006-deu&SaneID=178.24.130.71-1404610229579
#
#

raise Exception



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
    
        url = "http://www.live365.com/genres/%s" % cat.lower()
        html = http.get(url, feedback=self.parent.status)
        
        # Extract from JavaScript       
        rx = re.compile(r"""
                stn.set\(   " (\w+) ", \s+  " ((?:[^"\\]+|\\.)*) "\);  \s+
            """, re.X|re.I|re.S|re.M)

        # Group entries before adding them
        ls = []
        for i,g in groupby(rx.findall(html), self.group_by_station):
            row = dict(g)
            ls.append({
                "name": row["stationName"],
                "title": row["title"],
                "playing": "",
                "id": row["id"],
                "access": row["listenerAccess"],
                "status": row["status"],
                "mode": row["serverMode"],
                "rating": int(row["rating"]),
                "rating": row["ratingCount"],
                "listeners": int(row["tlh"]),
                "location": row["location"],
                "favicon": row["imgUrl"],
                "format": self.mediatype,
                "url": "urn:live365:%s:%s" % (row["id"], row["stationName"])
            })
        print ls
        return ls

    # inject session id etc. into direct audio url
    def play(self, row):
        if row.get("url"):

            # params
            id = row["id"]
            name = row["name"]

            # get session
            mini = "http://www.live365.com/cgi-bin/mini.cgi?version=3&templateid=xml&from=web&site=web" \
                 + "&caller=&tag=web&station_name=%s&_=%i111" % (name, time())
            xml = parseString(http.get(mini)).getElementsByTagName("LIVE365_PLAYER_WINDOW")[0]
            x = lambda name: xml.getElementsByTagName(name)[0].childNodes[0].data

            # mk audio url
            play =  "http://www.live365.com/play?now=0&" \
                 + x("NANOCASTER_PARAMS") \
                 + "&token=" + x("TOKEN") \
                 + "&AuthType=NORMAL&lid=276006-deu&SaneID=178.24.130.71-1406763621701"
            __print__(dbg.DATA, play)
            
            # let's see what happens
            action.action.play(play, self.mediatype, self.listformat)

            


    # itertools.groupby filter
    gi = 0
    def group_by_station(self, kv):
        if kv[0] == "stationName":
            self.gi += 1
        return self.gi

    # we can no longer cache all the things
    def cache(self):
        pass
    def save(self):
        pass


