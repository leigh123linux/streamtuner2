# encoding: UTF-8
# api: streamtuner2
# title: radiolist.net
# description: Station list by continent+country
# url: http://radiolist.net/
# version: 0.4
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
import action
import ahttp
from config import *
from channels import *


# radiolist.net
#
# · Groups stations by continents and countries. Where Europe seems to be the
#   main category (empty "" path), while U.S. is labeled "/world", and Canada
#   and Asia etc. again a subpath "/world/canada" even. The .catmap{} assigns
#   paths to titles.
#
# · Playlist formats vary wildly. Therefore this module comes with a guessing
#   method (super crude) of its own.
#
# · The audio-format-from-URL guessing should be generalized out of here perhaps.
#
# · Each station is in a <tr>…</tr> block. Invidual regexps are used for field
#   extraction afterwards (instead of a block match).
#
# · Entries may contain more than one streaming url. Each accompanied by a
#   bitrate. → Therefore the .best_url() sorting method.
#
# · Later versions might of course use multi-urls again…
#
class radiolist (ChannelPlugin, action.heuristic_funcs):

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
        rx_title = re.compile('<a\s+href="([^">]+)"[^>]+target="_blank"[^>]*>(.+?)</a>', re.I)
        rx_urls = re.compile('<a href="([^">]+)">(\d+)(?: Kbps)*</a>', re.I)
        rx_genre = re.compile('<td[^>]+>(\w*[^<>]*)</td>\s*<td[^>]+>(\w+[^<>]+)</td>\s*$', re.I)
        entries = []
        html = ahttp.get("http://radiolist.net/" + self.catmap[cat])
        log.DATA(html)
        for block in re.findall("<tr>(.+?)</tr>", html, re.S):
            log.BLOCK(block)
            ut = re.findall(rx_title, block)  # homepage+title
            uu = re.findall(rx_urls, block)   # urls+bitrates
            lg = re.findall(rx_genre, block)  # location+genre
            #print ut, uu, lg
            if ut and uu and lg:
                log.D(ut,uu,lg)
                url, br = self.best_url(uu)
                entries.append(dict(
                    homepage = ut[0][0],
                    title = unhtml(ut[0][1]),
                    url = url,
                    bitrate = br,
                    format = self.mime_guess(url, "audio/mpeg"),
                    listformat = self.list_guess(url),
                    playing = lg[0][0],
                    genre = lg[0][1]
                ))
        # done    
        [log.DATA(e) for e in entries]
        return entries

    # pick highest rated URL from [(url,bitrate),…] tuples
    def best_url(self, urls):
        r = dict([(u, to_int(b)) for u,b in urls])  # {url: bitrate, …}
        best = sorted(r, key=r.get, reverse=True)
        return best[0], r[best[0]]

    