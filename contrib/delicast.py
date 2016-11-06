# encoding: UTF-8
# api: streamtuner2
# title: Delicast
# description: directory of streaming media
# url: http://delicast.com/
# version: 0.5
# type: channel
# category: radio
# config: -
# png:
#    iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAAAAAA6mKC9AAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAA
#    AmJLR0QA/4ePzL8AAAAHdElNRQffBB4UJAsX77G0AAAANUlEQVQY02OwQwMMdv/BAEUASCFEoAIIEZIEIGYjBCAUwpb/6O5ACEABGQJ2cFsQIlB3oAEA6iVo+vl+BbQA
#    AAAldEVYdGRhdGU6Y3JlYXRlADIwMTUtMDQtMzBUMjI6MzY6MDMrMDI6MDAFLUvfAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDE1LTA0LTMwVDIyOjM2OjAzKzAyOjAwdHDz
#    YwAAAABJRU5ErkJggg==
# priority: rare
#
# Just a standard genre/country radio directory. Not very
# suitable for extraction actually, because it requires a
# second page request for uncovering the streaming URLs.
#
# This is done in row(), so only happens on playback. Which
# of course won't allow for exporting/bookmarking etc.
# And the server is somewhat unresponsive at times. Only one
# page (50 stations) is fetched.


import re
from config import *
from channels import *
import ahttp
import action


# Delayed streaming URL discovery
class delicast (ChannelPlugin):

    # control flags
    has_search = False
    listformat = "srv"
    audioformat = "audio/mpeg"
    titles = dict(listeners=False, bitrate=False, playing="Location")

    categories = ["60s", "70s", "80s", "90s", "Alternative", "Blues",
    "Chillout", "Christian", "Classical", "Community", "Country", "Culture",
    "Dance", "Disco", "Easy listening", "Electronic", "Folk", "Funk",
    "Gospel", "Hiphop", "House Indie", "Information", "Jazz", "Latin",
    "Lounge", "Love", "Metal", "Oldies", "Pop", "R n b", "Reggae", "Rock",
    "Romantic", "Soul", "Sports", "Student", "Talk", "Techno", "Trance",
    "Urban", "World music"]
    

    # static
    def update_categories(self):
        pass


    # Fetch entries
    def update_streams(self, cat, search=None):

        ucat = re.sub("\W+", "-", cat.lower())
        html = ahttp.get("http://delicast.com/radio/" + ucat)

        r = []
        for tr in html.split("<tr>")[1:]:
            ls = re.findall("""
                "pStop\(\)" \s href="(.*?)">
                .*?
                pics/((?!play_triangle)\w+)
                .*?
                120%'>([^<>]+)</span>
            """, tr, re.X|re.S)
            if len(ls):
                homepage, country, title = ls[0]
                r.append(dict(
                    homepage = homepage,
                    playing = country,
                    title = unhtml(title),
                    url = "urn:delicast",
                    genre = cat,
             #      genre = unhtml(tags),
                ))
        return r
      

    # Update `url` on station data access (incurs a delay for playing or recording)
    def resolve_urn(self, row):
        if row.get("url").startswith("urn:delicast"):
            html = ahttp.get(row["homepage"])
            ls = re.findall("^var url = \"(.+)\";", html, re.M)
            if ls:
                row["url"] = unhtml(ls[0])
            else:
                log.ERR("No stream found on %s" % row["homepage"])
        return row

