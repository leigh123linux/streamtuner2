
# api: streamtuner2
# title: modarchive browser
#
#
# Just a genre browser.
#
# MOD files dodn't work with all audio players. And with the default
# download method, it'll receive a .zip archive with embeded .mod file.
# VLC in */* seems to work fine however.
#


import re
import http
from config import conf
from channels import *
from channels import __print__
from xml.sax.saxutils import unescape














# MODs
class modarchive (ChannelPlugin):

    # description
    title = "modarchive"
    module = "modarchive"
    homepage = "http://www.modarchive.org/"
    version = 0.1
    base = "http://modarchive.org/"

    # keeps category titles->urls    
    catmap = {}
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
    def update_streams(self, cat, force=0):

        url = "http://modarchive.org/index.php?query="+self.catmap[cat]+"&request=search&search_type=genre"
        html = http.get(url)
        entries = []
        
        rx_mod = re.compile("""
            href="(http://modarchive.org/data/downloads.php[?]moduleid=(\d+)[#][^"]+)"
            .*?    /formats/(\w+).png"
            .*?    title="([^">]+)">([^<>]+)</a>
            .*?    >Rated</a>\s*(\d+)
        """, re.X|re.S)
        
        for uu in rx_mod.findall(html):
            (url, id, fmt, title, file, rating) = uu
            __print__( uu )
            entries.append({
                "genre": cat,
                "url": url,
                "id": id,
                "format": self.mime_fmt(fmt) + "+zip",
                "title": title,
                "playing": file,
                "listeners": int(rating),
                "homepage": "http://modarchive.org/index.php?request=view_by_moduleid&query="+id,
            })
        
        # done    
        return entries
        

