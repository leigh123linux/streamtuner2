#
# api: streamtuner2
# title: Xiph.org
# description: ICEcast radio directory. Now utilizes a cached JSON API.
# type: channel
# category: radio
# version: 0.3
# priority: standard
#
#
# Xiph.org maintains the Ogg streaming standard and Vorbis audio compression
# format, amongst others. The ICEcast server is an alternative to SHOUTcast.
#
# It meanwhile provides a JSOL dump, which is faster to download and process.
# So we'll use that over the older yp.xml. (Sadly it also doesn't output
# homepage URLs, listeners, etc.)
#
#



# streamtuner2 modules
from config import conf
from mygtk import mygtk
import ahttp as http
from channels import *
from config import __print__, dbg
import json

# python modules
import re
#from xml.sax.saxutils import unescape as entity_decode, escape as xmlentities
#import xml.dom.minidom



          
# I wonder what that is for                                             ---------------------------------------
class xiph (ChannelPlugin):

        # desc
        api = "streamtuner2"
        module = "xiph"
        title = "Xiph.org"
        homepage = "http://dir.xiph.org/"
        #base_url = "http://api.dir.xiph.org/"
        json_url = "http://api.include-once.org/xiph/cache.php"
        listformat = "url/http"
        config = [
           {"name":"xiph_min_bitrate", "value":64, "type":"int", "description":"minimum bitrate, filter anything below", "category":"filter"}
        ]
        has_search = True

        # content
        categories = [ "pop", "top40" ]
        current = ""
        default = "pop"
        empty = None
        
        
        # prepare category names
        def __init__(self, parent=None):
            
            self.categories = []
            self.filter = {}
            for main in self.genres:
                if (type(main) == str):
                    id = main.split("|")
                    self.categories.append(id[0].title())
                    self.filter[id[0]] = main
                else:
                    l = []
                    for sub in main:
                        id = sub.split("|")
                        l.append(id[0].title())
                        self.filter[id[0]] = sub
                    self.categories.append(l)
            
            # GUI
            ChannelPlugin.__init__(self, parent)


        # just counts genre tokens, does not automatically create a category tree from it
        def update_categories(self):
            pass


        # downloads stream list from xiph.org for given category
        def update_streams(self, cat, search=None):

            # With the new JSON cache API on I-O, we can load categories individually:
            params = {}
            if cat:
                params["cat"] = cat.lower()
            if search:
                params["search"] = search
            
            #-- get data
            data = http.get(self.json_url, params=params)
            #__print__(dbg.DATA, data)
            
            #-- extract
            l = []
            __print__( dbg.PROC, "processing api.dir.xiph.org JSON (via api.include-once.org cache)" )
            data = json.loads(data)
            for e in data:
                #__print__(dbg.DATA, e)
                bitrate = int(e["bitrate"])
                if conf.xiph_min_bitrate and bitrate and bitrate >= int(conf.xiph_min_bitrate):
                  l.append({
                    "title": e["stream_name"],
                    "url": e["listen_url"],
                    "format": e["type"],
                    "bitrate": int(e["bitrate"]),
                    "genre": e["genre"],
                    "playing": e["current_song"],
                    "listeners": 0,
                    "max": 0,
                    "homepage": (e["homepage"] if ("homepage" in e) else ""),
                  })
                
            # send back the list 
            return l




        genres = [
              "pop",
              [
                  "top40",
                  "90s",
                  "80s",
                  "britpop",
                  "disco",
                  "urban",
                  "party",
                  "mashup",
                  "kpop",
                  "jpop",
                  "lounge",
                  "softpop",
                  "top",
                  "popular",
                  "schlager",
              ],
              "rock",
              [
                  "alternative",
                  "electro",
                  "country",
                  "mixed",
                  "metal",
                  "eclectic",
                  "folk",
                  "anime",
                  "hardcore",
                  "pure"
                  "jrock"
              ],
              "dance",
              [
                  "electronic",
                  "deephouse",
                  "dancefloor",
                  "elektro"
                  "eurodance"
                  "b",
                  "r",
              ],
              "hits",
              [
                  "russian"
                  "hit",
                  "star"
              ],
              "radio",
              [
                  "live",
                  "community",
                  "student",
                  "internet",
                  "webradio",
              ],
              "classic",
              [
                   "classical",
                   "ebu",
                   "vivaldi",
                   "piano",
                   "opera",
                   "classix",
                   "chopin",
                   "renaissance",
                   "classique",
              ],
              "talk",
              [
                  "news",
                  "politics",
                  "medicine",
                  "health"
                  "sport",
                  "education",
                  "entertainment",
                  "podcast",
              ],
              "various",
              [
                  "hits",
                  "ruhit",
                  "mega"
              ],
              "house",
              [
                  "lounge",
                  "trance",
                  "techno",
                  "handsup",
                  "gay",
                  "breaks",
                  "dj",
              "electronica",
              ],
              "trance",
              [
                  "clubbing",
                  "electronical"
              ],
              "jazz",
              [
                  "contemporary"
              ],
              "oldies",
              [
                  "golden",
                  "decades",
                  "info",
                  "70s",
                  "60s"
              ],
              "religious",
              [
                  "spiritual",
                  "inspirational",
                  "christian",
                  "catholic",
                  "teaching",
                  "christmas",
                  "gospel",
              ],
              "music",
              "unspecified",
              "misc",
              "adult",
              "indie",
              [
                  "reggae",
                  "blues",
                  "college",
                  "soundtrack"
              ],
              "mixed",
              [
                  "disco",
                  "mainstream",
                  "soulfull"
              ],
              "funk",
              "hiphop",
              [
                  "rap",
                  "dubstep",
                  "hip",
                  "hop"
              ],
              "top",
              [
                  "urban"
              ],
              "musica",
              "ambient",
              [
                  "downtempo",
                  "dub"
              ],
              "promodj",
              "world",    # REGIONAL
              [
                  "france",
                  "greek",
                  "german",
                  "westcoast",
                  "bollywood",
                  "indian",
                  "nederlands",
                  "europa",
                  "italia",
                  "brazilian",
                  "tropical",
                  "korea",
                  "seychelles",
                  "black",
                  "japanese",
                  "ethnic",
                  "country",
                  "americana",
                  "western",
                  "cuba",
                  "afrique",
                  "paris",
                  "celtic",
                  "ambiance",
                  "francais",
                  "liberte",
                  "anglais",
                  "arabic",
                  "hungary",
                  "folklore"
                  "latin",
                  "dutch"
                  "italy"
              ],
              "artist",   # ARTIST NAMES
              [
                  "mozart",
                  "beatles",
                  "michael",
                  "nirvana",
                  "elvis",
                  "britney",
                  "abba",
                  "madonna",
                  "depeche",
              ],
              "salsa",
              "love",
              "la",
              "soul",
              "techno",
              [
                  "club",
                  "progressive",
                  "deep"
              "electro",
              ],
              "best",
              "100%",
              "rnb",
              "retro",
              "new",
              "smooth",
              [
                  "cool"
              ],
              "easy",
              [
                  "lovesongs",
                  "relaxmusic"
              ],
              "chillout",
              "slow",
              [
                  "soft"
              ],
              "mix",
              [
                  "modern"
              ],
              "punk",
              [
                  "ska"
              ],
              "international",
              "bass",
              "zouk",
              "video",
              [
                  "game"
              ],
              "hardstyle",
              "scanner",
              "chill",
              [
                  "out",
                  "trip"
              ],
              "drum",
              "roots",
              "ac",
              [
                  "chr",
                  "dc"
              ],
              "public",
              "contemporary",
              [
                  "instrumental"
              ],
              "minimal",
              "hot",
              [
                  "based"
              ],
              "free",
              [
                  "format"
              ],
              "hard",
              [
                  "heavy",
                  "classicrock"
              ],
              "reggaeton",
              "southern",
              "musica",
              "old",
              "emisora",
              "img",
              "rockabilly",
              "charts",
              [
                  "best80",
                  "70er",
                  "80er",
                  "60er"
                  "chart",
              ],
              "other",
              [
                  "varios"
              ],
              "soulful",
              "listening",
              "vegyes",
              "creative",
              "variety",
              "commons",
              [
                  "ccmusik"
              ],
              "tech",
              [
                  "edm",
                  "prog"
              ],
              "minecraft",
              "animes",
              "goth",
              "technologie",
              "tout",
              "musical",
              [
                  "broadway"
              ],
              "romantica",
              "newage",
              "nostalgia",
              "oldschool",
              [
                  "00s"
              ],
              "wij",
              "relax",
              [
                  "age"
              ],
              "theatre",
              "gothic",
              "dnb",
              "disney",
              "funky",
              "young",
              "psychedelic",
              "habbo",
              "experimental",
              "exitos",
              "digital",
              "no",
              "industrial",
              "epic",
              "soundtracks",
              "cover",
              "chd",
              "games",
              "libre",
              "wave",
              "vegas",
              "comedy",
              "alternate",
              "instrumental",
              [
                  "swing"
              ],
              "ska",
              [
                  "punkrock",
                  "oi"
              ],
              "darkwave",
          ]

