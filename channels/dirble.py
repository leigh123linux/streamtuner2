# encoding: UTF-8
# api: streamtuner2
# title: Dirble
# description: Song history tracker for Internet radio stations.
# url: http://dirble.com/
# version: 2.0
# type: channel
# category: radio
# config:
#    { name: dirble_api_key,  value: "a0bdd7b8efc2f5d1ebdf1728b65a07ece4c73de5",  type: text,  description: Required API access key. }
# png:
#    iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAAAA3NCSVQICAjb4U/gAAACP0lE
#    QVQokVVSO0+UURA9M/d+jyWbBVcQFSQhPqJSYBRFA5pVoFGURApjYYWtvYUNP8FKOwsttDFq
#    jMTEWEiDD0wETNSIxJC46yqEsCz7ve4di28hOO2cMzNnzqH+azcBACAiAgQg1EsAQESwCYBA
#    pwCxNowjI1v7YGLH0Y5iSQFhJEprYjZxtG13+/lCb2dOWxBBABiTrJSLkx8+z/xa0yRutml4
#    sC9X+qqJyFqTzTcPDfTup2p5NSTFSintOFmvZ7iv687Dl8/ezufaGgcHT2enKjpdbxMbRcnr
#    x09uT36JfJ9FWLtnCoWxkRM3Ris/F//Mlpce3LtvSsW6BhAxs5VgtVqtxUaJQCqPnr4ItXfr
#    Uve5fVM/PpbZzXgNniYCEaUs1spxdKIdBUvEsr4282nu29nuowdbmov2ytXRxukJBhGwwRCI
#    1F9pRbSjlytheTnY3t6iHCcMo9BYxtai1AymjSlRbII4YUcRAQQiMKWO0Vbahk2An3H9jJvU
#    IhEQCKD/TiJiZsXEzMxMYSy78rnOVvf34lISJ8R1pwGqpyCJkvUgCiyziFjJ5Fv7Tx5r07WJ
#    udJajRVDAI30TUQilG1qPry3I/Y9BThubmigb+R4x8L0m1fz5Ti3h0QE0ClcQCA+dflCz0VD
#    RKwUE5mgOvtu8u7z9wsVsyPPrBxfayqMjVtrMrmmI4f27swqkVS+GGMqy39nvy+W1uGxKL+h
#    u+uAt1KkwvVxAGJsEEWxEWzGm4iV8l1HM9K0BmEkrP8BlhoAUfmOxecAAAAASUVORK5CYII=
# priority: optional
# documentation: http://dirble.com/developer/api
#
# Hmm ok, the new v2 API isn't so bad after all.
# It actually contains streaming urls, and even
# station homepages now.
#
#  · No idea what status: or timedout: signify.
#  · Stream alternatives aren't yet sorted.
#  · Leave favicons to regular behaviour,
#    station banners are seemingly inaccessible.
#


import json
from config import *
from channels import *
import ahttp


# 
class dirble (ChannelPlugin):

    # control flags
    has_search = False
    listformat = "srv"
    titles = dict(listeners=False, playing="Location")
    base = "http://api.dirble.com/v2/{}"


    # Retrieve cat list and map
    def update_categories(self):
        cats = []
        for row in self.api("categories/tree"):
            print row
            cats += [row["title"]]
            self.catmap[row["title"]] = row["id"]
            if row.get("children"):
                cats += [[c["title"] for c in row["children"]]]
                for c in row["children"]:
                    self.catmap[c["title"]] = c["id"]
        self.categories = cats


    # Fetch entries
    def update_streams(self, cat, search=None):
        return [
            self.unpack(r)
               for r in
            self.api("category/{}/stations".format(self.catmap.get(cat, 0)), all=1)# per_page=200 won't work
        ]

    
    # Extract rows
    def unpack(self, r):
    
        # find stream (might select on `bitrate` or `format` if available)
        if len(r.get("streams", [])):
            s = r["streams"][0]
        else:
            return {}

        # rename fields
        return dict(
            genre = " ".join(c["slug"] for c in r["categories"]),
            title = r["name"],
            playing = "{country} {description}".format(**r),
            homepage = r["website"],
            url = s["stream"],
            format = s["content_type"],
            bitrate = s["bitrate"],
           # img = r["image"]["image"]["thumb"]["url"], # CDN HTTPS trip up requests.get
            status = "" if s["status"] else "gtk-stop",
            deleted = s["timedout"],
        )


    # Patch API url together, send request, decode JSON list
    def api(self, method, **params):
        params["token"] = conf.dirble_api_key
        try:
            r = ahttp.get(self.base.format(method), params)
            r = json.loads(r)
            if isinstance(r, dict) and "error" in r:
                log.ERR(r["error"])
                raise Exception
            if len(r) > conf.max_streams:
                del r[int(conf.max_streams):]
        except Exception as e:
            log.ERR("Dirble API retrieval failure:", e)
            r = []
        return r


