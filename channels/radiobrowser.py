# encoding: UTF-8
# api: streamtuner2
# title: RadioBrowser
# description: Community collection of stations; votes, clicks, homepage links.
# version: 0.1
# type: channel
# url: http://www.radio-browser.info/
# category: radio
# priority: optional
# config:
#   { type=select, name=radiobrowser_cat, value=tags, select="tags|countries|languages", description=Which category types to list. }
# documentation: http://www.radio-browser.info/#ui-tabs-7
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAMCAMAAABcOc2zAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAACQ1BMVEWNYNOIWNFyOsZtNcFx
#   N8hxN8hxN8hxN8hxN8hxN8hxN8dtNcFuNcJ+Ss2NX9N6T7uNX9NxPL9jMLBtNcBkMbFqNLuCT89wRq6MXtOATc17Rsp8SMl6Rcl6RctrQqmpht1qQ6PUxex6WqnXye18XarYyu3QyNzp5u739/jh3Ojd
#   2OX4+Pl7XKrYy+3i3eh8Y6Dg2+i2q8ecjrGqm8Krm8LTzN+ikbunl8D5+fl7W6rZy+7z8fTk4Or29fjAuM3Dv8rx7vTs6vHy8PTh3Ojy8PX5+fl6Wqraze75+fn5+vn6+vn6+vn6+vl6WqrMuOl1U6iR
#   bMmNbb2NbryOb72PcL6Qcb+Rcr+SdMCTdcGUdsGVd8KWeMOXesSZfMWMa71cNpSLW9JxN8hxN8hxN8hxN8hxN8hrNL2NX9OMXdJ+Ss1/S85/S85/S85+Ss18SMqHV9GMXdK/p+W/p+W+peW+peS9pOS9
#   o+S8ouS7oeO6oOO5nuO4neK3m+K3m+Kqidv5+fn5+vn5+fn5+fn5+fn5+fn5+fn4+fn4+Pn4+Pn4+Pn4+Pn5+fnl3vD5+fn5+fn7+/r6+vn5+fn5+vn5+vn5+vn5+fn6+/r6+vr5+fn6+/rp4/H6+vn0
#   8/X08vbz8vX08/b29vf6+/ro4vH7+/r6+/ro4vH6+vn6+vrn4fH6+/n6+vr6+/r6+vn6+/r6+vn6+vn7+/ro4fHt6PXu6fXu6vXv6vXv6/Xw6/bw7Pbw7fbx7fbx7vby7vby7/fz8ffd0+7///+qD5Mw
#   AAAAYHRSTlPJ4/Hz8/Lx7+3s6ufi08N9/fve8/bo//T8/vb6/fr67eL02vbc9/Tt//3v/N34/5aO/MWeoM7Rbene+f7E0PykaWqx3K333/v//Pv7/eD34Z/m7O3v8fL09vf5+vv8/9Pw7ECfAAAAAWJL
#   R0TAE2Hf+AAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB98EARcyBebz0PQAAADXSURBVAjXAcwAM/8AAAECAwQFBgcICQoLDA0ODwAQYBESE2FiY2RlZhQVFmcXABhoGRobaWprbG1uHB1vcB4A
#   H3Fyc3R1dnd4eXp7fH1+IAAhf4CBgoOEhYaHiImKi4wiACONjo+QkZKTlJWWl5iZmiQAJZucJiconZ6foCkqK6GiLAAtoy4vMDEyMzQ1Njc4pKU5ADqmOzw9Pj9AQUJDREWnqEYAR6mqq6xISUpLTK2u
#   r7CxTQBOsrO0tba3uLm6u7y9vr9PAFBRUlNUVVZXWFlaW1xdXl9emUehk/NThwAAACV0RVh0ZGF0ZTpjcmVhdGUAMjAxNS0wNC0wMlQwMTo0OTozOSswMjowMH98i/gAAAAldEVYdGRhdGU6bW9kaWZ5
#   ADIwMTUtMDQtMDJUMDE6NDk6MTcrMDI6MDAcO09kAAAAAElFTkSuQmCC
# x-icon-src: openclipart:tape.png
# x-service-by: segler_alex
#
#
# Radio-Browser is a community-collected list of internet radios.
# Currently lists 4400 streaming stations, and tracks favourited
# entries. Furthermore includes station homepage links!
#
# Also has a neat JSON API, so is quite easy to support.


import re
import json
from config import conf, dbg, __print__
from channels import *
import ahttp as http


# API endpoints:
# http://www.radio-browser.info/webservice/json/countries
# http://www.radio-browser.info/webservice/json/languages
# http://www.radio-browser.info/webservice/json/tags
# http://www.radio-browser.info/webservice/json/stations/topclick
# http://www.radio-browser.info/webservice/json/stations/topvote
# http://www.radio-browser.info/webservice/json/stations
# http://www.radio-browser.info/webservice/json/stations/searchterm
# http://www.radio-browser.info/webservice/json/stations/bytag/searchterm
#
# ENTRY sets:
# {"id":63,"name": "Energy Sachsen", "url":"http://www.energyradio.de/sachsen",
#  "homepage":"http://www.energy.de", "favicon":"http://www.energy.de/favicon.ico",
#  "tags":"Pop Dance RnB Techno","country":"Germany","subcountry":"","language":"German",
# "votes":4,"negativevotes":10},
#
class radiobrowser (ChannelPlugin):

    # description
    homepage = "http://www.radio-browser.info/"
    has_search = True
    listformat = "audio/x-scpls"
    titles = dict(listeners="Votes+", bitrate="Votes-", playing="Country")

    categories = []
    pricat = ("topvote", "topclick")
    catmap = { "tags": "bytag", "countries": "bycountry", "languages": "bylanguage" }
    
    base = "http://www.radio-browser.info/webservice/json/"
    

    # votes, and tags, no countries or languages
    def update_categories(self):
        self.categories = list(self.pricat)
        for sub in [conf.radiobrowser_cat]:
            cats = []
            for entry in self.api(sub):
                if entry["value"] and len(entry["value"]) > 1:
                    cats.append(entry["value"])
            self.categories.append(sub)
            self.categories.append(cats)
            

    # Direct mapping
    def update_streams(self, cat, search=None):

        if cat:
            if cat in self.pricat:
                data = self.api("stations/" + cat)
            elif cat in ("tags", "countries", "languages"):
                return [dict(genre="-", title="Placeholder category", url="offline:")]
            else:
                data = self.api("stations/" + self.catmap[conf.radiobrowser_cat] + "/" + cat)
        elif search:
            data = self.api("stations/" + cat)
        else:
            return []

        r = []
        for e in data:
            r.append(dict(
                genre = e["tags"],
                url = e["url"],
                format = "audio/mpeg",
                title = e["name"],
                homepage = e["homepage"],
                playing = e["country"],
                listeners = int(e["votes"]),
                bitrate = - int(e["negativevotes"]),
            ))
        return r


    # fetch multiple pages
    def api(self, method, params={}):
        j = http.get(self.base + method, params)
        try:
            return json.loads(j, strict=False)   # some entries contain invalid character encodings
        except:
            return []

