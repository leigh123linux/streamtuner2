# encoding: UTF-8
# api: streamtuner2
# title: SurfMusik
# description: User collection of streams categorized by region and genre.
# author: gorgonz123
# version: 0.5
# type: channel
# category: radio
# config:
#   { name: surfmusik_lang,  value: EN,  type: select,  select: "DE=German|EN=English",  description: "Switching to a new category title language requires reloading the category tree.",  category: language  }
# priority: default
# source: http://forum.ubuntuusers.de/topic/streamtuner2-zwei-internet-radios-anhoeren-au/3/
# recognizes: max_streams
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
import ahttp as http
from config import conf, dbg, __print__
from channels import *



# Surfmusik sharing site
class surfmusik (ChannelPlugin):

    # description
    title = "SurfMusik"
    module = "surfmusik"
    homepage = "http://www.surfmusik.de/"
    listformat = "audio/x-scpls"

    lang = "DE"   # last configured categories
    base = {
       "DE": ("http://www.surfmusik.de/", "genre/", "land/"),
       "EN": ("http://www.surfmusic.de/", "format/", "country/"),
    }

    categories = []
    titles = dict( genre="Genre", title="Station", playing="Location", bitrate=False, listeners=False )
    
    # Set channel title
    def __init__(self, parent=None):
        self.title = ("SurfMusik", "SurfMusic")[conf.get("surfmusik_lang", "EN") == "EN"]
        ChannelPlugin.__init__(self, parent)


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
                subcats = rx_links.findall( http.get(base_url + map[cat]) )
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
            path = None
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
        
        if path is not None:
            ucat = cat.replace(" ", "+").lower()
            html = http.get(base_url + path + ucat + ".html")
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
                    m = rx_video.search(http.get(url))
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


