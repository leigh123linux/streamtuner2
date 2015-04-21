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
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAA3lJREFUOI1Fk01MHGUAht9vZnZml53dhcJSYIEVt8Tu1qbQRNI0wKGxiUk1HBpjbzUmatWUCzHe1Kjx0KQH5WA08aAXYzTRpKnSFG2kpB4ILEstP1skwC50f1nmf3Zmvvk8aOtzf05PHoL/YIyhWtpD
#   JBKRlpZzp3YK+6OqpqcAIBaN/N2f6L57evhUTtM0p7O797EGAgC6puCNtyYx+c6b6YXsX1M75cMXHSLFebGFI4TAdy1fZM1qf2fsxnNDJ65/9fW369OfXUNLOAoy88tNFEpVDPQnRn+bX/qiZErPdiTTCMltgBAAYwClLpqGAmV/A52idf/c2aErxf3yvc72VpC5ubuQRC714425H+4/wnBfZgQk
#   FAYlHIIBICoBMREQGMXmIw2F/AoyHe7SxQvjLzddusWNjY2Sheza23eWy8N+LIWKG0DNojjTS/DqmVa8Pt6N184lMTHSA9MBHHkAf+Sqpxdza1fGx8aIcG/+91R2tfjSniaD90PQPQFhniHdJaFNYlA1DaUDBgEEikugUAlFLYzsanHiz/k7Xwr7pdrwdsno1WkbKiaD6HHwgxx2azq+yevYhQxd
#   dXG5x4HhARWTQfNC2C41+vbKtSFB0Yxe3WYSJSI0h0FiHMKcgEOPYjGcgCVHQKHCovuwXAbV8uFBgG4zSdPMhOBT6gUCHCM8AQQOPs/BA2BaJrggQ9ixkOEP0cq7oNR/0j7AE0apRwUCfyveKplczYkQz0Ofp2IkREENDdS1McbtYCJuw3QA13VBqAvOtxFvkwwCusVpykE2lZDzEcEErx5gIl7F
#   +aMNUEsDMxwUKwaWHpbwa66GAwuAqSMqmHi6R95QGvVlfubWrLaSXZAdp/n8bs3jRGbDdmwsqjLUcBcaXBS5egBrShC2aoBWCxhJUu9EMnJ9aurdWf5QUdGol/KDT3U/Yzet9FIliDW7A0rLUXAEYE0HjumiWT+EVy7gZLuGs+noT3s7+U9v3Z61CAB8Pj2NzfzGwJGu5LX1Mp1YrQcCOhcDxBAY
#   Y4BtQPYayMSpk+4Rf25UCu+ljg1uT169+u9MAPDhB+9jdfXBkeOZk6+4JHSpbrK03oQMALIIvT2MNYHZ360/WPk+nc40Pvr4k/9vfExQEmE3HXLhhfMdqWODx4Mt4QQAWKZR3Np8uH5z5nZdEgOs6bhPnH8APR+/sJEZQ8oAAAAASUVORK5CYII=
# documentation: http://lab.rolisoft.net/playlists.html
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
from config import *
from channels import *
import ahttp as http


# Surfmusik sharing site
class itunes (ChannelPlugin):

    # control attribues
    has_search = False
    listformat = "pls"
    titles = dict(listeners=False, bitrate=False, playing=False)
    base = "http://lab.rolisoft.net/playlists/itunes.php"
    #base = "http://aws-eu.rolisoft.net/playlists/itunes.php"
    #base = "http://aws-us.rolisoft.net/playlists/itunes.php"

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
    

    # static list for iTunes
    def update_categories(self):
        pass

    # Just copy over stream URLs and station titles
    def update_streams(self, cat):
    
        m3u = http.get(self.base, {"category": cat.lower()})
        if len(m3u) < 256:
            log.ERR(m3u)
        
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

