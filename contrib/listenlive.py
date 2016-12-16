# encoding: UTF-8
# api: streamtuner2
# title: ListenLive
# description: European radio stations streaming live on the internet
# url: http://listenlive.eu/
# version: 0.0
# type: channel
# category: radio
# config: -
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAARVBMVEWdHBWSg1Cbj1mnmF6jn5GuomajpaCrqYu3qmy0roi6
#   r3rAsW25tae2t7HCvKfPv3rOw4zKxrfJyMDTzaXUz7LW1s7g4t727CdZAAAAAXRSTlMAQObYZgAAAAFiS0dEAIgFHUgAAAAJ
#   cEhZcwAACxMAAAsTAQCanBgAAAAHdElNRQffBQcAMynMUk7PAAAAkElEQVQY01VP2xbDIAizUq0WGS1e/v9TB9qdbXlLICE4
#   Z9g8gN/cB1tAVmB4JI98tdbqlZJ/eBWS3u8jTCVx7RRNKEdKzgFffVBUfpdyItjCGJG6iCqZk0Nuo6tDiIp6cAqiDokx7hZi
#   Fo3QBSp7xmChOhSxjNfJsM5OaKadncWWkL9V/6rrc7Ceg59/vWLRN2yqCjHMvARcAAAAAElFTkSuQmCC
# png-orig: https://openclipart.org/detail/148465/1-euro
# priority: extra
# extraction-method: regex
#
# And another radio directory, primarily collecting euro
# stations, mixed genres, and grouping by country.
#
# Also available:
#  http://www.australianliveradio.com/
#  http://www.nzradioguide.co.nz/


import re
from config import *
from channels import *
import ahttp


# listenlive.eu
class listenlive (ChannelPlugin):

    # control flags
    has_search = False
    listformat = "srv"
    audioformat = "mp3"
    titles = dict(listeners=False, playing="Location")
    categories = []
    base = "http://listenlive.eu/{}.html"


    # short list of categories
    def update_categories(self):
        html = ahttp.get("http://listenlive.eu/")
        ls = re.findall(r"""b.gif"[\s/]*>\s+<a\s+href="(\w+).html">([^<>]+)</a>""", html)
        self.catmap = {title: link for link, title in ls}
        self.categories = [title for link, title in ls]


    # Fetch entries
    def update_streams(self, cat, search=None):
        r = []

        # split into table rows
        html = ahttp.get(self.base.format(self.catmap[cat]), encoding="utf-8")
        for tr in html.split("<tr>"):
        
            # extract fields
            ls = re.findall("""
                <a\s+href="([^<">]+)">    # homepage
                <b>([^<>]+)</b>           # title
                .*? <td>([^<>]+)</td>     # location
                .+  alt="(\w+)"           # format
                .+ <a\s+href="([^<">]+)"> # url
                (\d+)                     # bitrate
            """, tr, re.X|re.S)
            
            # assemble into rows
            if len(ls) and len(ls[0]) == 6:
                homepage, title, location, format, url, bitrate = ls[0]
                genre = re.findall("<td>([^<>]+)</td>\s</tr>", tr)
                r.append(dict(
                    homepage = homepage,
                    playing = location,
                    title = unhtml(title),
                    url = url,
                    genre = genre[0] if genre else cat,
                    bitrate = int(bitrate),
                    format = mime_fmt(format),
                ))
        return r
      

