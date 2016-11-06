# encoding: UTF-8
# api: streamtuner2
# title: Reciva
# url: https://radios.reciva.com/
# description: Home internet radio app and diverse station database.
# version: 0.4
# type: channel
# category: radio
# config: -
# priority: contrib
# png:
#    iVBORw0KGgoAAAANSUhEUgAAABAAAAAQBAMAAADt3eJSAAAAGFBMVEXiMATfORfhQyTrZk7uh3Tzs6n10879+/iUjtOkAAAAAWJLR0QAiAUdSAAAAAlwSFlzAAALEwAA
#    CxMBAJqcGAAAAAd0SU1FB+AEBw4nI8D7wUYAAACISURBVAjXDc09D4JAFETREcParl/UvKdoKxi1JgZoiYnQSiJua2ST+ftud3KLGZDvYteT4DRTifqAFCvVmPBRl6um
#    DsOWP1W5oUw42dQaFBu2lckqqJwxHg8Burx+u0WGXOW5nuoYZUhN6xMMKr03ryYMyj36WAee5OJaE7687R5zF8Cx2DvyD3ZIHyPRcAnIAAAAAElFTkSuQmCC
#
# Reciva is a mobile app. They have a web directory though.
# It's a bit difficult to query, and streaming urls aren't
# directly accessible. But allows to fetch all stations from
# a category at once; so still a quick database.
#
# They probably have an API somewhere, but no public docs.
#
# You can optionally define a user account and password in
# `.netrc` (make a `machine reciva.com` entry) → which is
# going to be used implicitly.
#


import re
from pq import pq
import ahttp
import action
from config import *
from channels import *


# Reciva directory
class reciva (ChannelPlugin):

    # module attributes
    module = "reciva"
    listformat = "pls"
    has_search = True
    categories = ['60s', '70s', '80s', '90s', 'Adult', ['Adult Contemporary'], 'Alternative', 'Ambient', 'Bluegrass', 'Blues', 'Bollywood', 'Christian', ['Christian Contemporary'], 'Classic Rock', 'Classical', 'College', 'Comedy', 'Contemporary', 'Country', 'Dance', 'Discussion', 'Easy', 'Electronica', 'Experimental', 'Folk', 'Gospel', 'Greek', 'Hip Hop', 'Indian', 'Indie', ['Indie Rock'], 'Jazz', 'Jungle', 'Kids', 'Latin Hits', 'New Age', 'News', ['News Talk', 'News Updates'], 'Oldies', 'Pop', 'Public', 'Punk', 'Rap', 'Reggae', 'Religious', 'Rock', 'Short Wave Radio', 'Soft Rock', 'Spanish', 'Sports', 'Talk', 'Top 40', 'Unknown', 'Varied', 'World', ['World Africa', 'World Asia', 'World Caribbean', 'World Europe', 'World Mediterranean', 'World Middle East', 'World Tropical']]
    catmap = { 'classical': '14', 'dance': '18', 'bluegrass': '52', 'contemporary': '16', 'pop': '34', 'spanish': '66', 'college': '15', 'rap': '38', 'ambient': '69', 'talk': '43', 'alternative': '9', 'religious': '39', 'blues': '10', 'folk': '23', 'classic rock': '13', '90s': '7', 'adult contemporary': '8', 'oldies': '33', 'indie rock': '54', 'electronica': '21', 'unknown': '45', 'discussion': '19', 'news talk': '31', 'world mediterranean': '55', 'sports': '42', 'new age': '51', 'indie': '27', 'indian': '65', 'easy': '20', '80s': '6', 'world africa': '67', 'comedy': '62', 'public': '35', 'jungle': '72', 'reggae': '48', 'world middle east': '50', 'christian': '11', 'world caribbean': '68', '60s': '58', 'world europe': '56', 'jazz': '28', '70s': '5', 'soft rock': '41', 'top 40': '44', 'adult': '57', 'news': '30', 'bollywood': '60', 'world tropical': '53', 'latin hits': '29', 'varied': '46', 'christian contemporary': '12', 'kids': '59', 'short wave radio': '73', 'world': '49', 'world asia': '47', 'country': '17', 'news updates': '32', 'punk': '36', 'greek': '25', 'hip hop': '26', 'rock': '40', 'gospel': '24', 'experimental': '22' }
    titles = dict( genre="Genre", title="Station", playing="Location", bitrate="Bitrate", listeners=False )
    base_url = "https://radios.reciva.com/stations/genre/%s?&start=0&count=%s"
    
    
    # update list
    def update_categories(self):
        self.categories = []
        html = ahttp.get(self.base_url % (1, 1))
        for c in re.findall('id="cg-(\d+)">([\w\d\s]+)</a></li>', html):
            self.catmap[c[1].lower()] = c[0]
            self.categories.append(c[1])


    # fetchy fetch
    def update_streams(self, cat, search=None):
        entries = []
        if cat:
            html = ahttp.get(self.base_url % (self.catmap[cat.lower()], conf.max_streams))
        else: # search
            html = ahttp.get("https://radios.reciva.com/stations/search?q=%s&categories=&codec=&min_bitrate=&max_bitrate=&working=true&count=%s" % (search, conf.max_streams))
        if not html:
            log.ERR("No results from http://radios.reciva.com/ server. Their category browsing sometimes breaks. We're not using the search function as that would strain their server too much. You might try adding login credentials to `.netrc` - albeit that rarely helps.", html)
            return []
        
        # extract
        for row in (pq(row) for row in pq(html).find("#mytable").find(".oddrow, .evenrow")):
            u = row.find(".streamlink")
            if u:
                id = re.findall("(\d+)", u.attr("href"))[0]
                entries.append({
                    "title": row.find(".stationName").text(),
                    "id": id,
                    "url": "urn:reciva:%s" % id,
                    "homepage": "https://radios.reciva.com/station/%s" % id,
                    "playing": row.find(".stationLocation").text(),
                    "genre": row.find(".stationGenre").text(),
                    "format": mime_fmt(row.find(".streamCodec").text()[0:3]),
                    "bitrate": int(re.findall("\d+", row(".streamCodec").text()[4:] + " 0")[0]),
                })

        # done    
        return entries


    # Fetch real `url` on stream access/playback (delay)
    def resolve_urn(self, r):
        if r["url"].startswith("urn:"):
            id = r["url"].split(":")[2]
            html = ahttp.get("https://radios.reciva.com/streamer?stationid=%s&streamnumber=0" % id)
            ls = re.findall("""(?:<iframe src=|iframe\()['"]([^'"]+)['"]""", html)
            if ls:
                r["url"] = ls[0]
            else:
                log.ERR("No stream found for reciva station #%s", row["id"])
        return r


    # Option login
    def init2(self, *p):
        lap = conf.netrc(varhosts = ("reciva.com", "radios.reciva.com"))
        if lap:
            log.LOGIN("Reciva account:", lap)
            ahttp.get(
                "https://radios.reciva.com/account/login",
                {
                    "username": lap[0] or lap[1],
                    "password": lap[2]
                },
                timeout=2
            )
