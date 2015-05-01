# encoding: UTF-8
# api: streamtuner2
# title: 8tracks
# description: radio created by people, not algorithms
# version: 0.1
# type: channel
# category: collection
# config:
#   { name: eighttracks_apikey,  value: "",  type: text,  description: Custom API access key. }
#   { name: eighttracks_safe,  value: 1,  type: bool,  description: Filter explicit/NSFW tracks. }
# priority: optional
# url: http://8tracks.com/
# documentation: https://8tracks.com/developers
#
# Requires a pingback on playing a track
#  → which is near impossible without player control.
#  → Automatic/implied notifications could work.
#  → Or checking via dbus/mpris even (less assertable).
#  → Else a customized playlist export with the reporting URL as
#    faux first entry even.
#  → Or an external URL redirector just (api.i-o/cache service).
#

import json
import re
from config import *
from channels import *
import ahttp


# 8tracks mix tapes
class eighttracks (ChannelPlugin):

    # description
    has_search = False
    listformat = "pls"
    titles = dict(listeners=False, playing="Location")

    categories = ["none"]
    catmap = {}
    
    base = "http://8tracks.com/mixes/1?format=json&api_key=%s" # or X-Api-Key: header
    cid = ""


    # Mix types, genres, etc?
    def update_categories(self):
        self.categories = []


    # Excerpt newest or most popular
    def update_streams(self, cat, search=None):
        row = {
           "url": "urn:8tracks",
           "id": "$mix_id-12345",
        }
        return []

    
    # Craft a stream URL with play token
    def row(self):
        self.status("Retrieving playback token...")
        r = ChannelPlugin.row(self)
        token = self.api("sets/new")["play_token"]
        track = self.api("sets/{}/play".format(r["id"]))
        r["url"] = track["set"]["track"]["track_file_stream_url"]

    # Call after .play()    
    def report(self, mixid)
        self.api("sets/{}/report".format(mixid), {"track_id": mixid, "mix_id": mixid})
    
    #def play(self):
    #    ChannelPlugin.play(self)
    #    self.report()


    # Patch API url together, send request, decode JSON and whathaveyou
    def api(self, method="mix_sets/all", *params):
        params.update({
            "api_version": 3,
            "api_key": conf.eighttracks_apikey or self.cid,
           #"include": "mixes",
        })
        try:
            j = ahttp.get("http://8tracks.com/{}.json".format(method), params)
            r = json.loads(j)
            # test for mishaps
            if "errors" in r and r["errors"]:
                self.status(r["errors"])
                raise Exception(r)
            return r
        except Exception as e:
            log.ERR("8tracks API request failed:", e)
        return []


