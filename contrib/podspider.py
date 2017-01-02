# encoding: UTF-8
# api: streamtuner2
# title: PODspider
# description: lists Podcasts RSS from proprietary podspider xml database
# version: 0.0
# type: channel
# category: talk
# depends: lxml.etree, pyquery
# url: http://www.radiograbber.de/
# status: unsupported
# priority: never
# extraction-method: dom
#
# Podspider is one part of the commercial Windows "Radiograbber" software.
# A demo version is available from http://www.surfmusik.net/downloads/download.php?pid=13
# and runs under Wine.
# It downloads a "Podspiderpdb.xml.tmp_", which this plugin can display as
# streamtuner2 channel. The contents are a pre-classified list of PODcasts
# via RSS feeds. It needs some rework to strip out excessive duplicates, but
# it's nevertheless the largest overview.
#
# You can move the Podspiderpdb.xml.* into your ~/.config/streamtuner2/ dir
# after you have it.
#
# The current implementation is very inefficient. It reads the XML on every
# start. Caching it as JSON wouldn't be very wise, as it'd still be 20 MB.
#
# Untested.


import action
import ahttp
from config import conf
from channels import *
import os, os.path
from pq import pq
import lxml.etree
import uikit



# return text entry from etree list
def get(item, tag, hint=None):
    if hint != None:
        if len(item) > hint:  # hint tells us the usual position of the element
            if item[hint].tag == tag and item[hint].text:
                return item[hint].text
    for e in item:  # else we look at each
        if e.tag==tag:
            try:
                if e.text:
                    return e.text
            except:
                pass
    return ""  # empty string if nothing found


# PODlist from Radiograbber
class podspider (ChannelPlugin):

    # pi info
    module = 'podspider'
    homepage = "http://www.radiograbber.de/"
    listformat = "rss"

    # data
    config = [
    ]
    xml = None
    all = []
    streams = {}
    categories = []
    
    
    # set up
    def __init__(self, parent):
        self.xml = self.find_podspider_xml()
        if self.xml:
            print self.xml
            self.all = self.fetch()
            #self.save()
        else:
            self.warn()
        ChannelPlugin.__init__(self,parent)


    # gtk.messagebox
    def warn(self):
        uikit.msg("Podspiderpdb.xml.tmp_ couldn't be found anywhere. Install Radiograbber via Wine to create it.")


    # prevent cache file creation, as it would contain sublists and ends up being unreadable by json module
    def save(self, *a):
        pass

    
    # get podspider.xml filename
    def find_podspider_xml(self):
        wine_dir = "%s/.wine/drive_c/windows/profiles/%s/Temp/RapidSolution/" % (os.environ["HOME"], os.environ["USER"])
        fn_vari = ("Podspiderpdb.xml.tmp_", "Podspiderpdb.xml.tmp", "Podspiderpdb.xml", "podspider.xml")
        for dir in (conf.dir, wine_dir):
            if os.path.exists(dir):
                for fn in fn_vari:
                    if os.path.exists(dir +"/"+ fn):
                        return dir+fn
        pass
        

    # extract XML
    def fetch(self, f=lambda row:1):
        r = []

        # read Podspider*.xml.*
        doc = open(self.xml).read()
        doc = doc.replace(' xmlns=', ' x-ign=')

        # parse to object tree
        doc = lxml.etree.fromstring(doc)
        # step down to <channel>
        doc = doc[0]
        # skip <title> or other meta tags
        while doc[0].tag != "item":
            del doc[0]

        # each <item>
        last_url = ""
        for item in doc:

            row = {
                "title": get(item, "title", hint=0),
                "homepage": get(item, "link", hint=1),
                "playing": str(str(get(item, "description", hint=2)).replace("\n", " "))[:512],
                "favicon": get(item, "artwork", hint=4),
             #   "format": "application/rss+xml",
                "language": get(item, "language", hint=5) or "English",
             #   "lang": get(item, "iso3166", hint=6),
                "category": [e.get("category") for e in item if e.tag=="classification"],
                "listeners": int(1000.0 * float(item.get("relevance") or 0)),
            }
                
            if row["homepage"] != last_url and f(row):
                r.append(row)
                last_url = row["homepage"]
            
        return r
        

    # loads RSS and gets first entry url
    def play(self, row):
        audio = "audio/mp3"
        r = []
        for e in pq(ahttp.get(row["homepage"])).find("enclosure"):
            r.append(e.get("url"))
            audio = e.get("type")
        if r:
            action.action.play(r[0], audioformat=audio, listformat="url/direct")
        
        
        
    
    # look for categories
    def update_categories(self):
    
        # collect
        cat = {}
        for row in self.streams["all"]:

            lang = row["language"]
            if lang not in cat:
                cat[lang] = []
                
            for c in row["category"]:
                if c and c not in cat[lang]:
                    cat[lang].append(c)
                    
        # populate as two-level list
        self.categories = []
        for c,sub in cat.iteritems():
            self.categories.append(c)
            self.categories.append(sorted(sub))


    # extract     
    def update_streams(self, cat):
        r = []
    
        # ignore lang-only entries:
        if cat in self.categories:
            pass
            
        # scan through list
        else:
            for row in self.all:
                if cat in row["category"]:
                    row = dict(row) #copy
                    row["genre"] = ", ".join(row["category"])
                    del row["category"]
                    r.append(row)

        return r



