
# api: streamtuner2
# title: Jamendo
# description: A license-free music collection and artist hub.
# type: channel
# version: 2.2
# category: radio
# depends: json
# priority: default
#
# Now utilizes the Jamendo /v3.0/ API.
#
# Radio station lists are fixed for now. Querying the API twice per station
# doesn't seem overly sensible.
#
# Tracks are queried by genre, where currently there's just a small built-in
# tag list in ST2.
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



import re
import ahttp as http
from config import conf, __print__, dbg
from channels import *
import json






# jamendo CC music sharing site
class jamendo (ChannelPlugin):

    # description
    title = "Jamendo"
    module = "jamendo"
    homepage = "http://www.jamendo.com/"
    version = 0.3
    has_search = True

    base = "http://www.jamendo.com/en/"
    listformat = "url/http"
    api_base = "http://api.jamendo.com/v3.0/"
    cid = "49daa4f5"

    categories = ["radios"]

    titles = dict( title="Title", playing="Album/Artist/User", bitrate=False, listeners=False )
 
    config = [
        {"name":"jamendo_stream_format",
         "value":"ogg",
         "type": "text",
         "description":"Streaming format. Use 'ogg' for Vorbis, 'mp32' for MP3 with 192kbps/VBR, or 'mp31' for 96kbps MP3, and even 'flac' for lossless audio."
        },
        {"name": "jamendo_image_size",
         "value": "50",
         "type": "select",
         "select": "25=25px|35=35px|50=50px|55=55px|60=60px|65=65px|70=70px|75=75px|85=85px|100=100px|130=130px|150=150px|200=200px|300=300px",
         "description": "Preview images size (height and width) for albums or tracks."
        },
        {"name": "jamendo_count",
         "value": "1",
         "type":"text",
         "description": "How many result sets (200 entries each) to retrieve."
        }
    ]    
    


    # refresh category list
    def update_categories(self):

        self.categories = [
            "radios",
            "playlists",
            "albums",
                ["newest"],
            "tracks",
                ["pop", "rock", "dance", "classical", "jazz", "instrumental"]
        ]
        return self.categories


    # retrieve category or search
    def update_streams(self, cat, search="", force=0):

        entries = []
        fmt = self.stream_mime(conf.jamendo_stream_format)
        
        # Static list of Radios
        if cat == "radios":
            for radio in ["BestOf", "Pop", "Rock", "Lounge", "Electro", "HipHop", "World", "Jazz", "Metal", "Soundtrack", "Relaxation", "Classical"]:
                entries.append({
                    "genre": radio,
                    "title": radio,
                    "url": "http://streaming.radionomy.com/Jam" + radio,
                    "playing": "various artists",
                    "format": "audio/mpeg",
                    "homepage": "http://www.jamendo.com/en/radios",
                    "img": "http://imgjam1.jamendo.com/new_jamendo_radios/%s30.jpg" % radio.lower(),
                })
        
        # Playlist
        elif cat == "playlists":
            for e in self.api(method = cat, order = "creationdate_desc"):
                entries.append({
                    "title": e["name"],
                    "playing": e["user_name"],
                    "homepage": e["shareurl"],
                    #"url": "http://api.jamendo.com/v3.0/playlists/file?client_id=%s&id=%s" % (self.cid, e["id"]),
                    "url": "http://api.jamendo.com/get2/stream/track/xspf/?playlist_id=%s&n=all&order=random&from=app-%s" % (e["id"], self.cid),
                    "format": "application/xspf+xml",
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
                    "url": "http://api.jamendo.com/get2/stream/track/xspf/?album_id=%s&streamencoding=ogg2&n=all&from=app-%s" % (e["id"], self.cid),
                    "format": "application/xspf+xml",
                })
		
        # Genre list, or Search
        else:
            if cat:
                data = self.api(method = "tracks", order = "popularity_week", include = "musicinfo", fuzzytags = cat, audioformat = conf.jamendo_stream_format)
            elif search:
                data = self.api(method = "tracks", order = "popularity_week", include = "musicinfo", search = search, audioformat = conf.jamendo_stream_format)
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
                    #"url": e["audio"],
                    "url": "http://storage-new.newjamendo.com/?trackid=%s&format=ogg2&u=0&from=app-%s" % (e["id"], self.cid),
                    "format": fmt,
                })
 
        # done    
        return entries

    
    # Collect data from Jamenda API
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
            data = json.loads(http.get(self.api_base + method, params))
            if data and "results" in data:
                r += data["results"]
            else:
                return r
            params["offset"] += 200;
            self.parent.status(float(params["offset"])/float(max+17))
            __print__(dbg.PROC, params["offset"], max, len(r))
        return r
        

    # audio/*
    def stream_mime(self, name):
        map = {
            "ogg": "audio/ogg", "ogg2": "audio/ogg",
            "mp3": "audio/mpeg", "mp31": "audio/mpeg", "mp32": "audio/mpeg",
            "flac": "audio/flac"
        }
        if name in map:
            return map[name]
        else:
            return map["mp3"]

