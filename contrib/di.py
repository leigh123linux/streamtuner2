# encoding: UTF-8
# api: streamtuner2
# title: di.fm / sky.fm
# description:
# url: http://di.fm/
# version: 0.1
# type: channel
# category: radio
# config: -
# png:
# priority: extra
#
# Just prints the public list of RadioTunes stations.
# Premium entries are available, not fetched here.
# Free entries use a 64kbit/s AACP audio encoding.
#
# Alternative JSON list: http://listen.di.fm/public3
# Required unpacking a complex category association,
# and only adds a few more descriptions.



from config import *
from channels import *
import ahttp
import json


# di.fm
class di (ChannelPlugin):

    # control flags
    has_search = False
    listformat = "pls"
    audioformat = "audio/aac"
    titles = dict(listeners=False, bitrate=False, playing=False)
    categories = ["di.fm", "sky.fm", "jazzradio.com"]
               # sky.fm is an alias of "radiotunes.com"

    # static
    def update_categories(self):
        pass

    # ignore category, because there is just but one
    def update_streams(self, cat, search=None):
        ls = json.loads(ahttp.get("http://listen.{}/public1".format(cat)))
        rows = [
           dict(genre=row["key"], title=row["name"], url=row["playlist"], id=row["key"],
                homepage="http://www.{}/{}".format(cat, row["key"]), bitrate=64)
           for row in ls
        ]
        return rows    
