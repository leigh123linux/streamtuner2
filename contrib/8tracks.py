# encoding: UTF-8
# api: streamtuner2
# title: 8tracks
# description: radio created by people, not algorithms
# version: 0.1
# type: channel
# category: collection
# config:
#   { name: 8tracks_api_key,  value: "",  type: text,  description: Custom API access key. }
# priority: optional
# url: http://8tracks.com/
# documentation: https://8tracks.com/developers
#
# Requires a pingback on playing, which is near impossible to implement
# without also controlling the player. Automatic/implied notifications
# could work, or checking via dbus/mpris even.
#

import re
import json
from config import *
from channels import *
import ahttp as http


# Surfmusik sharing site
class _8tracks (ChannelPlugin):

    # description
    title = "8tracks"
    module = "8tracks"
    homepage = "http://8tracks.com/"
    has_search = False
    listformat = "audio/x-scpls"
    titles = dict(listeners=False, playing="Location")

    categories = ["none"]
    catmap = {}
    
    base = "http://8tracks.com/mixes/1?format=json&api_key=%s" # or X-Api-Key: header
    cid = ""


    # Retrieve cat list and map
    def update_categories(self):
        self.categories = []

    # Just copy over stream URLs and station titles
    def update_streams(self, cat, search=None):
        return []

    # Patch API url together, send request, decode JSON and whathaveyou
    def api(self, *params):
        r = []
        return r


# Need to rename the class, else plugin loader won't find it.
globals()["8tracks"] = _8tracks
_8tracks = None
