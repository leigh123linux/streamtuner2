# encoding: UTF-8
# api: streamtuner2
# title: radio.net
# description: Europe's biggest radio platform
# url: http://radio.net/
# version: 0.6
# type: channel
# category: radio
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAt0lEQVR42mNgYGD4r+Ar/F/BDwkD+SBxojBMs1mLPBArgGlFqEEENYMNQNLsukIDYkirAvGu
#   ABsA1OC6XOP/5f8nwIaYAg0k2gBFsAsgTgcZkvnfDugFEeK9AFKsCPMG0CU6eZJgQ4R1eP8H7LLEivWyFJANQcQCLPBAmkGG4MJohmA6C6QA5gI5OxEUDNII
#   MwSvASBFIA3ociCxkWQAKMDICkSQIpgh2LDnSmP80YhsCFEJiRIMADpmeUOpqgjRAAAAAElFTkSuQmCC
# priority: optional
# extraction-method: regex
#
# Radio.net lists around 20.000 worldwide radio stations.
# A maximum of three pages from each genre are fetched here,
# some of the empty categories already omitted.
#
# The website heavily depends on JavaScript, a Flash player,
# some social tracking cookies. But still feasible to access
# per custom JSON extractor.
#
# May require refreshing the station lists once in a while,
# because there's an API key in each JSON station info URL.


import time
import json
import re
from config import *
from channels import *
import ahttp
import action


# hook special JSON format in to avoid grepping images by generic handler
action.playlist_fmt_prio.insert(5, "rnjs")
action.playlist_content_map.insert(7, ("rnjs", r'"logo175x175rounded"'))
action.extract_playlist.extr_urls["rnjs"] = dict(
    url   = r" (?x) \"streamUrl\" \s*:\s* \"(\w+:\\?/\\?/[^\"]+)\" ",
    title = r" (?x) \"(?:description|seoTitle)\" \s*:\s* \"([^\"]+)\" ",
    unesc = "json",
)


# Radio.net
#
# · Uses HTML block-wise regex extraction.
#   → <a href="stationname.radio.net"> <img…> <strong>…</strong> <small>…</small>
#
# · There's an API key in each page listing, contained in a script block
#   as `apiKey: '…'?`
#
# · Which is needed for generating the station info JSON urls:
#   → https://api.radio.net/info/v2/search/station?apikey=…&pageindex=1&station=STNAME
#
# · To extract these JSON info targets, a custom extraction recipie is injected
#   into the action module.
#   → "streamUrl": and "description": are scanned for.
#
class radionet (ChannelPlugin):

    # control flags
    has_search = False
    audioformat = "audio/mpeg"
    listformat = "rnjs"
    titles = dict(listeners=False, playing="Description")

    # sources
    apiPrefix = "https://api.radio.net/info/v2"
    genre_url = "http://www.radio.net/genre/{}/"
    apiKey = None
    
    
    # Retrieve cat list and map
    def update_categories(self):
        html = ahttp.get("http://www.radio.net/")
        self.set_key(html)
        ls = re.findall("""<li><a class="language-info".*?>([\w\s']+)</a>""", html)
        self.categories = [i for i in ls][0:-18]


    # Fetch entries
    def update_streams(self, cat, search=None):

        # category page, get key
        html = ahttp.get(self.genre_url.format(cat))
        for p in range(2, 4):
            if html.find('"?p={}">'.format(p)) >= 0:
                html += ahttp.get(self.genre_url.format(cat) + "?p={}".format(p))
        self.set_key(html)
        r = []

        # split station blocks
        for row in re.split("""<div class="stationinfo""", html)[1:]:
        
            # extract text fields
            d = re.findall("""
              <a\s+href="(?:https?:)?(//([\w-]+)\.radio\.net/?)" .*?
              <img\s+src="([^<">]+)" .*?
              <strong[^>]*>(.*?)</strong> .*?
              <small[^>]*>\s*(.*?)\s*</small> .*?
            """, row, re.X|re.S)
            
            # refurbish extracted strings
            if d and len(d) and len(d[0]) == 5:
                href, name, img, title, desc = d[0]
                r.append(dict(
                    name = name,
                    genre = cat,
                    title = unhtml(title),
                    playing = unhtml(desc),
                    url = self._url(name),
                    homepage = "http:{}".format(href),
                    img = img,
                ));
        return r
    

    # Patch together JSON station info URL
    def _url(self, name):
        return \
        "{}/search/station?apikey={}&pageindex=1&station={}".format(
            self.apiPrefix, self.apiKey, name
        )      # '?_={time}&' is omitted here, only relevant to jQuery/AJAX,
               # and just made bookmarks.is_in() fail due to randomized URLs


    # extract JavaScript key from any HTML blob (needed for station query)
    def set_key(self, html):
        ls = re.findall("""apiKey: '(\w+)'""", html)
        if ls:
            self.apiKey = ls[0]



