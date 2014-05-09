
# api: streamtuner2
# title: jamendo browser
# description: Jamendo is a license-free music collection and artist hub
# depends: json
#
# Now utilizes the Jamendo /v3.0/ API.
#
# Radio station lists are fixed for now. Querying the API twice per station
# doesn't seem overly sensible.
#
# Albums and Playlists are limited to 200 entries. Adding a cursor is
# feasible however.
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
    api = "http://api.jamendo.com/v3.0/"
    cid = "49daa4f5"

    categories = [
        "radios",
        "playlists",
        "albums",
        "tracks",
            ["pop", "rock", "dance", "classical", "jazz", "instrumental"]
    ]
    titles = dict( title="Title", playing="Album/Artist/User", bitrate=False, listeners=False )
 
    config = [
        {"name":"jamendo_stream_format", "value":"ogg2", "type":"text", "description":"streaming format, 'ogg2' or 'mp31'"}
    ]    
    


    # refresh category list
    def update_categories(self):

        pass
        


    # retrieve category or search
    def update_streams(self, cat, search="", force=0):

        entries = []
        
        # return a static list for now
        if cat == "radios":
        
            entries = [
                {"title": "Best Of", "url": "http://streaming.radionomy.com/BestOf", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios", "favicon": "http://imgjam1.jamendo.com/new_jamendo_radios/bestof30.jpg"},
                {"title": "Pop", "url": "http://streaming.radionomy.com/JamPop", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios", "favicon": "http://imgjam1.jamendo.com/new_jamendo_radios/pop30.jpg"},
                {"title": "Rock", "url": "http://streaming.radionomy.com/JamRock", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios", "favicon": "http://imgjam1.jamendo.com/new_jamendo_radios/rock30.jpg"},
                {"title": "Lounge", "url": "http://streaming.radionomy.com/JamLounge", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios", "favicon": "http://imgjam1.jamendo.com/new_jamendo_radios/lounge30.jpg"},
                {"title": "Electro", "url": "http://streaming.radionomy.com/JamElectro", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios", "favicon": "http://imgjam1.jamendo.com/new_jamendo_radios/electro30.jpg"},
                {"title": "HipHop", "url": "http://streaming.radionomy.com/JamHipHop", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios", "favicon": "http://imgjam1.jamendo.com/new_jamendo_radios/hiphop30.jpg"},
                {"title": "World", "url": "http://streaming.radionomy.com/JamWorld", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios", "favicon": "http://imgjam1.jamendo.com/new_jamendo_radios/world30.jpg"},
                {"title": "Jazz", "url": "http://streaming.radionomy.com/JamJazz", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios", "favicon": "http://imgjam1.jamendo.com/new_jamendo_radios/jazz30.jpg"},
                {"title": "Metal", "url": "http://streaming.radionomy.com/JamMetal", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios", "favicon": "http://imgjam1.jamendo.com/new_jamendo_radios/metal30.jpg"},
                {"title": "Soundtrack", "url": "http://streaming.radionomy.com/JamSoundtrack", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios", "favicon": "http://imgjam1.jamendo.com/new_jamendo_radios/soundtrack30.jpg"},
                {"title": "Relaxation", "url": "http://streaming.radionomy.com/JamRelaxation", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios", "favicon": "http://imgjam1.jamendo.com/new_jamendo_radios/relaxation30.jpg"},
                {"title": "Classical", "url": "http://streaming.radionomy.com/JamClassical", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios", "favicon": "http://imgjam1.jamendo.com/new_jamendo_radios/classical30.jpg"},
            ]
        
        # playlist
        if cat == "playlists":
            data = http.get(self.api + cat, params = {
                "client_id": self.cid,
                "format": "json",
                "limit": "200"
            })
            for e in json.loads(data)["results"]:
                entries.append({
                    "title": e["name"],
                    "playing": e["user_name"],
                    "homepage": e["shareurl"],
                    #"url": "http://api.jamendo.com/v3.0/playlists/file?client_id=%s&id=%s" % (self.cid, e["id"]),
                    "url": "http://api.jamendo.com/get2/stream/track/xspf/?playlist_id=%s&n=all&order=random&from=app-%s" % (e["id"], self.cid),
                    "format": "application/xspf+xml",
                })

        # albums
        if cat == "albums":
            data = http.get(self.api + cat, params = {
                "client_id": self.cid,
                "format": "json",
                "limit": "200",
                "imagesize": "50"
            })
            for e in json.loads(data)["results"]:
                entries.append({
                    "title": e["name"],
                    "playing": e["artist_name"],
                    "favicon": e["image"],
                    "homepage": e["shareurl"],
                    #"url": "http://api.jamendo.com/v3.0/playlists/file?client_id=%s&id=%s" % (self.cid, e["id"]),
                    "url": "http://api.jamendo.com/get2/stream/track/xspf/?album_id=%s&streamencoding=ogg2&n=all&from=app-%s" % (e["id"], self.cid),
                    "format": "application/xspf+xml",
                })
		
        # genre list
        else:
            data = http.get(self.api + "tracks", params={
                "client_id": self.cid,
                ("fuzzytags" if cat else "search"): (search if search else cat),
                "format": "json",
                "audioformat":"ogg",
                "limit": "200",
                "offset": 200,
                "imagesize": "50",
                "order": "popularity_week",
                "include": "musicinfo",
            })
            for e in json.loads(data)["results"]:
                entries.append({
                    "lang": e["musicinfo"]["lang"],
                    "genre": " ".join(e["musicinfo"]["tags"]["genres"]),
                    "description": ", ".join(e["musicinfo"]["tags"]["vartags"]),
                    "title": e["name"],
                    "playing": e["album_name"] + " / " + e["artist_name"],
                    "favicon": e["album_image"],
                    "homepage": e["shareurl"],
                    #"url": e["audio"],
                    "url": "http://storage-new.newjamendo.com/?trackid=%s&format=ogg2&u=0&from=app-%s" % (e["id"], self.cid),
                    "format": "audio/ogg",
                })
 
        # done    
        return entries
        
        
    # smaller album link
    def cover(self, url):
        return url.replace(".100",".50").replace(".130",".50")
     
    # track id to download url   
    def track_url(self, track_id, fmt="ogg2", track="track", urltype="redirect"):
        # track = "album"
        # fmt = "mp31"
        # urltype = "m3u"
	return "http://api.jamendo.com/get2/stream/"+track+"/"+urltype+"/?id="+track_id+"&streamencoding="+fmt

    # audio/*
    def stream_mime(self):
        if conf.jamendo_stream_format.find("og") >= 0:
            return "audio/ogg"
        else:
            return "audio/mpeg"


