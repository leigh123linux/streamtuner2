# encoding: UTF-8
# api: streamtuner2
# title: house-mixes.com
# description: UK DJs house/techno mixes
# type: channel
# category: collection
# version: 0.6
# url: http://www.house-mixes.com/
# config:
#    ( -x-off-name: housemixes_pages, type: int, value: 5, description: maximum number of pages to scan )
# priority: contrib
# png:
#    iVBORw0KGgoAAAANSUhEUgAAABQAAAASBAMAAACp/uMjAAAAGFBMVEUIBQE7KCGSPABUWFrwcACIkJayuLr3+vjaVnR4AAAAAWJLR0QAiAUdSAAAAAlwSFlzAAALEwAACxMB
#    AJqcGAAAAAd0SU1FB+AKCQwWONCoEiQAAACPSURBVAjXLY29DsIgFIUPxehaExJXW+EB7MJaCE/gAKvRaNdWYu/rewve6bsn5wcARN+3KNeE7hgq60t8X30Rx4mIhjOj2tMr
#    UnaMPmXAUsPiSBwRdHMcWtEKpIdHMFk7FQ6fAG0WPe46OXgos9QhrpC5jm576wayvBO0x7Pgaebee0HJDlv9sN80/xGxOH8QkRfKLi9RvwAAAABJRU5ErkJggg==
# depends: pq, ahttp
#
# House-mixes.com is an UK platform for DJs to showcase their
# house/dance/techno mixes.
#


import ahttp
from pq import pq
import re
from config import *
from channels import *
import channels



# House-Mixes
#
class housemixes(channels.ChannelPlugin):

    # attrs
    base_url = "http://www.house-mixes.com"
    listformat = "href" # direct mp3s (after .row() hook)
    has_search = False
    titles = dict(title="Mix Title", playing = "DJ", bitrate="Favs")
    img_resize = 32
    
    # categories
    catmap = {"Ambient / Chillout": "/djmixes/chillout-dj-mixes", "Bassline House / Speed Garage / 4x4": "/djmixes/bassline-house-dj-mixes", "Breakbeat": "/djmixes/breakbeat-dj-mixes", "Chicago House": "/djmixes/chicago-house-dj-mixes", "Commercial House": "/djmixes/commercial-house-dj-mixes", "Darkstep": "/djmixes/darkstep-dj-mixes", "Deep House": "/djmixes/deep-house-dj-mixes", "Deep Tech House": "/djmixes/deep-tech-house-dj-mixes", "Detroit Techno": "/djmixes/destroit-techno-dj-mixes", "Drum n Bass": "/djmixes/dnb-dj-mixes", "Dub": "/djmixes/dub-dj-mixes", "Dub Techno": "/djmixes/dub-techno-dj-mixes", "Dubstep": "/djmixes/dub-step-dj-mixes", "Electro House": "/djmixes/electro-house-dj-mixes", "Fidget House": "/djmixes/fidget-house-dj-mixes", "Funk / Disco / Nu-Disco": "/djmixes/funk-disco-dj-mixes", "Funky House": "/djmixes/funky-house-dj-mixes", "Goa Trance": "/djmixes/goa-trance-dj-mixes", "Hard House / Hard Dance": "/djmixes/hardhouse-dj-mixes", "Hardcore Gabber": "/djmixes/hardcore-gabber-dj-mixes", "Hardstyle": "/djmixes/hardstyle-dj-mixes", "House": "/djmixes/house-dj-mixes", "Intelligent Drum n Bass": "/djmixes/intelligent-dnb-dj-mixes", "Jackin House": "/djmixes/jackin-house-dj-mixes", "Jump Up": "/djmixes/jumpup-dnb-dj-mixes", "Jungle": "/djmixes/jungle-dnb-dj-mixes", "Latin House": "/djmixes/latin-dj-mixes", "Liquid Drum n Bass": "/djmixes/liquid-dnb-dj-mixes", "Mash-Ups": "/djmixes/Mash-Ups-dj-mixes", "Minimal / Techno": "/djmixes/minimal-techno-dj-mixes", "Mixed Genre": "/djmixes/mixed-genre-dj-mixes", "Neurofunk": "/djmixes/neurofunk-dj-mixes", "Old Skool": "/djmixes/old-skool-dj-mixes", "Original Productions": "/djmixes/productions-dj-mixes", "Progressive House": "/djmixes/progressive-house-dj-mixes", "Progressive Trance": "/djmixes/progressive-trance-dj-mixes", "Psy  Trance": "/djmixes/psy-trance-dj-mixes", "Reggae": "/djmixes/reggae-dj-mixes", "Remixes": "/djmixes/Remixes-dj-mixes", "RnB / Hip Hop": "/djmixes/hiphop-dj-mixes", "Soulful House": "/djmixes/soulful-house-dj-mixes", "Tech House": "/djmixes/tech-house-dj-mixes", "Techno": "/djmixes/techno-dj-mixes", "Techstep": "/djmixes/techstep-dj-mixes", "Trance": "/djmixes/trance-dj-mixes", "Trap": "/djmixes/trap-dj-mixes", "Tribal House": "/djmixes/tribal-dj-mixes", "Trip Hop": "/djmixes/trip-hop-dj-mixes", "Tropical House": "/djmixes/tropical-house-dj-mixes", "UK Funky": "/djmixes/uk-funky-dj-mixes", "UK Garage": "/djmixes/uk-garage-dj-mixes", "UK Hardcore": "/djmixes/uk-hardcore-dj-mixes", "Uplifting Trance": "/djmixes/uplifting-trance-dj-mixes", "Urban": "/djmixes/urban-dj-mixes", "Vocal  Trance": "/djmixes/vocal-trance-dj-mixes"}
    categories = ["Drum n Bass", ["Darkstep", "Intelligent Drum n Bass", "Jump Up", "Jungle", "Liquid Drum n Bass", "Neurofunk", "Techstep"], "House", ["Ambient / Chillout", "Chicago House", "Commercial House", "Deep House", "Deep Tech House", "Electro House", "Fidget House", "Funk / Disco / Nu-Disco", "Funky House", "Jackin House", "Latin House", "Progressive House", "Soulful House", "Tech House", "Tribal House", "Tropical House"], "Mash-Ups", [], "Mixed Genre", [], "Old Skool", [], "Original Productions", [], "Remixes", [], "Techno", ["Detroit Techno", "Dub Techno", "Dub Techno", "Hard House / Hard Dance", "Hardcore Gabber", "Hardstyle", "Minimal / Techno", "UK Hardcore"], "Trance", ["Goa Trance", "Progressive Trance", "Psy  Trance", "Uplifting Trance", "Vocal  Trance"], "Urban", ["Bassline House / Speed Garage / 4x4", "Breakbeat", "Dub", "Dubstep", "Reggae", "RnB / Hip Hop", "Trap", "Trip Hop", "UK Funky", "UK Garage"]]
    
    # redefine
    streams = {}
    
        
    # Update cat list
    def update_categories(self):
        self.categories = []

        # Fetch /mixes to scan genres
        html = ahttp.get(self.base_url + "/mixes")
        #log.DATA( html )
        for group in pq(html)("ul.genre-nav > li"):

            a = pq(group)("a")[0]
            self.categories.append(a.text)
            self.catmap[a.text] = a.attrib["href"]
            subs = []
            
            for a in pq(group)("ul > li > a"):
                subs.append(a.text)
                self.catmap[a.text] = a.attrib["href"]
            
            self.categories.append(subs)
        

    # downloads stream list from shoutcast for given category
    def update_streams(self, cat):
        streams = []
        if not cat in self.catmap:
            return

        # collect
        self.status(0.0)
        html = ahttp.get(self.base_url + self.catmap[cat])
        max = int(conf.max_streams) / 50  # or enable conf.housemixes_pages?
        for i in range(2, int(max)):
            self.status(float(i) / max)
            if html.find("latest/" + str(i)):
                html = html + ahttp.get(self.base_url + self.catmap[cat] + "/latest/%s" % i)
        html = re.sub("</body>.+?<body>", "", html, 100, re.S)
        self.status("Extracting mixes…")
        
        # extract
        for card in [pq(e) for e in pq(html)(".card-audio")]:
            r = {
                "title": card(".card-audio-title span").text(),
                "playing": card(".card-audio-user a").text(),
                "genre": card(".card-tags a span").text(),
                # url will be substitute later
                "url": self.base_url + card(".audio-image-link").attr("href"),
                "homepage": self.base_url + card(".audio-image-link").attr("href"),
                # standard size 318x318 loads quicker
                "img": card(".audio-image-link img").attr("src"), # re.sub("=318&", "=32&",  ...)
                "listeners": int(card("a.card-plays").text()),
                "bitrate": sum(int(a) for a in card(".card-likes, .card-downloads, .card-favs").text().split()),
            }
            streams.append(r)

        #log.DATA( streams )
        return streams


    # Hook `url` access, look up actual mp3 file
    def row(self):
        r = ChannelPlugin.row(self)
        url = r.get("url")
        if url and url.find("/profile/") > 0:
            html = ahttp.get(url)
            ls = re.findall(r""" Mp3Url [\\\\:"]+ (http[^\\\\"]+) """, html, re.M|re.X)
            if ls:
                log.URL(ls[0])
                r["url"] = ls[0]
        return r
