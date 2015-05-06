# encoding: UTF-8
# api: streamtuner2
# title: Magnatune
# description: Independent and user-friendly radio label
# url: http://magnatune.com/
# version: 0.1
# docs: https://magnatune.com/info/api
# type: channel
# category: collection
# config: -
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABIAAAASBAMAAACk4JNkAAAAMFBMVEUAW5kAY6ACa6MVd6sWgLE2irdHmcBdpslvrsuEudWY
#   xdmiy9+21+fO4u7z+fz9//wtPja+AAAAAWJLR0QAiAUdSAAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB98FBhQ2G9ph
#   h8MAAACySURBVAjXY/j//22rccS9//8Z/v9NVAl1ErsPZB0W2/vudqLPf4a/Ruv+lf9/qXyf4ZnU+79O//9Pime4mPf/j9H/
#   /1+tGYr2//tj9O/dH3EGl/vHzhr9yf1nyqD6vqjW6AfXu2AgKwnIkvoXDJSFsMyAOkCyUkAdF/MTaw1/cAFNeSZ1/d6sv3VN
#   cQx/neb///f/BdC2/0dEz717E2QLclWycKihGchV/99Mc8k89/8/AD9dZbS2m1Y9AAAAAElFTkSuQmCC
# priority: extra
# 
# Magnatune is a label for independent music. It provides
# free access to a partial section of its reportoire as MP3.
# Using paid subscriptions, all albums are available in
# higher quality Ogg Vorbis or FLAC encodings however.
#
# You can listen to all albums and tracks freely. They're
# just interspersed with short "magnatune" voiceunders.
#
# For now this plugin just fetches the small highested
# ranked album list. Just an excerpt. The huge album list
# is a 70 MiB download.
#
# src:
#   http://magnatune.com/info/shoutcast/
#   http://magnatune.com/genres/m3u/ranked_all.xspf (current)
#   http://he3.magnatune.com/info/song_info_csv.gz
#   http://he3.magnatune.com/info/album_info.xml


import re
from config import *
from channels import *
import ahttp
import action
from compat2and3 import urlencode


# Magnatune
class magnatune (ChannelPlugin):

    # control flags
    has_search = False
    listformat = "srv"
    audioformat = "audio/mpeg"
    titles = dict(listeners=False, bitrate=False, playing=False)
    categories = ["radios", "albums"]


    # static
    def update_categories(self):
        pass


    # Just one list to fetch
    def update_streams(self, cat, search=None):

        # Radios are just rotating playlists
        if cat == "radios":
            return [
                { "genre": "classical", "title": "Classical: renaissance and baroque", "url": "http://sc2.magnatune.com:8000/listen.pls", "listformat": "pls" },
                { "genre": "electronic", "title": "Electronica: downtempo, techno & trance", "url": "http://sc2.magnatune.com:8002/listen.pls", "listformat": "pls" },
                { "genre": "metal", "title": "Metal and Punk", "url": "http://sc2.magnatune.com:8004/listen.pls", "listformat": "pls" },
                { "genre": "new age", "title": "New Age", "url": "http://sc2.magnatune.com:8006/listen.pls", "listformat": "pls" },
                { "genre": "rock", "title": "Rock", "url": "http://sc2.magnatune.com:8008/listen.pls", "listformat": "pls" },
                { "genre": "world", "title": "World Music: Indian, Celtic, Arabic, Baltic...", "url": "http://sc2.magnatune.com:8010/listen.pls", "listformat": "pls" },
                { "genre": "./.", "title": "Free song download of the day", "url": "none:", "homepage": "http://magnatune.com/today/", "listformat": "href" },
            ]

        # Short album list
        return self.fetch_ranked_xspf()            

    
    # Broken playlist file
    def fetch_ranked_xspf(self):
        xspf = ahttp.get("http://magnatune.com/genres/m3u/ranked_all.xspf")
        xspf = re.sub("/([^</>]+)\.mp3</location>", self.urlenc, xspf)
        cnv = action.extract_playlist(text=xspf)
        rows = [
           dict(title=unhtml(r["playing"]), url=r["url"], homepage=r["homepage"], genre="album")
           for r in cnv.rows("xspf")
        ]
        return rows

    # Custom URL patching
    def urlenc(self, m):
        u = str(m.group(1))
        u = u.replace(" ", "%20")
        return "/" + u + ".mp3</location>"


