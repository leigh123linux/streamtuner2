# encoding: UTF-8
# api: streamtuner2
# title: Liveradio.ie
# description: Irish/worldwide radio station directory
# url: http://liveradio.ie/
# version: 0.2
# type: channel
# category: radio
# config: -
# png:
#    iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAABB0lEQVR4nLWTQUpDMRCGv0lregDBI3gAfW/hRrp8ZOMh5PUMXkFcu7EbTxHd
#    CC4EhfQkQg/QR5txYQqvMdVHwdnMZJj555uQwH+YurpaNZUOqTWl5i5qGIusDxIAZgBGuBhCsiOgrq7WUa+tkReAjepHystQgmn8zt0As40y
#    skYa4HwfSS5w2otd8svtWurqHyvnCZcXAHRRW7v8nANnq6bSPk0ucFQS+M3G2fkduMqLrJF5d3zSTnyYATsXmhO89WLfix8A1NWjvwhek5+m
#    praLGibPC8knFwnEh4U1ct9FvUvoLk0uPbjiCgCPyd+KD0/WyKX4EPcJFLG2/8EaMeLDoE91sH0B3ERWq2CKMoYAAAAASUVORK5CYII=
# priority: extra
#
# LiveRadio.ie, based in Ireland, is a radio station directory. It provides
# genre or country browsing (not in this plugin). It accepts user submissions.
#
# This channel loads their station logos as favicons, provides a live search.
#
# However, station URLs have to be fetched in a second page request. Such
# the listings are unsuitable for exporting right away. OTOH the website is
# pretty fast; so no delay there or in fetching complete categories.

import re
from config import *
from channels import *
import ahttp
import action


# Just a blog, needs per-page lookup
class liveradio (ChannelPlugin):

    # control flags
    has_search = True
    listformat = "srv"
    audioformat = "audio/mpeg"
    titles = dict(listeners=False, bitrate=False, playing="Location")
    fixed_size = 30
    img_resize = [30,30]

    # data store    
    categories = ["Top 20"]
    catmap = {"Top 20":"top-20"}
    base = "http://www.liveradio.ie/"
    

    # static
    def update_categories(self):
        html = ahttp.get("http://www.liveradio.ie/genres")
        self.categories = ["Top 20"]
        for row in re.findall(r"""<a href="/(stations/genre-[\w-]+)">([^<]+)</a>""", html):
            self.categories.append(unhtml(row[1]))
            self.catmap[unhtml(row[1])] = unhtml(row[0])


    # Fetch entries
    def update_streams(self, cat, search=None):

        # fetch
        html = ""
        page = 1
        while page < 9:
            page_sfx = "/%s"% page if page > 1 else ""
            if cat:
                add = ahttp.get(self.base + self.catmap[cat] + page_sfx)
            elif search:
                add = ahttp.get(self.base + "stations" + page_sfx, { "text": search, "country_id": "", "genre_id": ""})
            html += add
            if re.search('/\d+">Next</a>', add):
                page += 1
            else:
                break

        # extract
        r = []
        ls = re.findall("""
           itemtype="http://schema.org/RadioStation"> .*?
           href="/stations/([\w-]+) .*?
           <img\s+src="/(files/images/[^"]+)"   .*?
           ="country">([^<]+)<  .*?
           itemprop="name"><a[^>]+>([^<]+)</a> .*?
           class="genre">([^<]+)<
        """, html, re.X|re.S)
        for row in ls:
            log.DATA(row)
            id, img, country, title, genre = row
            r.append(dict(
                homepage = self.base + "stations/" + id,
                url = "urn:liveradio:" + id,
                playing = unhtml(country),
                title = unhtml(title),
                genre = unhtml(genre),
                img = self.base + img,
                img_resize = 32
            ))
        return r
      

    # Update `url` on station data access (incurs a delay for playing or recording)
    def resolve_urn(self, row):
        if row.get("url").startswith("urn:liveradio"):
            id = row["url"].split(":")[2]
            html = ahttp.get(self.base + "stations/" + id)
            ls = re.findall("jPlayer\('setMedia',\s*\{\s*'?\w+'?:\s*'([^']+)'", html, re.M)
            if ls:
                row["url"] = unhtml(ls[0])
            else:
                log.ERR("No stream found on %s" % row["homepage"])
        return row

