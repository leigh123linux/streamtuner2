# encoding: UTF-8
# api: streamtuner2
# title: Dirble
# description: Open radio station directory.
# version: 0.2
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
# Uh, and API is appearently becoming for-pay (two days
# after writing this plugin;). So ST2 users may have to
# request their own Dirble.com key probably.
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
        {"name": "dirble_api_key",
         "value": "",
         "type": "text",
         "description": "Custom API access key."
        },
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
            for subrow in self.api("childCategories", "primaryid", row["id"]):
                sub.append(subrow["name"])
                self.catmap[subrow["name"]] = subrow["id"]


    # Just copy over stream URLs and station titles
    def update_streams(self, cat, search=None):
    
        if cat:
            id = self.catmap.get(cat, 0);
            data = self.api("stations", "id", id)
        elif search:
            data = self.api("search", "search", search)
        else:
            pass

        r = []
        for e in data:
            # skip musicgoal (resolve to just a blocking teaser)
            if e["streamurl"].find("musicgoal") > 0:
                continue
            # append dict after renaming fields
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
            try:
                return self.api("station", "id", id)["website"]
            except:
                None
        name = re.sub("[^\w\s]+", "", name)
        name = re.sub("\s", "-", name)
        return "http://dirble.com/station/" + name.lower();


    # Patch API url together, send request, decode JSON and whathaveyou
    def api(self, *params):
        method = params[0]
        try:
            j = http.get((self.base % (method, conf.dirble_api_key or self.cid)) + "/".join([str(e) for e in params[1:]]))
            r = json.loads(j);
        except:
            r = []
        if len(r) and "errormsg" in r[0]:
          __print__(dbg.ERR, r[0]["errormsg"]) 
          r = []
        return r


