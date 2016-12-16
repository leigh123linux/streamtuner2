# encoding: UTF-8
# api: streamtuner2
# title: TuneIn
# description: Online Radio, Broadcasts, Podcasts per RadioTime API
# version: 0.3
# type: channel
# category: radio
# url: http://tunein.com/
# config:
#   { name: radiotime_group, value: music, type: select, select: music|genres, description: Catalogue type as categories. (→ Reload Category Tree) }
#   { name: radiotime_maxpages, value: 10, type: int, description: Maximum number of pages. }
# priority: default
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAbpJREFUOI2Nkk9PE1EUxc+ZuTMIaP+KqClxx4dA0jRVgwFM/JPIRv0CunDnxsQ1G4NGvgD7LkiExG5IDHFhDDEmblwRQJG2AVuwMNOZd91QAuUR
#   e1bvnnfeLzf3PsKioq6Dtf25xsq3Kdf3gkxh9OUis29tWcdm9iPxuvHl62MNQz/a+3uhVl56M647d7sGHOxU8hpFR7Uag9+l+UddAySdWuv0soWR710DXOj93mtDWxQBRTBwq7AcZfte2bK0mQCQ11X0I5lzEW2858BZMXBkZWkGqk8Atk7c
#   mBhqVCWV2E0MDz9dYLo8ptWbwdrP2aC6nSYhIOck2PiVdDwvfXxox9WqVAcPVtc/jOkm68uf56M/9T4AoAhMq5V06NCc2d+hNAzhwBttPz5q36FxchOT0xT5HwMEvRO1CHITk9MEgHHdfED4z4La9nmQqiY2dNywHY6b++d6h65OhVvVElw3
#   7rmY2VOE7xZ5pWTdwh2t52NEzwEeQtgTIXhR5uUfnVlr783m7vXGx0/32oOlCC7dLs4COAWwfiTH9+PTrrFnbWan6LkA/HLXAFckaJ+9bKYyeKP4cIEpK/wffVOh5FvT8j8AAAAASUVORK5CYII=
# documentation: http://opml.radiotime.com/
# extraction-method: dom
#
# RadioTime API uses OPML for station/podcast entries.
#
# Only radio listings are queried for now. But there are
# heaps more talk and local show entries, etc. (Would require
# more deeply nested category tree.)
#


import re
import json
from config import *
from channels import *
import ahttp
from xml.etree import ElementTree


# TuneIn radio directory
class tunein (ChannelPlugin):

    # control flags
    has_search = False
    listformat = "pls"
    titles = dict(listeners=False)
    base = "http://opml.radiotime.com/"

    categories = ["local", "60's", "70's", "80's", "90's", "Adult Contemporary", "Alternative Rock", "Ambient", "Bluegrass", "Blues", "Bollywood", "Children's Music", "Christmas", "Classic Hits", "Classic Rock", "Classical", "College Radio", "Country", "Decades", "Disco", "Easy Listening", "Eclectic", "Electronic", "Folk", "Hip Hop", "Indie", "Internet Only", "Jazz", "Live Music", "Oldies", "Polka", "Reggae", "Reggaeton", "Religious", "Rock", "Salsa", "Soul and R&B", "Spanish Music", "Specialty", "Tango", "Top 40/Pop", "World"]
    catmap = {"60's": "g407", "Live Music": "g2778", "Children's Music": "c530749", "Polka": "g84", "Tango": "g3149", "Top 40/Pop": "c57943", "90's": "g2677", "Eclectic": "g78", "Decades": "c481372", "Christmas": "g375", "Reggae": "g85", "Reggaeton": "g2771", "Oldies": "c57947", "Jazz": "c57944", "Specialty": "c418831", "Hip Hop": "c57942", "College Radio": "c100000047", "Salsa": "g124", "Bollywood": "g2762", "70's": "g92", "Country": "c57940", "Classic Hits": "g2755", "Internet Only": "c417833", "Disco": "g385", "Rock": "c57951", "Soul and R&B": "c1367173", "Blues": "g106", "Classic Rock": "g54", "Alternative Rock": "c57936", "Adult Contemporary": "c57935", "Classical": "c57939", "World": "c57954", "Indie": "g2748", "Religious": "c57950", "Bluegrass": "g63", "Spanish Music": "c57945", "Easy Listening": "c10635888", "Ambient": "g2804", "80's": "g42", "Electronic": "c57941", "Folk": "g79"}
    groupmap = {
       "music":  "Browse.ashx?c=music",
       "genres": "Describe.ashx?c=genres",
    }


    # Retrieve cat list and map
    def update_categories(self):
        self.categories = ["local"]
        self.catmap = {}
        # Only music for now
        for row in self.api(self.groupmap[conf.radiotime_group]):
            self.categories.append(row["text"])
            self.catmap[row["text"]] = row["guide_id"]


    # Just copy over stream URLs and station titles
    def update_streams(self, cat, search=None):
        r = []
        # catmap only set for genres, not for category groups like "local"    
        if search:
            url = "Search.ashx?query=%s&formats=ogg,aac,mp3" % urlencode(search) 
        elif cat in self.catmap and cat != "local":
            url = "Browse.ashx?id=%s" % self.catmap[cat]
        else:
            url = "Browse.ashx?c=%s" % cat
        # fetch
        for row in self.api(url):
          if "URL" in row and "bitrate" in row and "subtext" in row:
            r.append({
               "genre": "radio",
               "title": row["text"],
               "url": row["URL"],
               "bitrate": int(row.get("bitrate", 0)),
               "playing": row.get("subtext", ""),
               "favicon": row.get("image", None),
            })
        return r


    # Fetch OPML, convert outline elements to dicts
    def api(self, method):
        r = []
        # fetch API page
        next = self.base + method
        max = int(conf.radiotime_maxpages)
        while next:
            opml = ahttp.get(next)
            next = None
            x = ElementTree.fromstring(opml)
            # append entries
            for outline in x.findall(".//outline"):
                outline = dict(outline.items())
                # additional pages
                if "key" in outline and outline["key"] == "nextStations":
                    if len(r) < conf.max_streams and max > 0:
                        next = outline["URL"]
                        max = max - 1
                else:
                    r.append(outline)
        return r


