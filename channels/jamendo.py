# encoding: UTF-8
# api: streamtuner2
# title: Jamendo
# description: A license-free music collection and artist hub.
# type: channel
# version: 2.2
# category: radio
# url: http://jamendo.com/
# depends: json
# config: 
#    { name: jamendo_stream_format, value: ogg,  type: select,  select: "ogg=Vorbis, 112kbit/s|mp32=MP3, 192kbit/s|mp31=MP3, 96kbit/s|flac=FLAC, ≳600kbit/s",  description: "Audio format for tracks, albums, playlists." }
#    { name: jamendo_image_size,    value: 35,   type: select,  select: "25=25px|35=35px|50=50px|55=55px|60=60px|65=65px|70=70px|75=75px|85=85px|100=100px|130=130px|150=150px|200=200px|300=300px",  description: "Preview images size (height and width) for albums or tracks." }
#    { name: jamendo_count,         value: 1,    type:text,     description: "How many result sets (200 entries each) to retrieve." }
# priority: default
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAwNJREFUOI1lk0toXGUYhp/v/8+ZzDQzmdZMZ8YSkxIQCWTTYsALLsQsUsWFQgJeEJQqIigUvBK0FBQULIJKMEKrFjdOW9xoW1AbRdRCEYtd2GCxxUQbk8bMrTNnzpn//1xMLYLv6l2877N7oBcB0GMY
#   IAUY/p9w/glCrVzby3+LVqaxM4dx+inQV7KIHcKYAbzG4FYgqcmudYBAF+jKnT2QAExPYysVHCdKRQgewwRT0B1FfQboYsLLeE7hk4Oo/iD3rFit4GQGRCsYwJMt7yQVfrS6Go3HUQtvskiwCWM82qlijGdbaUsbTV5G/X65+y+rCzgBRI+VbsSmvvltqVkuX78t6rvpKWtvuMsgOfHtJia66OPz
#   86564UtDkA2Lm/VJYF6mLgXo50X0xNAHy4cK2jk+diVe+1FVVX/57oIuL66qqmriVF23rZ1TjyTLH2YT/WJ4TY+XRgAMKqNgJ41vebbvTgeFneo6Tb567zPmHn+LxdPnCIxHTFrt2CtB/8BWqtVOAewDWgGDmHG0u1VtztjC7SLqRSUkM5Clsd5ibs/7nDzyLd51xfQPq82PKS5SsHfQAEMsIZG3
#   khgvJqUqBhFBnSeTS1O/XOPou0eoVxuIsfgkRDsqxBIQgaEVXyIyTVdvGFdbQlD1LibpJDTWG9w8NcHsgRfIb8ni4qbIxhISGU87+Z00BMTuDPhfg47b4X4+oHZ4VxiksxRHi9x3y71M7p5EjAWE6OxBkj/OaSqTgyvJUUIQncuDDx6qRsHHLqpHuR0PW3vbbCj5EYyAAq7dgMVPfHRytt2Kkv7i
#   5vAw0n1wZuFvFcDq/kGP5/X1tnm+2aiTLQy59MiE00wZ49okK2fNxsWfgnRfmvJA8D3E98tztTWdBtG9IPuw+tqgI+RRTLin1miNJ3EkRhQFxIRcl8+tgj9EN35VXqrV9G2MPIPvWfgv5I1Bh/pNBOGtYCeALEKM6nlc52uUP+XFDfRpRN7psa/ZeBWSAmJ99qrQGaANeJA3AUjpXhLZ1zsD+g+5
#   Cnd9pANrngAAAABJRU5ErkJggg==
#
# Utilizes the Jamendo /v3.0/ API now completely. That means all tracks will
# be available as Ogg Vorbis per default.
#
# Radio stations are a fixed internal list. There's not much point in querying
# the API for them. (They're really just automated playlists, and MP3-only.)
#
# Genre lists for tracks are built-in, but give a good enough overview. There's
# no "related" lookup possibility yet in our station lists. (Might be feasible
# as plugin though, via [load more] button etc...)
#
# Per default Ogg Vorbis is used as streaming format. Track URLs can be played
# back directly. Playlists and albums now require a roundtrip over the action
# module to extract the JAMJson format into pls/m3u/xspf. (The previous v2 API
# retrieval is going to become inaccessible soon.)


import re
import ahttp
from config import *
from channels import *
import json


# jamendo CC music sharing site
#
#
# The v3.0 streaming URLs don't seem to work. Therefore some /get2 URLs will
# be used.
#
#  [x]  http://api.jamendo.com/v3.0/playlists/file?client_id=&id=
#  [+]  http://storage-new.newjamendo.com/?trackid=792843&format=ogg2&u=0
#  [+]  http://api.jamendo.com/get2/stream/track/xspf/?playlist_id=171574&n=all&order=random
#  [+]  http://api.jamendo.com/get2/stream/track/xspf/?album_id=%s&streamencoding=ogg2&n=all
#
# Seem to resolve to OGG Vorbis each.
#
class jamendo (ChannelPlugin):

    # control flags
    has_search = True
    base = "http://www.jamendo.com/en/"
    audioformat = "audio/ogg"
    listformat = "srv"
    api_base = "http://api.jamendo.com/v3.0/"
    cid = "49daa4f5"
    categories = []
    titles = dict( title="Title", playing="Album/Artist/User", bitrate=False, listeners=False )


    # refresh category list
    def update_categories(self):

        self.categories = [
            "radios",
            "playlists",
                ["feeds"],  # should go below `albums`, but looks nicer here
            "albums",
                ["newest"],
            "tracks",
                [
                "pop",
                "synthpop",
                "trashpop",
                "disco",
                "eurodance",
                "electropop",

                "rock",
                "hardrock",
                "alternativerock",
                "acousticrock",
                "poprock",

                "dance",
                "dancehall",
                "trance",
                "psytrance",
                "trancecore",

                "hiphop",
                "rap",
                "rappers",
                "dubstep",
                "beat",
                "beats",
                "breakbeats",
                "dub",
                "club",
                "edm",
                "electronic",
                "techno",
                "electric",
                "synthesizer",
                "triphop",
                "house",
                "electrohouse",
                "darkelectro",
                "rnb",

                "metal",
                "heavymetal",
                "thrashmetal",
                "powermetal",
                "groovemetal",

                "jazz",
                "acidjazz",
                "smoothjazz",
                "classicjazz",

                "instrumental",
                "acoustic",

                "singersongwriter",
                "vocal",
                "vocals",
                "voice",


                "game",
                "gamemusic",
                "8bit",
                "computer",

                "classical", ###
                "organ",
                "orchestral",
                "choral",
                "ballad",
                "piano",
                "mozart",
                "violin",
                "cello",
                "fiddle",
                "ukelele",
                "trumpet",
                "saxophone",
                "harmonica",
                "accordion",

                "soul",
                "blues",
                "deltablues",
                "swing",
                "boogie",
                "funk",
                "electrofunk",
                "folk",
                "folkrock",

                "world", ###
                "african",
                "middleeastern",
                "arabic",
                "asian",
                "oriental",
                "latin",
                "french",
                "german",
                "irish",
                "celtic",
                "country",
                "reggae",

                "emotion",
                "romantic", ###
                "love",
                "slow",
                "quiet",
                "happy",
                "angry",
                "sad",
                "mysterious",
                "atmospheric",
                "mellow",
                "dark",
                "dream"
                "energic",
                "downtempo",
                "sexy",
                "melancholic",



                "progressive",
                "experimental",
                "evolutive",
                "alternative",
                "sampler",
                "minimalism",
                "avantgarde",
                "elegant",
                "vintage",
                "retro",
                "oldschool",
                "traditional",
                "adult",
                "communication",
                "advertising",
                "indie",
                "improvisation",
                "lofi",
                "newage",
                "grunge",
                "raw",

                "industrial",
                "bass",
                "drum",
                "epic",
                "soundtrack",
                "rhythmic",
                "keyboard",
                "drummachine",
                "acousticguitar",
                "bongo",

                "rumba",
                "pinkfloydian",
                "gothic",
                "space",
                "didgeridoo",
                "energetic",
                "worldfusion",
                "fusion",
                "noise",
                "jungle",

                "lounge",
                "relaxing",
                "easylistening",
                "ambient",
                "meditative",
                "psychedelic",
                "chillout",
                "soft",
                ]
        ]
        return self.categories


    # retrieve category or search
    def update_streams(self, cat, search=None):

        entries = []
        fmt = conf.jamendo_stream_format
        fmt_mime = self.stream_mime(fmt)
                
        # Static list of Radios
        if cat == "radios":
            for radio in ["BestOf", "Pop", "Rock", "Lounge", "Electro", "HipHop", "World", "Jazz", "Metal", "Soundtrack", "Relaxation", "Classical"]:
                entries.append({
                    "genre": radio,
                    "title": radio,
                    "url": "http://streaming.radionomy.com/Jam" + radio,  # optional +".m3u"
                    "playing": "various artists",
                    "format": "audio/mpeg",
                    "homepage": "http://www.jamendo.com/en/radios",
                    "img": "http://imgjam1.jamendo.com/new_jamendo_radios/%s30.jpg" % radio.lower(),
                })
        
        # Playlist
        elif cat == "playlists":
            for e in self.api(method="playlists", order="creationdate_desc"):
                entries.append({
                    "title": e["name"],
                    "playing": e["user_name"],
                    "homepage": e["shareurl"],
                    "extra": e["creationdate"],
                    "format": fmt_mime,
                    #"listformat": "xspf", # deprecated
                    #"url": "http://api.jamendo.com/get2/stream/track/xspf/?playlist_id=%s&n=all&order=random&from=app-%s" % (e["id"], self.cid),
                    #"listformat": "href", # raw ZIP redirect
                    #"url": "http://api.jamendo.com/v3.0/playlists/file?client_id={}&audioformat=mp32&id={}".format(self.cid, e["id"]),
                    #"listformat": "href", # raw ZIP direct
                    #"url": e["zip"],
                    "listformat": "jamj",
                    "url": "http://api.jamendo.com/v3.0/playlists/tracks?client_id={}&audioformat={}&id={}".format(self.cid, fmt, e["id"]),
                })

        # Albums
        elif cat in ["albums", "newest"]:
            if cat == "albums":
                order = "popularity_week"
            else:
                order = "releasedate_desc"
            for e in self.api(method = "albums/musicinfo", order = order, include = "musicinfo"):
                entries.append({
                    "genre": " ".join(e["musicinfo"]["tags"]),
                    "title": e["name"],
                    "playing": e["artist_name"],
                    "img": e["image"],
                    "homepage": e["shareurl"],
                    #"url": "http://api.jamendo.com/v3.0/playlists/file?client_id=%s&id=%s" % (self.cid, e["id"]),
                    #"url": "http://api.jamendo.com/get2/stream/track/xspf/?album_id=%s&streamencoding=ogg2&n=all&from=app-%s" % (e["id"], self.cid),
                    #"format": "audio/ogg",
                    #"listformat": "xspf",
                    "url": "http://api.jamendo.com/v3.0/tracks?client_id={}&audioformat={}&album_id={}".format(self.cid, fmt, e["id"]),
                    "listformat": "jamj",
                    "format": fmt_mime,
                })
		
        # Feeds (News)
        elif cat == "feeds":
            for e in self.api(method="feeds", order="date_start_desc", target="notlogged"):
              if e.get("joinid") and e.get("subtitle"):
                entries.append({
                    "genre": e["type"],
                    "title": e["title"]["en"],
                    "playing": e["subtitle"]["en"],
                    "extra": e["text"]["en"],
                    "homepage": e["link"],
                    "format": fmt_mime,
                    "listformat": "jamj",
                    "url": "http://api.jamendo.com/v3.0/tracks?client_id={}&audioformat={}&album_id={}".format(self.cid, fmt, e["joinid"]),
                })

        # Genre list, or Search
        else:
            if cat:
                data = self.api(method="tracks", order="popularity_week", include="musicinfo", fuzzytags=cat, audioformat=fmt)
            elif search:
                data = self.api(method="tracks", order="popularity_week", include="musicinfo", search=search, audioformat=fmt)
            else:
                data = []
            for e in data:
                entries.append({
                    "lang": e["musicinfo"]["lang"],
                    "genre": " ".join(e["musicinfo"]["tags"]["genres"]),
                    "extra": ", ".join(e["musicinfo"]["tags"]["vartags"]),
                    "title": e["name"],
                    "playing": e["album_name"] + " / " + e["artist_name"],
                    "img": e["album_image"],
                    "homepage": e["shareurl"],
                    "url": e["audio"],
                    #"url": "http://storage-new.newjamendo.com/?trackid=%s&format=ogg2&u=0&from=app-%s" % (e["id"], self.cid),
                    "format": fmt_mime,
                    "listformat": "srv",
                })
 
        # done    
        return entries

    
    # Collect data sets from Jamendo API
    def api(self, method, **params):
        r = []
        max = 200 * int(conf.jamendo_count)
        params = dict(
            list({
                "client_id": self.cid,
                "format": "json",
                "audioformat": "mp32",
                "imagesize": conf.jamendo_image_size,
                "offset": 0,
                "limit": 200,
            }.items()) + list(params.items())
        )
        while (params["offset"] < max) and (len(r) % 200 == 0):
            data = ahttp.get(self.api_base + method, params, encoding="utf-8")
            data = json.loads(data)
            if data:
                r += data["results"]
            else:
                return r
            params["offset"] += 200;
            self.parent.status(float(params["offset"])/float(max+17))
        return r
        

    # audio/*
    def stream_mime(self, name):
        map = {
            "ogg": "audio/ogg", "ogg2": "audio/ogg",
            "mp3": "audio/mpeg", "mp31": "audio/mpeg", "mp32": "audio/mpeg",
            "flac": "audio/flac"
        }
        return map.get(name) or map["mp3"]

