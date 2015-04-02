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
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAMAAAAoLQ9TAAAABGdBTUEAALGPC/xhBQAAAAFzUkdCAK7OHOkAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAAcVQTFRF
#   ////8PDw5OTk9/f3z9fYW3qnKFmLC0N9K1qVYYay2N7hl6zAHU6BYIqaqdDN4vvt9fzstuPeV42+JVmWn7TKi6XBFE+Og62t+/6f7/2MoMmMs+OPpdPDns/7ir/YGlehjqjE0tnfGFGTQXWuncmX6/tt
#   4vlvvfBv6vtsreGNbaXhdrTyXJXCY4m2JWStM2aZ4PhjtOhjy/FpeKioZaDoRYTAOXSpLGGgMXK/GlONlcxG1fZZfqyEX5XRY6TqPobZI2zCWJKqGVWbMHTHH12hT4BMt+0tgrFTfKt3XpG4WZfYR4vY
#   NHrTK3TMRYTCIlmdM3bNKmy8KGGWgrs3UYRXSHp0TISKS4WaPXq4OXrENHrNO3zRPnitXpZ/aqJrRnd5Y5VPWYVXNGeTNnO1M2OiLmy+PYPdSo3eUZHaU5DLg7cxtOwNntIaYpVrMGittLvEKV+lQofd
#   UZXoXp7rY6HfVoutsOUMQnOHdIurM2q2Y6TvbarqZJvFYpBlp9sSs+gMboag3t/dfZCqPWysSoLNYJvgYZSxfq5NNmF6MlmCcoab19nXqKyyZoSwTnawN2OfRGqXXXqanKKjzMzMt7e3o6SjsLKvtVfy
#   AwAAAAFiS0dEBxZhiOsAAAAJcEhZcwAAAEgAAABIAEbJaz4AAADxSURBVBjTY2AAAUYmIGBkZoACRhZWNnZ2Dk4uqAgjNw8vH7+AoJCwCCOIzywqJi4hKSUtIysnrwBSo6ikrKKqpq6hqaWto6QIVKCr
#   p69uYGBoZGxiYmrGyczAaG5haWVtbW1ja2fv4GjOyMDo5Ozi6ubu4enl7ePr5w8U8A8IDAoOCQ0Lj4iMigYJmDtHRcbExsUnJCYlR6YwMjCzpqalZ2SGZ2Vn5+TmsTIzMOcXFBYVl5TmZGeXlXPkgxxa
#   UZleVV1TW1efyNYAdmpjU3NLq1Zbe0dnVzfEM0w9vX3N/RMmTmqEeZd58pSpU6dNBnsWAEP5Nco3FJZfAAAAJXRFWHRkYXRlOmNyZWF0ZQAyMDE0LTA2LTAxVDAxOjI4OjA3KzAyOjAw7O+A+AAAACV0
#   RVh0ZGF0ZTptb2RpZnkAMjAxNC0wNi0wMVQwMToyODowNyswMjowMJ2yOEQAAAAASUVORK5CYII=
# documentation: http://api.icast.io/
#
#
# A modern alternative to ShoutCast/ICEcast.
# Streams are user-contributed, but often lack
# meta data (homepage) and there's no ordering
# by listeneres/popularity.
#
# OTOH it's every easy to interface with. Though
# the repeated API queries due to only 10 entries
# per query results make fetching slow.


import re
import json
from config import conf, dbg, __print__
from channels import *
import ahttp as http


# Surfmusik sharing site
class icast (ChannelPlugin):

    # description
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

