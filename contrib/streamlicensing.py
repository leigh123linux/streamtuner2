# encoding: UTF-8
# api: streamtuner2
# title: streamlicensing
# description: Smaller streaming service provider
# url: http://www.streamlicensing.com/directory/
# version: 0.1
# type: channel
# category: radio
# priority: extra
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQBAMAAADt3eJSAAAAGFBMVEVhcAAODy8rLVpHS4RPU22DismUmLTm6va3Zc/ZAAAAAXRSTlMAQObYZgAA
#   AAFiS0dEAIgFHUgAAAAJcEhZcwAACxMAAAsTAQCanBgAAAAHdElNRQfhAgwUMiN14qDwAAAAW0lEQVQI12NggAADCMVW7gym3crBDJb08rJgZbB4
#   qqEQmBGsKMQEZggqMLCA1LAJM8AZaWUQhjpEO5uwamiQMJjBrChkADSlXBhsfHh5qgCYoWysqACxWQlCAwArBw5QNfhFygAAAABJRU5ErkJggg==
# extraction-method: regex
#
# Streaming service provider, which ensures station legality or fees
# according to US copyright/streaming laws.
#
# Has only major categories. Does not provide channel homepages, and
# is a bit slow due to huge page sizes. No search function implemented
# here.
#


import re
import ahttp
from config import *
from channels import *


# radiolist.net
class streamlicensing (ChannelPlugin):

    # module attributes
    listformat = "pls"
    has_search = False
    categories = []
    catmap = {}
    titles = dict( listeners=False )
    
    # config (not as plugin options here)
    conf_family_unsafe = 0
    conf_maxpages = 3
    
    # magic values
    base_url = "http://www.streamlicensing.com/directory/"
    pls_sffx = "%sindex.cgi/playlist.pls?action=playlist&type=pls&sid=%s&stream_id=%s"
    # This is well hidden, but it comes with a playlist generator, so doesn't require double lookups.
    # http://www.streamlicensing.com/directory/index.cgi?action=webpro_links&sid=4785&start=1&g=14&e=1&s=
    # .../directory/index.cgi/playlist.pls?action=playlist&type=pls&sid=4785&stream_id=1234

    # just a static list for now
    def update_categories(self):
        html = ahttp.get(self.base_url)
        cats = re.findall('"\?start=&g=(\d+)&e=&s="><.+?>([\w\s-]+)</span>', html)
        self.categories = sorted([c[1] for c in cats])
        self.catmap = dict([(t,i) for i,t in cats])

    # extract stream urls
    def update_streams(self, cat):
    
        # prep block regex
        rx_genre = re.compile(r"""
           <tr\sid='(\d+)' .*?
           Station\sName:<.*?>([^<]+)</(?:span|font|td|a)> .*?
           ^var\slastsong_\d+\s*=\s*'([^\n]+)'; .*?
           <a[^>]+onClick=[^>]+&stream_id=(\d+)'[^>]+>(\d+)k<
        """, re.I|re.S|re.X|re.M)
        
        # collect pages into single string
        html = ""
        for page in range(0, self.conf_maxpages):
            html += ahttp.get("%s?start=%s&g=%s&e=%s&s=" % (self.base_url, page * 10, self.catmap[cat], self.conf_family_unsafe))
            if not re.search("\?start=%s.*>Next" % ((page + 1) * 10), html):
                break
        html = re.sub(">Featured Stations.+?>Previous Page", "", html, 100, re.S)
        print html

        # extract and convert to station rows
        entries = []
        for uu in re.findall(rx_genre, html):
            print uu
            entries.append(dict(
                genre = cat,
                id = to_int(uu[0]),
                sid = to_int(uu[3]),
                title = unhtml(uu[1]),
                playing = unhtml(uu[2]),  # actually JS decoding...
                format = "audio/mpeg",
                bitrate = to_int(uu[4]),
                url = self.pls_sffx % (self.base_url, uu[0], uu[3])
            ))
        return entries

