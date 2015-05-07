# encoding: UTF-8
# api: streamtuner2
# title: WindowsMedia
# description: 
# url: http://windowsmedia.com/
# version: 0.3
# type: channel
# category: radio
# config:
#   { name: windowsmedia_culture, type: select, value: en-gb, select: "en-gb|de-de|da-dk|cs-cz|es-es|fr-fr|it-it|nl-nl|pl-pl|tr-tr|pt-pt|pt-br|en-us", description: "Country/language preference (for localized ads:?)" }
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAAk1BMVEWwMjIAAQACAAoSAwQ2CQcAH5VqERZsESgNK489KFwA
#   MrMAN6UQQwAXNpEAPakAQJ8AQ44RO7S2JQ8ASr6vLwqPOgoZYgCCSgvPPgVCbAF9XwzMTRrqUAHNY0VemADjbTiShjOYhiJR
#   oApJqgRerwlUtgBjwgDAsQDdqQB02AnowgP+soDfywDs2RL25Qr4727/8rdsT1F2AAAAAXRSTlMAQObYZgAAAAFiS0dEAIgF
#   HUgAAAAJcEhZcwAACxMAAAsTAQCanBgAAAAHdElNRQffBQcANDDneHDIAAAAlUlEQVQY02VPWxKCMAzcKmIF5GGrVkVAKA+x
#   Ve9/OhUK0xmTj2Q3yU4WAPnmL6Y69rDQwJB/bDOLpYNDEFgc352betYh4EIcK5lVgVHnIk/3kCdp5g7PHykv742sp43LFS4y
#   lMMNgbvebJl3U6ptjSxFFDPop+7NF5RFcVK8X6qfPIS+n0BrNf9FQ98retXZDlfoxuYDwYsJfXHQg0AAAAAASUVORK5CYII=
# png-orig: https://openclipart.org/detail/176727/windows-bug
# priority: extra
# status: unsupported
#
# Well, this one is Windows-specific, so naturally uses
# horrible formats WAX ( ASX ) for playlists. Still can
# be parsed by action module, but possibly falling back
# onto raw extraction etc.
#
# Only fetches the first page for each category anyway.
# And there's no specific category extraction, so stuck
# on the UK entries.
#
# Most entries are lower bitrates, 32 to 64 kbit/s MP3.


import re
from config import *
from channels import *
import ahttp


# Yay, windows playlists.
class windowsmedia (ChannelPlugin):


    # control flags
    has_search = False
    listformat = "wax"
    audioformat = "audio/mpeg"
    titles = dict(listeners=False, bitrate=False, playing="Location")
    _web = "http://www.windowsmedia.com/RadioUI/Home.aspx?g={}&culture=en-gb"
    base = "http://www.windowsmedia.com/RadioUI/getstationsforgenre.aspx?g={}&offset=0&culture={}"
    _url = "http://www.windowsmedia.com/RadioTunerAPI/Service.asmx/playStation?stationID={}&dialupDetected=true&useHighBandwidth=false&locale={}"

    categories = ["80s", "Adult Hits", "Adult Rock", "Alternative Rock",
    "Americana + Roots", "Big Band", "Blues", "Christian Hits", "Classic R&B",
    "Classic Rock", "Classical", "Comedy", "Country", "Dance + Electronica",
    "Holiday", "Indie", "International", "Jazz", "Latin", "Metal", "Miscellaneous",
    "New Age", "News + Talk", "Oldies", "Public Radio", "Rap + Hip Hop", "Reggae",
    "Religious", "Rock", "Smooth Jazz", "Soft Rock", "Soundtracks + Musicals",
    "Sports", "Top 40", "Urban/Modern R&B"]


    # static
    def update_categories(self):
        pass


    # Fetch entries
    def update_streams(self, cat, search=None):

        ucat = re.sub("\W+", "", cat.lower())
        html = ahttp.get(self.base.format(ucat, conf.windowsmedia_culture))

        r = []
        ls = re.findall("""
            stationid="([a-f0-9-]+)"  \s+
            onclick="Listen\('[\w-]+',\s*'(.+?)',\s*'(.+?)',
        """, html, re.X|re.S)
        for id, title, homepage in ls:
            r.append(dict(
                id = id,
                title = unhtml(title),
                homepage = homepage,
                url = self._url.format(id, conf.windowsmedia_culture),
                bitrate = 32,
            ))
        return r
      

