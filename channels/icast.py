# encoding: UTF-8
# api: streamtuner2
# title: iCast.io
# description: Open collaborative stream directory
# version: 0.1
# type: channel
# url: http://www.icast.io/
# category: radio
# priority: optional
# config: -
# documentation: http://api.icast.io/
#
# A modern alternative to ShoutCast/ICEcast.
# Streams are user-contributed, but often lack meta data (homepage) and
# there's no ordering by listeneres/popularity.
#
# OTOH it's every easy to interface with. Though the repeated API queries
# due to 10-entries-per-query results make fetching slow.
#
#
#

import re
import json
from config import conf, dbg, __print__
from channels import *
import ahttp as http


# Surfmusik sharing site
class icast (ChannelPlugin):

    # description
    title = "iCast"
    module = "icast"
    homepage = "http://www.icast.io/"
    has_search = True
    listformat = "audio/x-scpls"
    titles = dict(listeners=False, bitrate=False, playing=False)

    categories = []
    
    base = "http://api.icast.io/1/"
    

    # Categories require little post-processing, just dict into list conversion
    def update_categories(self):
        self.categories = []
        for genre,cats in json.loads(http.get(self.base + "genres"))["genres"].items():
            self.categories.append(genre.title())
            self.categories.append([c.title() for c in cats])

    # Just copy over stream URLs and station titles
    def update_streams(self, cat, search=None):
    
        if cat:
            data = self.api("stations/genre/", cat.lower(), {})
        elif search:
            data = self.api("stations/search", "", {"q": search})
        else:
            pass

        r = []
        for e in data:
            r.append(dict(
                genre = " ".join(e["genre_list"]),
                url = e["streams"][0]["uri"],
                format = e["streams"][0]["mime"],
                title = e["name"],
                #playing = " ".join(e["current"].items()),
            ))

        return r

    # fetch multiple pages
    def api(self, method, path, params):
        r = []
        while len(r) < int(conf.max_streams):
            data = json.loads(http.get( self.base + method + path, params))
            r += data["stations"]
            if len(r) >= data["meta"]["total_count"] or len(data["stations"]) < 10:
                break
            else:
                params["page"] = int(data["meta"]["current_page"]) + 1
                self.parent.status(params["page"] * 9.5 / float(conf.max_streams))
            #__print__(dbg.DATA, data)
        return r

