# encoding: UTF-8
# api: streamtuner2
# title: vTuner
# url: http://vtuner.com/
# description: 
# version: 0.1
# type: channel
# category: radio
# config:
#   { name: vtuner_pages,  value: 1,  type: int,  description: "Pages" }
# priority: contrib
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAhFBMVEUAAACIowCIowCIowCIowAkWlsAP3yIowCIowATTWoAP3wAP3xrjhsAP3wAP3yIowAAP3wAP3wAP3wMSHEbU2MAP3wV
#   TmkAP3wAP3wAP3yIowAAP3wJRXQzZU5Vfi9ehCcRTG1EcT4aUmWAnQgiWF0rXlVmih88a0Z3lxBNdzZvkBf///9k8C2HAAAAGnRSTlMAML8QgO8wIJ9wj3DfEN9wr2BAr++/z1Cfzypf+6cAAAABYktHRCskueQIAAAAB3RJTUUH4AQEFxQcg7S+WgAAAJFJREFUGNNVjlkWgjAMRSOiOCJzMa9SQGit
#   +1+gQ5CD+ct9Q0JEtArW9Dchb7ZEUTiDaLc/0PHEC885pvgSLFNJmizXLC9Q5Nm8p/rWGNO06U8H0DH3wOQpAXNnHjRKAdAjM1tAQ8DYOgHoBbgGsPx4R0YBFetvK1wlQHmr4fnZd2q6W/vhU+vr+TN1HTpXif4CK/0NNsIh2vQAAAAldEVYdGRhdGU6Y3JlYXRlADIwMTYtMDQtMDVUMDE6MjA6MjAr
#   MDI6MDD2b3oJAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDE2LTA0LTA1VDAxOjIwOjIwKzAyOjAwhzLCtQAAAABJRU5ErkJggg==
#
#
#

import re
import ahttp
from config import *
from channels import *


# vTuner directory
class vtuner (ChannelPlugin):

    # module attributes
    module = "vtuner"
    listformat = "pls"
    has_search = False
    categories = [
         "Alternative", "Folk", "Show Tunes", "Ambient", "Gospel", "Smooth Jazz",
         "Big Band", "Hard Rock", "Soft Rock", "Bluegrass", "Hip Hop",
         "Soundtracks", "Blues", "Holiday", "Top 40", "Celtic", "Jazz", "Variety",
         "Christian Contemporary", "Latin Hits", "World", "Christian Rock", "New Age",
         "World Asia", "Classic Rock", "Oldies", "World Europe", "Classical",
         "Pop", "World Hawaiian", "College", "Public", "World India", "Country",
         "R&B", "World Middle East", "Dance", "Reggae", "World", "Native American",
         "Electronica", "Rock", "World Tropical"
    ]
    titles = dict( genre="Genre", title="Station", playing="Location", bitrate="Bitrate", listeners=False )

    

    # just a static list for now
    def update_categories(self):
        pass


    # summarize links from surfmusik
    def update_streams(self, cat):

        entries = []
        url = "http://vtuner.com/setupapp/guide/asp/BrowseStations/BrowsePremiumStations.asp?sCategory=%s&sBrowseType=Format&sViewBy=&sSortby=POP&sWhatList=&sNiceLang=&iCurrPage=%s"
        html = ""
        for i in xrange(1, int(conf.vtuner_pages) + 1):
            html = html + ahttp.get(url % (cat, i))

        rx_radio = re.compile(r"""
            <a\s+href="\.\./func/dynampls.asp\?link=1&id=(\d+)">([^<>]+)</a>
            .+? "middle">([^<>]+)</td>
            .+? Category.+?>([^<>]+)</td>
            .+? <td.+?>(\w+)&nbsp;(\d+)K</td>
        """, re.X|re.S|re.I)

        # per-country list
        for uu in rx_radio.findall(html):
            log.DATA(uu)
            (id, title, loc, genre, fmt, br) = uu
            

            entries.append({
                "title": title,
                "url": "http://vtuner.com/setupapp/guide/asp/func/dynampls.asp?link=1&id=%s" % id, 
                "playing": loc,
                "genre": genre,
                "format": mime_fmt(fmt),
                "bitrate": int(br),
            })

        # done    
        return entries


