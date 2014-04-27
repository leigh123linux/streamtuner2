
# api: streamtuner2
# title: punkcast listing
#
#
# Disables itself per default.
# ST1 looked prettier with random images within.
#


import re
import ahttp as http
from config import conf
import action
from channels import *
from config import __print__, dbg





# disable plugin per default
if "punkcast" not in vars(conf): 
    conf.plugins["punkcast"] = 0









# basic.ch broadcast archive
class punkcast (ChannelPlugin):

    # description
    title = "punkcast"
    module = "punkcast"
    homepage = "http://www.punkcast.com/"
    version = 0.1

    # keeps category titles->urls    
    catmap = {}
    categories = ["list"]
    default = "list"
    current = "list"
 


    # don't do anything
    def update_categories(self):
        pass


    # get list
    def update_streams(self, cat, force=0):

        rx_link = re.compile("""
            <a\shref="(http://punkcast.com/(\d+)/index.html)">
            \s+<img[^>]+ALT="([^<">]+)"
        """, re.S|re.X)

        entries = []
 
        #-- all from frontpage
        for uu in rx_link.findall(http.get(self.homepage)):
            (homepage, id, title) = uu
            entries.append({
                    "genre": "?",
                    "title": title,
                    "playing": "PUNKCAST #"+id,
                    "format": "audio/mp3",
                    "homepage": homepage,
            })

        # done    
        return entries


    # special handler for play
    def play(self, row):
    
        rx_sound = re.compile("""(http://[^"<>]+[.](mp3|ogg|m3u|pls|ram))""")
        html = http.get(row["homepage"])
        
        # look up ANY audio url
        for uu in rx_sound.findall(html):
            __print__( dbg.DATA, uu )
            (url, fmt) = uu
            action.action.play(url, self.mime_fmt(fmt), "url/direct")
            return
        
        # or just open webpage
        action.action.browser(row["homepage"])
            
        





