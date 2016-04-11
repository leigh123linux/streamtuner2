# encoding: UTF-8
# api: streamtuner2
# title: vTuner
# url: http://vtuner.com/
# description: Huge station list by music service provider
# version: 0.3
# type: channel
# category: radio
# config:
#   { name: vtuner_pages,  value: 1,  type: int,  description: "Number of pages to fetch." }
#   { name: vtuner_order,  value: POP,  type: select,  select: "POP=Popularity|AA=Alphabetically|HBR=Quality|RELI=Uptime|OP=Country",  description: "Station sorting order." }
# priority: contrib
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAAhFBMVEUAAACIowCIowCIowCIowAkWlsAP3yIowCIowATTWoAP3wAP3xrjhsAP3wAP3yIowAAP3wAP3wAP3wMSHEbU2MAP3wV
#   TmkAP3wAP3wAP3yIowAAP3wJRXQzZU5Vfi9ehCcRTG1EcT4aUmWAnQgiWF0rXlVmih88a0Z3lxBNdzZvkBf///9k8C2HAAAAGnRSTlMAML8QgO8wIJ9wj3DfEN9wr2BAr++/z1Cfzypf+6cAAAABYktHRCskueQIAAAAB3RJTUUH4AQEFxQcg7S+WgAAAJFJREFUGNNVjlkWgjAMRSOiOCJzMa9SQGit
#   +1+gQ5CD+ct9Q0JEtArW9Dchb7ZEUTiDaLc/0PHEC885pvgSLFNJmizXLC9Q5Nm8p/rWGNO06U8H0DH3wOQpAXNnHjRKAdAjM1tAQ8DYOgHoBbgGsPx4R0YBFetvK1wlQHmr4fnZd2q6W/vhU+vr+TN1HTpXif4CK/0NNsIh2vQAAAAldEVYdGRhdGU6Y3JlYXRlADIwMTYtMDQtMDVUMDE6MjA6MjAr
#   MDI6MDD2b3oJAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDE2LTA0LTA1VDAxOjIwOjIwKzAyOjAwhzLCtQAAAABJRU5ErkJggg==
#
#
# vTuner is a rather large station directory. The website is somewhat
# slow though. So fetching large results sets isn't advisable.
#
# There's an C API of sorts, but no publically available docs. So
# querying the website for stations. Personal/non-commercial use
# seems explicitely permitted.
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
        'Alternative', 'Ambient', 'Big Band', 'Bluegrass', 'Blues',
        'Business News', 'Celtic', 'Christian Contemporary', 'Christian Rock',
        'Classic Rock', 'Classical', 'College', 'Country', 'Dance',
        'Electronica', 'Folk', 'Gospel', 'Hard Rock', 'Hip Hop', 'Holiday',
        'Jazz', 'Latin Hits', 'New Age', 'Oldies', 'Pop', 'Public', 'Reggae',
        'Rock', 'Show Tunes', 'Smooth Jazz', 'Soft Rock', 'Soundtracks', 'Top 40',
        'Variety', 'World', 'World Asia', 'World Europe', 'World Hawaiian',
        'World India', 'World Middle East', 'World Native American',
        'World Tropical',
        'Talk', ['Business News', 'News Talk', 'Scanner', 'Comedy',
        'News Updates', 'Sports', 'Government', 'Radio Drama', 'Talk', 'News',
        'Religious', 'Weather'],
        'TV', ['Music TV', 'TV Live Broadcast', 'TV Sports', 'TV Audio', 'TV News',
        'TV Variety', 'TV College', 'TV Public', 'TV Government', 'TV Religious',
        'Web Video']
    ]
    
    titles = dict( genre="Genre", title="Station", playing="Location", bitrate="Bitrate", listeners=False )

    base_url = "http://vtuner.com/setupapp/guide/asp/BrowseStations/BrowsePremiumStations.asp?sCategory=%s&sBrowseType=Format&sViewBy=&sSortby=%s&sWhatList=&sNiceLang=&iCurrPage=%s"
    

    # update list
    def update_categories(self):
        html = ahttp.get("http://vtuner.com/setupapp/guide/asp/BrowseStations/startpage.asp")
        rx_cat = re.compile("""BrowsePremiumStations\.asp\?sCategory=([\w\s]+)&""")
        cats = rx_cat.findall(html)
        if cats:
            self.categories = sorted(cats[:14*3])  \
                            + ["Talk"] + [cats[14*3-1:18*3-1]] \
                            + ["TV"] + [cats[18*3-1:]]
        return


    # fetchy fetch
    def update_streams(self, cat):
        entries = []
        html = ""
        for i in xrange(1, int(conf.vtuner_pages) + 1):
            html = html + ahttp.get(self.base_url % (cat, conf.vtuner_order, i))

        # crude <tr> extraction
        rx_radio = re.compile(r"""
            <a\s+href="\.\./func/dynampls.asp\?link=1&id=(\d+)">([^<>]+)</a>
            .+? "middle">([^<>]+)</td>
            .+? Category.+?>([^<>]+)</td>
            .+? <td.+?>(\w+)&nbsp;(\d+)K</td>
        """, re.X|re.S|re.I)

        # assemble
        for uu in rx_radio.findall(html):
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


