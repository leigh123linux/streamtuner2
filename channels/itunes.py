# encoding: UTF-8
# api: streamtuner2
# title: iTunes Radio
# description: iTunes unsorted station list via RoliSoft Radio Playlist caching webservice.
# version: 0.1
# type: channel
# category: radio
# url: http://www.itunes.com?
# priority: optional
# config: -
# documentation: http://lab.rolisoft.net/playlists.html
#
#
# API provides pre-parsed radio station playlists for various services
#
#  → Shoutcast
#  → Xiph/ICEcast
#  → Tunein
#  → iTunes
#  → FilterMusic
#  → SomaFM
#  → AccuRadio
#  → BBC
#
# In this module only iTunes will be queried for now.
#

import re
from config import conf, dbg, __print__
from channels import *
import ahttp as http


# Surfmusik sharing site
class itunes (ChannelPlugin):

    # description
    title = "iTunes RS"
    module = "itunes"
    #module = "rs_playlist"
    homepage = "http://www.itunes.com?"
    has_search = False
    listformat = "audio/x-scpls"
    titles = dict(listeners=False, bitrate=False, playing=False)

    categories = [
        "Adult Contemporary",
        "Alternative Rock",
        "Ambient",
        "Blues",
        "Classic Rock",
        "Classical",
        "College",
        "Comedy",
        "Country",
        "Eclectic",
        "Electronica",
        "Golden Oldies",
        "Hard Rock",
        "Hip Hop",
        "International",
        "Jazz",
        "News",
        "Raggae",
        "Religious",
        "RnB",
        "Sports Radio",
        "Top 40",
        "'70s Retro",
        "'80s Flashback",
        "'90s Hits",
    ]
    
    base = "http://lab.rolisoft.net/playlists/itunes.php"
    #base = "http://aws-eu.rolisoft.net/playlists/itunes.php"
    #base = "http://aws-us.rolisoft.net/playlists/itunes.php"
    

    # static list for iTunes
    def update_categories(self):
        pass

    # Just copy over stream URLs and station titles
    def update_streams(self, cat):
    
        m3u = http.get(self.base, {"category": cat.lower()})
        if len(m3u) < 256:
            __print__(dbg.ERR, m3u)
        
        rx_m3u = re.compile(r"""
            ^File(\d+)\s*=\s*(http://[^\s]+)\s*$\s*
            ^Title\1\s*=\s*([^\r\n]+)\s*$\s*
        """, re.M|re.I|re.X)

        r = []
        for e in rx_m3u.findall(m3u):
            r.append(dict(
                genre = cat,
                url = e[1],
                title = e[2],
                format = "audio/mpeg",
                playing = "",
            ))

        return r

