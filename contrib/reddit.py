# encoding: UTF-8
# api: streamtuner2
# title: reddit⛱music
# description: Music recommendations from reddit /r/music and associated subreddits.
# version: 0.6
# type: channel
# url: http://reddit.com/r/Music
# category: playlist
# config:
#   { name: reddit_pages, type: int, value: 2, description: Number of pages to fetch. }
#   ( name: kill_soundcloud, type: boolean, value: 1, description: Filter soundcloud links (no player configurable). )
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQBAMAAADt3eJSAAAAJ1BMVEUAAAAcICX/AABHSk1jZ299hYz/bmajq6//lY/d0M3C1+3T7P38+/iaLhuGAAAAAXRSTlMAQObYZgAAAAFiS0dEAIgF
#   HUgAAAAJcEhZcwAACxMAAAsTAQCanBgAAAAHdElNRQffBRUXIyQbWArCAAAAh0lEQVQI12Pg3g0BDLtXrVq1eveq3Qy7gIxCU9dqEGO11/ZKbzBDenUIUM3u7cGi1UDFW0TE55wsdpZikAw/
#   eebMnMmHGVxqDuUc0zzpynD4zIk5J3vOSDNsOQMG1gy7bI5HTq85Ws2wu/jM9PIzrkArdhmXlzuuXg00eVd5+epVqxmgrtgNAOWeS1KYtcY4AAAAAElFTkSuQmCC
# priority: extra
#
# Just imports Youtube links from music-related subreddits.
# Those are usually new bands or fresh releases, or favorite
# user selections. Soundcloud and weblinks are filtered out.
#
# This plugin currently uses the old reddit API, which will
# be obsolete by August. It's thus a temporary channel, as
# migrating to OAuth or regressing to plain HTML extraction
# is not very enticing.


import json
import re
from config import *
from channels import *
import ahttp


# reddit.com
#
# Uses old API requests such as:
#  → http://www.reddit.com/r/music/new.json?sort=new
#
class reddit (ChannelPlugin):

    # control attributes
    has_search = False
    listformat = "srv"
    audioformat = "video/youtube"
    titles = dict(playing="submitter", listeners="votes", bitrate=False)
    
    # just subreddit names to extract from
    categories = [
        "radioreddit",
        "Music",
        "music_discovery",
        "trueMusic",
        "futurebeats",
        "futurefunkairlines",
        "ElectronicMusic",
        ["acidhouse", "ambientmusic", "bigbeat", "breakbeat", "breakcore", "chillout",
        "darkstep", "deephouse", "DnB", "Dubstep", "EDM", "electronicdancemusic", "electrohouse",
        "electropop", "funkhouse", "gabber", "hardhouse", "house", "industrialmusic",
        "minimal", "partymusic", "psytrance", "Techno", "Trance", "tech_house", "witchhouse"],
        "indiewok",
        "Jazz",
        "ClassicalMusic",
        ["baroque", "composer", "contempory", "ChamberMusic",
        "choralmusic", "EarlyMusic", "ElitistClassical", "opera", "pianocovers"],
        "ListenToThis",
        "ListenToUs",
        "WhatIListenTo",
        "ListenToConcerts",
        "HeadBangToThis",
        "unheardof",
        "under10k",
        "MusicForConcentration", ["MusicToSleepTo"],
        "gamemusic", 
        "2010sMusic", ["2000sMusic", "90sMusic", "80sMusic", "70sMusic", "60sMusic",
        "50sMusic", "SoundsVintage"],
        "PopMusic",
        "Catchysongs",
        "CoverSongs",
        ["ICoveredASong", "MyMusic", "UserProduced", "RepublicOfMusic", "RoyaltyFreeMusic"],
        "musicvideos",
        "Frisson",
        "Turntablists",
    ]


    # static
    def update_categories(self):
        pass


    # Extract video/music news links
    def update_streams(self, cat, search=None):
        
        # radioreddit
        if cat == "radioreddit":
           return self.radioreddit()

        # collect links
        data = []
        after = None
        for i in range(1, int(conf.reddit_pages) + 1):
            j = ahttp.get(
                "http://www.reddit.com/r/{}/new.json".format(cat.lower()),
                { "sort": "new", "after": after }
            )
            try:
                j = json.loads(j)
            except Exception as e:
                log.ERR("Reddit down?", e)
                break
            if j.get("data",[]).get("children"):
                data += j["data"]["children"]
            else:
                break
            if j.get("data",[]).get("after"):
                after = j["data"]["after"]
            else:
                break

        # convert
        r = []
        for row in (ls["data"] for ls in data):

            # find links in text posts
            text_urls = re.findall("\]\((https?://(?:www\.)?youtu[^\"\'\]\)]+)", row.get("selftext", ""))
            url_ext = (re.findall("\.(\w+)$", row["url"]) or [None])[0]
            listformat = "href"

            # Youtube
            if re.search("youtu", row["url"]):
                format = "video/youtube"
                listformat = "srv"
            # direct MP3/Ogg
            elif url_ext in ("mp3", "ogg", "flac", "aac", "aacp"):
                format = "audio/" + url_ext
                listformat = "srv"
            # playlists?
            elif url_ext in ("m3u", "pls", "xspf"):
                listformat = url_ext
                format = "audio/x-unknown"
            # links from selftext
            elif text_urls:
                row["url"] = text_urls[0]
                format = "video/youtube"
            # filter out Soundcloud etc.
            else:
                continue

            # repack into streams list
            r.append(dict(
                title = row["title"],
                url = row["url"],
                genre = re.findall("\[(.+?)\]", row["title"] + "[-]")[0],
                playing = row["author"],
                listeners = row["score"],
                homepage = "http://reddit.com{}".format(row["permalink"]),
                img = row.get("thumbnail", ""),
                format = format,
                listformat = listformat,
            ))
        return r        


    # static station list
    def radioreddit(self):
        return [
            dict(
                genre=id, title=id.title(),
                url="http://cdn.audiopump.co/radioreddit/"+id+"_mp3_128k",
                format="audio/mpeg", homepage="http://radioreddit.com/",
                listformat="srv"
            )
            for id in [
                "main", "random", "rock", "metal", "indie",
                "electronic", "hiphop", "talk", "festival"
            ]
        ]
    
