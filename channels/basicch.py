
# api: streamtuner2
# title: basic.ch channel
#
#
#
# Porting ST1 plugin senseless, old parsing method wasn't working any longer. Static
# realaudio archive is not available anymore.
#
# Needs manual initialisation of categories first.
#


import re
import http
from config import conf
from channels import *
from xml.sax.saxutils import unescape














# basic.ch broadcast archive
class basicch (ChannelPlugin):

    # description
    title = "basic.ch"
    module = "basicch"
    homepage = "http://www.basic.ch/"
    version = 0.3
    base = "http://basic.ch/"

    # keeps category titles->urls    
    catmap = {}
    categories = []   #"METAMIX", "reload category tree!", ["menu > channel > reload cat..."]]
    #titles = dict(listeners=False, bitrate=False)
 
    
    # read previous channel/stream data, if there is any
    def cache(self):
        ChannelPlugin.cache(self)
        # catmap
        cache = conf.load("cache/catmap_" + self.module)
        if (cache):
            self.catmap = cache
        pass
    

    # refresh category list
    def update_categories(self):

        html = http.get(self.base + "shows.cfm")

        rx_current = re.compile(r"""
            <a\shref="shows.cfm[?]showid=(\d+)">([^<>]+)</a>
            \s*<span\sclass="smalltxt">([^<>]+)</span><br
        """, re.S|re.X)


        #-- archived shows
        for uu in rx_current.findall(html):
            (id, title, genre) = uu
            self.catmap[title] = {
                "sub_url": self.base + "shows.cfm?showid=" + id,
                "title": title,
                "genre": genre,
                "id": id,
            }

        #-- populate category treee
        self.categories = [
            "METAMIX",
            "shows", [ title for title in self.catmap.keys() ]
        ]
        
        #-- keep catmap as cache-file, it's essential for redisplaying        
        self.save()
        return

    # saves .streams and .catmap
    def save(self):
        ChannelPlugin.save(self)
        conf.save("cache/catmap_" + self.module, self.catmap)


    # download links from dmoz listing
    def update_streams(self, cat, force=0):

        rx_metamix = re.compile("""
            <a\shref="(http://[^<">]+)">(METAMIX[^<]+)</a>
            \s+<span\sclass="smalltxt">([^<>]+)</span><br
        """, re.S|re.X)

        rx_playlist = re.compile("""
            <filename>(http://[^<">]+)</filename>\s*
            <artist>([^<>]+)</artist>\s*
            <title>([^<>]+)</title>
        """, re.S|re.X)

        entries = []
 
        #-- update categories first
        if not len(self.catmap):
            self.update_categories()
    
        #-- frontpage mixes
        if cat == "METAMIX":
            for uu in rx_metamix.findall(http.get(self.base)):
                (url, title, genre) = uu
                entries.append({
                    "genre": genre,
                    "title": title,
                    "url": url,
                    "format": "audio/mp3",
                    "homepage": self.homepage,
                })

        #-- pseudo entry        
        elif cat=="shows":
            entries = [{"title":"shows","homepage":self.homepage+"shows.cfm"}]
            
        #-- fetch playlist.xml
        else:
        
            # category name "Xsound & Ymusic" becomes "Xsoundandymusic"
            id = cat.replace("&", "and").replace(" ", "")
            id = id.lower().capitalize()
            
            catinfo = self.catmap.get(cat, {"id":"", "genre":""})
            
            # extract
            html = http.get(self.base + "playlist/" + id + ".xml")
            for uu in rx_playlist.findall(html):    # you know, we could parse this as proper xml
                (url, artist, title) = uu           # but hey, lazyness works too
                entries.append({
                    "url": url,
                    "title": artist,
                    "playing": title,
                    "genre": catinfo["genre"],
                    "format": "audio/mp3",
                    "homepage": self.base + "shows.cfm?showid=" + catinfo["id"],
                })

        # done    
        return entries
        










# basic.ch broadcast archive
class basicch_old_static: #(ChannelPlugin):

    # description
    title = "basic.ch"
    module = "basicch"
    homepage = "http://www.basic.ch/"
    version = 0.2
    base = "http://basic.ch/"

    # keeps category titles->urls    
    catmap = {}
 
    
    # read previous channel/stream data, if there is any
    def cache(self):
        ChannelPlugin.cache(self)
        # catmap
        cache = conf.load("cache/catmap_" + self.module)
        if (cache):
            self.catmap = cache
        pass
    

    # refresh category list
    def update_categories(self):

        html = http.get(self.base + "downtest.cfm")

        rx_current = re.compile("""
            href="javascript:openWindow.'([\w.?=\d]+)'[^>]+>
            <b>(\w+[^<>]+)</.+?
            <b>(\w+[^<>]+)</.+?
            <a\s+href="(http://[^">]+)"
        """, re.S|re.X)

        rx_archive = re.compile("""
            href="javascript:openWindow.'([\w.?=\d]+)'[^>]+>.+?
            color="000000">(\w+[^<>]+)</.+?
            color="000000">(\w+[^<>]+)</
        """, re.S|re.X)

        archive = []
        previous = []
        current = []
        
        #-- current listings with latest broadcast and archive link
        for uu in rx_current.findall(html):
            self.catmap[uu[1]] = {
                "sub_url": self.base + uu[0],
                "title": uu[1],
                "genre": uu[2],
                "url": uu[3],
            }
            archive.append(uu[1])

        #-- old listings only have archive link
        for uu in rx_archive.findall(html):
            self.catmap[uu[1]] = {
                "sub_url": self.base + uu[0],
                "genre": uu[2],
            }
            previous.append(uu[1])
        
        #-- populate category treee
        self.categories = [
            "current",
            "archive", archive,
            "previous", previous,
        ]
        
        #-- inject streams
        self.streams["current"] = [
             {
                "title": e["title"],
                "url": e["url"],
                "genre": e["genre"],
                "format": "audio/mp3",
                "listeners": 0,
                "max": 100,
                "bitrate": 0,
                "homepage": e["sub_url"],
             }
             for title,e in self.catmap.iteritems() if e.get("url")
        ]

        #-- keep catmap as cache-file, it's essential for redisplaying        
        self.save()
        return

    # saves .streams and .catmap
    def save(self):
        ChannelPlugin.save(self)
        conf.save("cache/catmap_" + self.module, self.catmap)


    # download links from dmoz listing
    def update_streams(self, cat, force=0):
    
        if not self.catmap:
            self.update_categories()
        elif cat=="current":
            self.update_categories()
            return self.streams["current"]
            
        if not self.catmap.get(cat):
            return []
    
        e = self.catmap[cat]
        html = http.get( e["sub_url"] )
        
        rx_archives = re.compile("""
            >(\d\d\.\d\d\.\d\d)</font>.+?
            href="(http://[^">]+|/ram/\w+.ram)"[^>]*>([^<>]+)</a>
            .+?   (>(\w+[^<]*)</)?
        """, re.X|re.S)
        
        entries = []
        
        for uu in rx_archives.findall(html):
            url = uu[1]
            ram = url.find("http://") < 0
            if ram:
                url = self.base + url[1:]
            entries.append({
                "title": uu[0],
                "url": url,
                "playing": uu[2],
                "genre": e["genre"],
                "format": ( "audio/x-pn-realaudio"  if  ram  else  "audio/"+uu[3].lower() ),
                "listeners": 0,
                "max": 1,
                "homepage": e["sub_url"],
            })
            
        return entries
        


