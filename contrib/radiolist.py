# encoding: UTF-8
# api: streamtuner2
# title: radiolist.net
# description: Station list by continent+country
# url: http://radiolist.net/
# version: 0.1
# type: channel
# category: radio
# priority: extra
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABgAAAAYBAMAAAASWSDLAAAAFVBMVEVKb61qibyDnMegs9S6yeDV4O37/vyx66abAAAAAWJLR0QAiAUdSAAAAAlwSFlzAAALEwAACxMB
#   AJqcGAAAAAd0SU1FB+ECDBAgLJqgZW4AAADoSURBVBjTNdBNj4MgEAbgqdLeZdo9C5NwFmo5Y7Wedauc1y/+/09YdLskkDwJmZl3IOxnON4A8frQhdc/7mG2cv3gx29X
#   rdUfZuVHQ3JHEzZ7GSuNXxFV/FYYwryO6MOiZqEdnQPUC/fsXZaMuxa6MFfOVYN7kIWpHZClyJGLFjbbC617KaRUEJ4r4fU7IqNYrW5f2kgU5gZInG6MZ086eejcyIvO
#   1KwoLayoJjqnuWO5giW8msxVmBQXD5PttSlRm8TG2fDNZS3rRO/opeSCMnPa82xSmNgkfRxJ5yZxlPrPDmLu+7GqX4lERq4G0UEyAAAAAElFTkSuQmCC
# extraction-method: regex
#
# Radio station list grouped by continents and countries.
# Some categories return no results, because web players are
# filtered out.


import re
import ahttp
from config import *
from channels import *


# radiolist.net
class radiolist (ChannelPlugin):

    # module attributes
    listformat = "pls"
    has_search = False
    categories = ["Europe", "America", "Canada", "Oceania", "Asia"]
    catmap = {"Europe":"", "America":"world", "Canada":"world/canada", "Oceania":"world/oceania", "Asia":"world/asia"}
    titles = dict( genre="Genre", title="Station", playing="Location", bitrate="Bitrate", listeners=False )

    # just a static list for now
    def update_categories(self):
        self.catmap = {"Europe":"", "America":"world", "Canada":"world/canada", "Oceania":"world/oceania", "Asia":"world/asia"}
        c = []#
        rx_links = re.compile(r"""
            <td(?:\sstyle="height:\s30px;")?><a\s+href="(?:http://www.radiolist.net)?/([\w/.-]+)">([\w\s-]+)</a>[^<]*</td>
        """, re.X)
        for title in ["Europe", "America", "Canada", "Oceania", "Asia"]:
            c.append(title)
            html = ahttp.get("http://www.radiolist.net/" + self.catmap[title])
            sub = []
            for p,t in re.findall(rx_links, html):
                if t in ["Terms", "About Us", "Donation", "United States"]:
                    continue
                sub.append(t)
                self.catmap[t] = p
            c.append(sorted(sub))
        self.categories = c

    # extract stream urls
    def update_streams(self, cat):
        rx_title = re.compile('<a href="([^">]+)" target="_blank">(.+?)</a>', re.I)
        rx_urls = re.compile('<a href="([^">]+)">(\d+)(?: Kbps)?</a>', re.I)
        rx_genre = re.compile('<td class="cell">([^<]+)</td>', re.I)
        entries = []
        html = ahttp.get("http://www.radiolist.net/" + self.catmap[cat])
        for block in re.findall("<tr>(.+?)</tr>", html, re.S):
            ut = re.findall(rx_title, block)
            uu = re.findall(rx_urls, block)
            lg = re.findall(rx_genre, block)
            print ut, uu, lg
            if ut and uu and lg:
                url, br = self.best_url(uu)
                entries.append(dict(
                    homepage = ut[0][0],
                    title = unhtml(ut[0][1]),
                    url = url,
                    bitrate = br,
                    format = self.guess_fmt(url),
                    listformat = self.guess_pls(url),
                    playing = lg[0],
                    genre = lg[1]
                ))
        # done    
        return entries

    # pick highest rated URL
    def best_url(self, urls):
        r = {}
        for url, br in urls:
            r[url] = to_int(br)
        #print "r=", r
        best = sorted(r, key=r.get, reverse=True)
        #print "best=", best
        return best[0], r[best[0]]

    # see if audio type can be guessed
    def guess_fmt(self, url):
        ext = re.findall("mp3|ogg|wma|asx", url)
        if ext:
            return mime_fmt(ext[0])
        else:
            return "audio/mpeg"

    # guess PLS/M3U from url
    def guess_pls(self, url):
        ext = re.findall("pls|asx|m3u|srv", url)
        if ext:
            return ext[0]
        else:
            return "srv"
    