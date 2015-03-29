
# api: streamtuner2
# title: MODarchive
# description: Collection of module / tracker audio files (MOD, S3M, XM, etc.)
# type: channel
# version: 0.2
# url: http://www.modarchive.org/
# priority: extra
# config: -
# category: music
#
#
# Just a genre browser.
#
# MOD files dodn't work with all audio players. And with the default
# download method, it'll receive a .zip archive with embeded .mod file.
# VLC in */* seems to work fine however.
#
# Modarchive actually provides an API
# http://modarchive.org/index.php?xml-api
# (If only it wasn't XML based..)
#


import re
import ahttp as http
from config import conf
from channels import *
from config import __print__, dbg














# MODs
class modarchive (ChannelPlugin):

    # description
    title = "modarchive"
    module = "modarchive"
    homepage = "http://www.modarchive.org/"
    base = "http://modarchive.org/"
    titles = dict(genre="Genre", title="Song", playing="File", listeners="Rating", bitrate=0)

    # keeps category titles->urls    
    catmap = {"Chiptune": "54", "Electronic - Ambient": "2", "Electronic - Other": "100", "Rock (general)": "13", "Trance - Hard": "64", "Swing": "75", "Rock - Soft": "15", "R &amp; B": "26", "Big Band": "74", "Ska": "24", "Electronic - Rave": "65", "Electronic - Progressive": "11", "Piano": "59", "Comedy": "45", "Christmas": "72", "Chillout": "106", "Reggae": "27", "Electronic - Industrial": "34", "Grunge": "103", "Medieval": "28", "Demo Style": "55", "Orchestral": "50", "Soundtrack": "43", "Electronic - Jungle": "60", "Fusion": "102", "Electronic - IDM": "99", "Ballad": "56", "Country": "18", "World": "42", "Jazz - Modern": "31", "Video Game": "8", "Funk": "32", "Electronic - Drum &amp; Bass": "6", "Alternative": "48", "Electronic - Minimal": "101", "Electronic - Gabber": "40", "Vocal Montage": "76", "Metal (general)": "36", "Electronic - Breakbeat": "9", "Soul": "25", "Electronic (general)": "1", "Punk": "35", "Pop - Synth": "61", "Electronic - Dance": "3", "Pop (general)": "12", "Trance - Progressive": "85", "Trance (general)": "71", "Disco": "58", "Electronic - House": "10", "Experimental": "46", "Trance - Goa": "66", "Rock - Hard": "14", "Trance - Dream": "67", "Spiritual": "47", "Metal - Extreme": "37", "Jazz (general)": "29", "Trance - Tribal": "70", "Classical": "20", "Hip-Hop": "22", "Bluegrass": "105", "Halloween": "82", "Jazz - Acid": "30", "Easy Listening": "107", "New Age": "44", "Fantasy": "52", "Blues": "19", "Other": "41", "Trance - Acid": "63", "Gothic": "38", "Electronic - Hardcore": "39", "One Hour Compo": "53", "Pop - Soft": "62", "Electronic - Techno": "7", "Religious": "49", "Folk": "21"}
    categories = []
 
    
    

    # refresh category list
    def update_categories(self):

        html = http.get("http://modarchive.org/index.php?request=view_genres")

        rx_current = re.compile(r"""
            >\s+(\w[^<>]+)\s+</h1>  |
            <a\s[^>]+query=(\d+)&[^>]+>(\w[^<]+)</a>
        """, re.S|re.X)


        #-- archived shows
        sub = []
        self.categories = []
        for uu in rx_current.findall(html):
            (main, id, subname) = uu
            if main:
                if sub:
                    self.categories.append(sub)
                sub = []
                self.categories.append(main)
            else:
                sub.append(subname)
                self.catmap[subname] = id
        #
        
        #-- keep catmap as cache-file, it's essential for redisplaying        
        self.save()
        return


    # saves .streams and .catmap
    def save(self):
        ChannelPlugin.save(self)
        conf.save("cache/catmap_" + self.module, self.catmap)


    # read previous channel/stream data, if there is any
    def cache(self):
        ChannelPlugin.cache(self)
        # catmap
        cache = conf.load("cache/catmap_" + self.module)
        if (cache):
            self.catmap = cache
        pass


    # download links from dmoz listing
    def update_streams(self, cat):

        url = "http://modarchive.org/index.php"
        params = dict(query=self.catmap[cat], request="search", search_type="genre")
        html = http.get(url, params)
        entries = []
        
        rx_mod = re.compile("""
            href="(http://api\.modarchive\.org/downloads\.php[?]moduleid=(\d+)[#][^"]+)"
            .*?    /formats/(\w+)\.png"
            .*?    title="([^">]+)">([^<>]+)</a>
            .*?    >(?:Rated|Unrated)</a>\s*(\d*)
        """, re.X|re.S)
        
        for uu in rx_mod.findall(html):
            (url, id, fmt, title, file, rating) = uu
            #__print__( dbg.DATA, uu )
            entries.append({
                "genre": cat,
                "url": url,
                "id": id,
                "format": self.mime_fmt(fmt) + "+zip",
                "title": title,
                "playing": file,
                "listeners": int(rating if rating else 0),
                "homepage": "http://modarchive.org/index.php?request=view_by_moduleid&query="+id,
            })
        
        # done    
        return entries
        

