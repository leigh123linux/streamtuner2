# encoding: UTF-8
# api: streamtuner2
# title: di.fm
# description: "Digitally Imported", electronic music stations, + sky.fm and jazzradio
# url: http://di.fm/
# version: 0.2
# type: channel
# category: radio
# config: -
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAPhJREFUOI3Fkj9OAkEYxX87uyyDgSxDYUyMV/AgNtzAkngC7Ci4AB1rTbyADYml8QY2tiZQmC34o4Qs
#   CDMUZAnRIQMmhNfNfN9733vJg1PDK7RMG6gB/j/4sVdomYVIh743n+w4ITBhEZ2PEOmQbM+ERbRUywDwvfmE78aVlT9ONffPIx7f1+Rsr9TsgVS+cHmMpOChWqEsptZ5kNkpNXtWcr9+CcD1RY7X
#   j5ldYNvaTSfhJYkwQZ7x11/R33BGcCGwqk4TYG37YIHu7bl18e3zx/q/V4S7pwEjfWaduYvEpjQ7ixRrqWpIFbqcaKlAquy5BOJ9EhwXK0vYVWJw1aEpAAAAAElFTkSuQmCC
# priority: extra
#
# Just prints the public list of RadioTunes stations.
# Premium entries are available, but not fetched here.
# Public stations use a 64kbit/s AACP audio encoding.
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

