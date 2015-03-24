# encoding: UTF-8
# api: streamtuner2
# title: TuneIn
# description: Online Radio, Broadcasts, Podcasts
# version: 0.1
# type: channel
# category: radio
# priority: optional
# documentation: http://opml.radiotime.com/
#
# Utilized OPML for station/podcast entries.
#
# Only radio listings are queried for now. But there are
# heaps more talk and local show entries, etc. (Would require
# more deeply nested category tree.)
#
# http://opml.radiotime.com/Browse.ashx?c=music
# http://opml.radiotime.com/Browse.ashx?id=g92
#



import re
import json
from config import conf, dbg, __print__
from channels import *
import ahttp as http
from xml.etree import ElementTree


# TuneIn radio directory
class tunein (ChannelPlugin):

    # description
    title = "TuneIn"
    module = "tunein"
    homepage = "http://tunein.com/"
    has_search = True
    listformat = "audio/x-scpls"
    titles = dict(listeners=False)
    base = "http://opml.radiotime.com/"

    categories = ["local", "60's", "70's", "80's", "90's", "Adult Contemporary", "Alternative Rock", "Ambient", "Bluegrass", "Blues", "Bollywood", "Children's Music", "Christmas", "Classic Hits", "Classic Rock", "Classical", "College Radio", "Country", "Decades", "Disco", "Easy Listening", "Eclectic", "Electronic", "Folk", "Hip Hop", "Indie", "Internet Only", "Jazz", "Live Music", "Oldies", "Polka", "Reggae", "Reggaeton", "Religious", "Rock", "Salsa", "Soul and R&B", "Spanish Music", "Specialty", "Tango", "Top 40/Pop", "World"]
    config = []
    catmap = {"local": "local", "60's": "g407", "Live Music": "g2778", "Children's Music": "c530749", "Polka": "g84", "Tango": "g3149", "Top 40/Pop": "c57943", "90's": "g2677", "Eclectic": "g78", "Decades": "c481372", "Christmas": "g375", "Reggae": "g85", "Reggaeton": "g2771", "Oldies": "c57947", "Jazz": "c57944", "Specialty": "c418831", "Hip Hop": "c57942", "College Radio": "c100000047", "Salsa": "g124", "Bollywood": "g2762", "70's": "g92", "Country": "c57940", "Classic Hits": "g2755", "Internet Only": "c417833", "Disco": "g385", "Rock": "c57951", "Soul and R&B": "c1367173", "Blues": "g106", "Classic Rock": "g54", "Alternative Rock": "c57936", "Adult Contemporary": "c57935", "Classical": "c57939", "World": "c57954", "Indie": "g2748", "Religious": "c57950", "Bluegrass": "g63", "Spanish Music": "c57945", "Easy Listening": "c10635888", "Ambient": "g2804", "80's": "g42", "Electronic": "c57941", "Folk": "g79"}


    # Retrieve cat list and map
    def update_categories(self):
        self.categories = ["local"]
        self.catmap = {"local": "local"}
        # Only music for now
        for row in self.api("Browse.ashx?c=music"):
            self.categories.append(row["text"])
            self.catmap[row["text"]] = row["guide_id"]


    # Just copy over stream URLs and station titles
    def update_streams(self, cat, search=None):
        r = []    
        for row in self.api("Browse.ashx?id=" + self.catmap[cat]):
          __print__(row)
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
        opml = http.get(self.base + method)
        x = ElementTree.fromstring(opml)
        for outline in x.findall(".//outline"):
            r.append(dict(outline.items()))
        return r


