# encoding: UTF-8
# api: streamtuner2
# title: Dirble
# description: Song history tracker for Internet radio stations.
# url: http://dirble.com/
# version: 2.3
# type: channel
# category: radio
# config:
#    { name: dirble_api_key,  value: "",  type: text,  description: Alternative API access key., hidden: 1 }
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
# extraction-method: json
#
#
# Dirble is a user-contributed list of radio stations,
# auto-updating song titles and station information.
# Homepages are there now, and thus favicons readily
# available. Extra station banners aren't fetched.
#
# It provides a JSON API. Since plugin version 2.3
# we're back to slower pagination requests however.
#
# Response times are fixed now by overriding the HTTP
# encoding. (A python-requests issue mostly).


import json
from config import *
from channels import *
import ahttp


# Dirble
#
# Hmm ok, the new v2 API isn't so bad after all.
# It actually contains streaming urls, and even
# station homepages now.
#
#  · No idea what status: or timedout: mean,
#    just mapped to `deleted` and `status`
#  · Stream alternatives are meanwhile scanned
#    for "best" format+bitrate combinations.
#  · Leave favicons to regular behaviour,
#    station banners are not accessible per CDN.
#
class dirble (ChannelPlugin):

    # control flags
    has_search = False
    listformat = "srv"
    titles = dict(playing="Location")
    base = "http://api.dirble.com/v2/{}"
    key = "a0bdd7b8efc2f5d1ebdf1728b65a07ece4c73de5"


    # Retrieve cat list and map
    def update_categories(self):
        cats = []
        for row in self.api("categories/tree"):
            cats += [row["title"]]
            self.catmap[row["title"]] = row["id"]
            if row.get("children"):
                cats += [[c["title"] for c in row["children"]]]
                for c in row["children"]:
                    self.catmap[c["title"]] = c["id"]
        self.categories = ["Popular", "Recent"] + cats


    # Fetch entries
    def update_streams(self, cat, search=None):
        self.progress(1)
        if search:
            r = self.api("search", query=search, page=0, pages=1)
        elif cat in ("Popular", "Recent"):
            r = self.api("stations/{}".format(cat.lower()), pages=15)
        else:
            r = self.api("category/{}/stations".format(self.catmap.get(cat, 0)), pages=10)
        return [self.unpack(row) for row in r]

    
    # Extract rows
    def unpack(self, r):
        listeners = 0

        # find stream
        if len(r.get("streams", [])):

            # compare against first entry
            s = r["streams"][0]

            # select "best" stream if there are alternatives
            if len(r["streams"]) > 0:
                for alt in r["streams"]:
                    listeners += alt.get("listeners", 0)

                    # set defaults
                    if not alt.get("content_type"):
                        alt["content_type"] = "?"
                    if not alt.get("bitrate"):
                        alt["bitrate"] = 16
                    alt["content_type"] = alt["content_type"].strip()  # There's a "\r\n" in nearly every entry :?
                
                    # weight format with bitrate
                    cur_q = self.format_q.get(  s["content_type"], "0.9") \
                            * s.get("bitrate", 32)
                    alt_q = self.format_q.get(alt["content_type"], "0.9") \
                            * alt.get("bitrate", 32)

                    # swap out for overall better score
                    if alt_q > cur_q:
                        s = alt
                        #log.DATA_BETTER_STREAM(s, "←FROM←", r)

            # fix absent audio type
            if not s.get("content_type") or len(s["content_type"]) < 7:
                s["content_type"] = "audio/mpeg"
            #log.DATA(s)

        else:
            return {}

        # rename fields
        return dict(
            genre = " ".join(c["slug"] for c in r["categories"]),
            title = r["name"],
            playing = "{} {}".format(r.get("country"), r.get("description", "")),
            homepage = ahttp.fix_url(r["website"]),
            url = s["stream"],
            format = s["content_type"],
            bitrate = s["bitrate"],
            listeners = listeners,
            img = r.get("image", {}).get("thumb", {}).get("url", ""), # CDN HTTPS trip up requests.get
            img_resize = 32,
            state = self.state_map.get(int(s["status"]), ""),
            deleted = s.get("timedout", False),
        )

    # Streams contain a `status`, here mapped onto arbitrary Gtk icons        
    state_map = {0:"gtk-media-pause", 1:"gtk-media-next", 2:"gtk-media-rewind"}

    # Weighting bitrate and audio format for alternative stream URLs
    format_q = {"?":0.75, "audio/mpeg":1.0, "audio/aac":1.25, "audio/aacp":1.35, "audio/ogg":1.50}


    # Patch API url together, send request, decode JSON list
    def api(self, method, pages=1, **params):
        # pagination parameters
        if pages > 1:
            params["page"] = 0
            params["per_page"] = 30
            params["offset"] = 0
        params["token"] = conf.dirble_api_key or self.key
        try:
            r = []
            # paginate results
            for params["page"] in range(0, pages):
                self.progress(pages)
                # send HTTP request and extract JSON
                add = ahttp.get(self.base.format(method), params, encoding="utf-8")
                add = json.loads(add)
                # check for errors
                if isinstance(add, dict) and add.get("error"):
                    if r:
                        log.WARN(add["error"])
                        break
                    else:
                        raise Exception(add)
                r += add
            # cut down stream list
            self.progress(0)
            #if len(r) > int(conf.max_streams):
            #    del r[int(conf.max_streams):]
        except Exception as e:
            log.ERR("Dirble API retrieval failure:", e)
            r = []
        return r


