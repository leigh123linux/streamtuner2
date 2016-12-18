# encoding: UTF-8
# api: streamtuner2
# title: SurfMusic
# description: User collection of streams categorized by region and genre.
# author: gorgonz123
# version: 0.5
# type: channel
# category: radio
# config:
#   { name: surfmusik_lang,  value: EN,  type: select,  select: "DE=German|EN=English",  description: "Switching to a new category title language requires reloading the category tree.",  category: language  }
# priority: default
# source: http://forum.ubuntuusers.de/topic/streamtuner2-zwei-internet-radios-anhoeren-au/3/
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAAAA3NCSVQICAjb4U/gAAACmklEQVQokWXSy0tUYRgG8Pe7zBnzWk06RFGhoNAmBJuBbFDcNEoK4k5cxUQbYQYZBtok2L7NuGrpIlSkQNI004g8Ss1GuqAILjSkmNKD45k53+XM97aQpOj3FzzPwwNKKfkv
#   ISVKiYjT6+uJx48Lvl/WWgihlFJKgfyPL+UPKWefPPlaXz/JefbRI4kohZBSKqUoAJA/DKL0PMX52vh41ciIF48Xurtrx8ZezM5almWMAURKCDlJpbUGxGAg8FNKnJ7Ww8NkYqKyWLxLSGB5uQRAjQFCKAAwxjjnjDFKKTAW0nrm4sVgJvMplepdWfkFUBePVwAgIb7v
#   c0SklBrEsu8HOWfB4BfHqXGcbwMD8Vwux5gaHb0djxutgTGKCEopz/PcQsFTal+ImZmZifb2XYBdgFex2OziYgHxdEetNUilpOdJxDXbnr5z5wPARij0oKXl1cuXRURELCvlFosnPYUQRHueDAZzT59eSyYLUr7u6fkYDr+37ZvXr19uaGhqbu7q6mptbdVaI6Lv+5Ra
#   1tuFhWAqdcWYz/fuPa+qCjFWWy7Xnzv3bnU1nU53dnZms1lKqTEmEAjAMeJkOu0AfGxre7O/v72xoYTo6e7e2tpCxEwmAwA1NTV7e3vlclkIQSt9/0Yymevvt7a3ry4tVV66dCylYezw4GBnZ2dzc5NznslkwuGw1poQQoque6ai4oixQ9tumJr6VSjU1tU9XFo6ikaL
#   +fzZ8+cTiURHR4fW2hhDKeUIIJRC191wnHwkEmtqutDY6H7/fn9oKBqNVldXA4AQglJKCAEAcBxHKTU3NwcAAHArFns2NdXb15fP540xpVKpVCqd/lIpRbTWAICI8/PzrutalmXb9uDgYCQS8TyPcw5/IYT8BpJoukMEtogaAAAAAElFTkSuQmCC
# recognizes: max_streams
# extraction-method: regex
# url: http://surfmusic.de/
#
# This plugin comes in German (SurfMusik) and English (SurfMusic) variations.
# It provides a vast collection of international stations and genres.
# While it's not an open source project, most entries are user contributed.
#
# They do have a Windows client, hencewhy it's even more important for
# streamtuner2 to support it on other platforms.
#
# TV stations don't seem to work mostly. And loading the webtv/ pages would
# be somewhat slow (for querying the actual mms:// streams).
#
#
#

import re
import ahttp
from config import *
from channels import *



# Surfmusik sharing site
class surfmusik (ChannelPlugin):

    # module attributes
    module = 'surfmusik'
    listformat = "m3u"
    has_search = False
    lang = "DE"   # last configured categories
    base = {
       "DE": ("http://www.surfmusik.de/", "genre/", "land/"),
       "EN": ("http://www.surfmusic.de/", "format/", "country/"),
    }
    categories = []
    titles = dict( genre="Genre", title="Station", playing="Location", bitrate=False, listeners=False )

    
    # Set channel title
    def init2(self, parent=None):
        # title updating is a workaround, because the fixed .meta attribute are read first
        self.title = ("SurfMusik", "SurfMusic")[conf.get("surfmusik_lang", "EN") == "EN"]
        self.meta["title"] = self.title


    # just a static list for now
    def update_categories(self):

        lang = conf.surfmusik_lang
        (base_url, path_genre, path_country) = self.base[lang]

        cats = {
            "DE": ["Genres", "Deutschland", "Europa", "USA", "Kanada", "Amerika", "Afrika", "Asien", "Ozeanien", "MusicTV", "NewsTV", "Poli", "Flug"],
            "EN": ["Genres", "Europe", "Germany", "USA", "Canada", "America", "Africa", "Asia", "Oceania", "MusicTV", "NewsTV", "Poli", "Flug"],
        }
        map = {
            "Genres": "genres.htm",
            "Europe": "euro.htm",           "Europa": "euro.htm",
            "Germany": "bundesland.htm",    "Deutschland": "bundesland.htm",
            "Africa": "africa.htm",         "Afrika": "africa.htm",
            "America": "amerika.htm",       "Amerika": "amerika.htm",
            "Asia": "asien.htm",            "Asien": "asien.htm",
            "Oceania": "ozean.htm",         "Ozeanien": "ozean.htm",
            "Canada": "canadian-radio-stations.htm", "Kanada": "kanada-online-radio.htm",
            "USA": "staaten.htm",
        }
        rx_links = re.compile(r"""
            <a\b  [^>]+ \b  href="
            (?:(?:https?:)?//www.surfmusi[kc].de)? /?
            (?:land|country|genre|format)/
            ([\-+\w\d\s%]+)  \.html"
        """, re.X)

        r = []
        # Add main categories, and fetch subentries (genres or country names)
        for cat in cats[lang]:
            r.append(cat)
            if map.get(cat):
                subcats = rx_links.findall( ahttp.get(base_url + map[cat]) )
                subcats = [x.replace("+", " ").title() for x in subcats]
                r.append(sorted(subcats))

        self.categories = r


    # summarize links from surfmusik
    def update_streams(self, cat):

        (base_url, path_genre, path_country) = self.base[conf.surfmusik_lang]
        entries = []
        i = 0
        max = int(conf.max_streams)
        is_tv = 0
        
        # placeholder category
        if cat in ["Genres"]:
            return self.placeholder
        # separate
        elif cat in ["Poli", "Flug"]:
            path = ""
        # tv
        elif cat in ["SurfTV", "MusikTV", "NewsTV"]:
            path = ""
            is_tv = 1
        # genre 
        elif cat in self.categories[self.categories.index("Genres") + 1]:
            path = path_genre
        # country
        else:
            path = path_country
        
        self.status(-1.0)
        if path is not None:
            ucat = cat.replace(" ", "+").lower()
            html = ahttp.get(base_url + path + ucat + ".html")
            html = re.sub("&#x?\d+;", "", html)
        
            rx_radio = re.compile(r"""
                <td\s+class="home1"><a[^>]*\s+href="(.+?)"[^>]*> .*?
                <a\s+class="navil"\s+href="([^"]+)"[^>]*>([^<>]+)</a></td>
                <td\s+class="ort">(.*?)</td>.*?
                <td\s+class="ort">(.*?)</td>.*?
            """, re.X|re.I)
            rx_video = re.compile(r"""
                <a[^>]+href="([^"]+)"[^>]*>(?:<[^>]+>)*Externer
            """, re.X|re.I)

            # per-country list
            for uu in rx_radio.findall(html):
                (url, homepage, name, genre, city) = uu
                
                # find mms:// for webtv stations
                if is_tv:
                    m = rx_video.search(ahttp.get(url))
                    if m:
                        url = m.group(1)
                # just convert /radio/ into /m3u/ link
                else:
                    url = "http://www.surfmusik.de/m3u/" + url[30:-5] + ".m3u"

                entries.append({
                    "title": name,
                    "homepage": homepage,
                    "url": url, 
                    "playing": city,
                    "genre": genre,
                    "format": ("video/html" if is_tv else "audio/mpeg"),
                })

                # limit result list
                if i > max:
                   break
                if i % 10 == 0:
                   self.parent.status(float(i)/float(max+5))
                i += 1
 
        # done    
        return entries


