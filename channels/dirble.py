# encoding: UTF-8
# api: streamtuner2
# title: Dirble
# description: New open radio station directory.
# version: 0.1
# type: channel
# category: radio
# priority: optional
# documentation: http://dirble.com/developer/api
#
# Provides a nice JSON API, so is easy to support.
#
# However useful station information (homepage, etc.) only
# with extraneous requests. So just for testing as of now.
#
#


import re
import json
from config import conf, dbg, __print__
from channels import *
import ahttp as http


# Surfmusik sharing site
class dirble (ChannelPlugin):

    # description
    title = "Dirble"
    module = "dirble"
    homepage = "http://dirble.com/"
    has_search = True
    listformat = "audio/x-scpls"
    titles = dict(listeners=False, playing="Location")

    categories = []
    config = [
        {"name": "dirble_fetch_homepage",
         "value": 0,
         "type": "boolean",
         "description": "Also fetch homepages when updating stations. (This is slow, as it requires one extra request for each.)"
        }
    ]    
    catmap = {}
    
    base = "http://api.dirble.com/v1/%s/apikey/%s/"
    cid = "84be582567ff418c9ba94d90d075d7fee178ad60"

    # Retrieve cat list and map
    def update_categories(self):
        self.categories = []
        # Main categories
        for row in self.api("primaryCategories"):
            self.categories.append(row["name"])
            self.catmap[row["name"]] = row["id"]
            # Request subcats
            sub = []
            self.categories.append(sub)
            for subrow in self.api("childCategories", ["primaryid", str(row["id"])]):
                sub.append(subrow["name"])
                self.catmap[subrow["name"]] = subrow["id"]

    # Just copy over stream URLs and station titles
    def update_streams(self, cat, search=None):
    
        if cat:
            id = self.catmap.get(cat, 0);
            data = self.api("stations", ["id", str(id)])
        elif search:
            data = self.api("search", ["search", search])
        else:
            pass

        r = []
        for e in data:
            r.append(dict(
                id = e["id"],
                genre = str(cat),
                status = e["status"],
                title = e["name"],
                playing = e["country"],
                bitrate = self.to_int(e["bitrate"]),
                url = e["streamurl"],
                homepage = e.get("homepage") or self.get_homepage(e["id"], e["name"]),
                format = "audio/mpeg"
            ))
        return r

    # Request homepage for stations, else try to deduce Dirble page
    def get_homepage(self, id, name):
        if conf.dirble_fetch_homepage:
            return self.api("station", ["id", str(id)])["website"]
        else:
            name = re.sub("[^\w\s]+", "", name)
            name = re.sub("\s", "-", name)
            return "http://dirble.com/station/" + name.lower();

    # Patch together
    def api(self, method, params=[]):
        j = http.get((self.base % (method, self.cid)) + "/".join([str(e) for e in params]))
        r = json.loads(j);
        return r


