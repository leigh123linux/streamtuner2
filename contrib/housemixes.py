# api: streamtuner2
# title: house-mixes.com
# description: UK DJs house/techno mixes
# type: channel
# category: archive
# version: 0.4
# url: http://www.house-mixes.com/
# config: -
# priority: contrib
# png:
#    iVBORw0KGgoAAAANSUhEUgAAABgAAAAVCAIAAADTi7lxAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAABmJLR0QA/wD/AP+gvaeTAAAAB3RJTUUH4AoIAh8yU50KHAAABKFJREFUOMtllHtM1WUYx7/P+/7eH4fDATpcDkcBuSuwIFG8l5eGmjnNwK3S/mu2MU1ctdacl1pmO1vWMpfTwBnNpuSW900s1CaJLpilCEOZ7kRJiFzOlXP5/Z7+QBHtu/ff97Pv8z57P6Tr
#    OjPjUZjZYIrTqNjOJUnRWemUKAGgN4DWXv5jUOseRsBgQSCisVtEREqpaDT6iAJBKE+lqiJanm2EImh9QEMeBiFWR7qV7Fa09GF/G+74eDxI07THIGbWBSoLxJaFHAjyoZsxXWZGfG55ckaOUJZwwDfU3SruXXvZ6XFajV2/U1MPooxRmqZp2lgXi6R1pdg027x4mw71Zpevesu15vXsjAlK10FkGqY/EGi+2nr80AG949T6Ms8zFnH0Fpv8qJpSCiACVRWIng3Y+YKsWLjo3C9N4UiEmQ3DGPZ6hz1ewzCYmZnv37/v+vzLyhLHkWU0
#    M5XG3oeUUpFIND8eP61G9zB/1VO2Y0/d3BlloVDockvL2bONHV23o4aRkZFRuWrl/HlzLRZLKBzZs3ff30e2F6qBD1poOAylNFh0VWin2sXUXY1XCuP31tWbzIODgy6Xy+l0js0uhEx1OD765NOBgQFm7h8YrF63btt08V4ZFdopVldYkiHb1pDxPg4swooVK3v+6Y1Ewi6Xy2azPV4tEUAAbDbbjp2fBYJBZj55tmlZSVZfNa6upVkOKaoKeKqT/SGc/9cyf+Gi9AlprW3XausOjPh8STGUZSWdQEQFCSInQZpBX+2+/ed/bQZQNKXA
#    WVAcGMF0J68pZC0/kTmMcBB+mZw/eYpp8rHjJ/T+rm1zxLx09oSw8TwE4ZsKLkgyO4fpXPfdg7XfzpwxPcEWlxpjkAEyUJ7GmjdKJJkZsXE2e4ojEBzpar/5bineLDV1K1p6SRJsirOSkJaIBwZIw6WfT584fmzKs2V3eocsOQBDF9Cae1CRB2EBC0lSgU1vwPfFn3ziLk1zUH8IgyPsDWNXM3kiaL2Pv3wIGv6Pt2+3JzvsfTf0IpgSl+6RdvSOzEvj4gR2DwXDfo+mtMRkx7kBtA/gjJsJiDIYqOtkg8EACERwu91utzvTSld6yWNS
#    XYeEplSiojwbEhIS9tcdNAzzw81bnlzWwzM+UkohhCTKjhNpVqkpXUopA1FzMEyhUCglJblicYUAGhsb/X6/JsVEq5gQyykxiNdF0IDBYOb0SVnTyqa63W6DeSgMf4SlFFJKyaY5+l28/uDz8xc8V1rS2dl54/r1VAu2luPtEqzMw4vpaOunvoBpsVjeWb9eCNHW1jZamghCCCilxgoDqN6wMRyJNF24MLmoWCeU2sWCiWLBRDEjVcRpAGhV5eofjvyYnZOLcdMqpZ4GpaSk1NfXh8Lh7+q/T3M6MS5CyKXLV1xsvvxq1Wo8+WZPg0ZZ
#    ubm5DQ0NwWDw1JkzS5a+NCkrKzXNWVhUVFNT03Xr9uYtW2Ot1v+DnjDkmG0zMzNrNm167Y21SqCjs3No2JudlQkhv969u+HwYZ/PO16PDw35lLNHYxhGQmLi7Dlzly6uyM/PF0TX29tPnjp95fJvzDzWfbyz/wNZXAuckyZkmAAAACV0RVh0ZGF0ZTpjcmVhdGUAMjAxNi0xMC0wOFQwNDozMDo1NCswMjowMFEBTy0AAAAldEVYdGRhdGU6bW9kaWZ5ADIwMTYtMTAtMDhUMDQ6MzA6NTQrMDI6MDAgXPeRAAAAGXRFWHRTb2Z0d2Fy
#    ZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAAABJRU5ErkJggg==
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
    listformat = "pls"
    has_search = False
    titles = dict(playing = "Artist", bitrate=False)
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
            print a.text
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
        html = ahttp.get(self.base_url + self.catmap[cat])
        for i in range(2, int(conf.max_streams)/50): #conf.housemixes_pages):
            if html.find("latest/" + str(i)):
                html = html + ahttp.get(self.base_url + self.catmap[cat] + "/latest/%s" % i)
        html = re.sub("</body>.+?<body>", "", html, 100, re.S)
        
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
            }
            streams.append(r)

        #log.DATA( streams )
        return streams


    # Hook `url` access, look up actual mp3 file
    def row(self):
        r = ChannelPlugin.row(self)
        url = r.get("url")
        if url and url.find("/profile/") > 0:
            print url
            html = ahttp.get(url)
            ls = re.findall(r""" Mp3Url [\\\\:"]+ (http[^\\\\"]+) """, html, re.M|re.X)
            print ls
            if ls:
                r["url"] = ls[0]
        return r
