#
# api: streamtuner2
# title: Xiph.org
# description: Xiph/ICEcast radio directory
# version: 0.2
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
        version = 0.2
        homepage = "http://dir.xiph.org/"
        #base_url = "http://api.dir.xiph.org/"
        json_url = "http://api.include-once.org/xiph/cache.php"
        listformat = "url/http"
        config = [
           {"name":"xiph_min_bitrate", "value":64, "type":"int", "description":"minimum bitrate, filter anything below", "category":"filter"}
        ]

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
        def update_streams(self, cat, search=""):

            # With the new JSON cache API on I-O, we can load categories individually:
            params = {}
            if cat:
                params["cat"] = cat.lower()
            if search:
                params["search"] = search
            
            #-- get data
            data = http.get(self.json_url, params=params)
            __print__(dbg.DATA, data)
            
            #-- extract
            l = []
            __print__( dbg.PROC, "processing api.dir.xiph.org JSON (via api.include-once.org cache)" )
            data = json.loads(data)
            for e in data.values():
                __print__(dbg.DATA, e)
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
                  "top100",
                  "schlager",
                  "top",
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
                  "internet"
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
              "the",
              [
                  "dome"
              ],
              "techno",
              [
                  "club",
                  "progressive",
                  "deep"
              ],
              "rap",
              [
                  "eurodance"
              ],
              "and",
              [
                  "italy"
              ],
              "webradio",
              "best",
              "electro",
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
              "electronica",
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
              ],
              "other",
              [
                  "varios"
              ],
              "soulful",
              "listening",
              "vegyes",
              "trance",
              [
                  "clubbing",
                  "electronical"
              ],
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
              "chart",
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
              "popular",
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
              "podcast",
              "darkwave",
          ]

"""
[

{"tag_name":"various","tag_usage":785},
{"tag_name":"rock","tag_usage":691},
{"tag_name":"radio","tag_usage":589},
{"tag_name":"pop","tag_usage":578},
{"tag_name":"dance","tag_usage":370},
{"tag_name":"anime","tag_usage":339},
{"tag_name":"jpop","tag_usage":301},
{"tag_name":"jrock","tag_usage":299},
{"tag_name":"jhiphop","tag_usage":291},
{"tag_name":"jrap","tag_usage":291},
{"tag_name":"hits","tag_usage":246},
{"tag_name":"alternative","tag_usage":198},
{"tag_name":"house","tag_usage":197},
{"tag_name":"christian","tag_usage":190},
{"tag_name":"talk","tag_usage":186},
{"tag_name":"music","tag_usage":178},
{"tag_name":"misc","tag_usage":154},
{"tag_name":"jazz","tag_usage":127},
{"tag_name":"electro","tag_usage":119},
{"tag_name":"techno","tag_usage":113},
{"tag_name":"top40","tag_usage":110},
{"tag_name":"trance","tag_usage":110},
{"tag_name":"electronic","tag_usage":110},
{"tag_name":"oldies","tag_usage":104},
{"tag_name":"news","tag_usage":102},
{"tag_name":"80s","tag_usage":101},
{"tag_name":"la","tag_usage":99},
{"tag_name":"musica","tag_usage":92},
{"tag_name":"lounge","tag_usage":87},
{"tag_name":"metal","tag_usage":84},
{"tag_name":"hip","tag_usage":80},
{"tag_name":"country","tag_usage":80},
{"tag_name":"mixed","tag_usage":78},
{"tag_name":"rap","tag_usage":78},
{"tag_name":"classic","tag_usage":77},
{"tag_name":"indie","tag_usage":75},
{"tag_name":"hop","tag_usage":73},
{"tag_name":"promodj","tag_usage":71},
{"tag_name":"eclectic","tag_usage":65},
{"tag_name":"gospel","tag_usage":62},
{"tag_name":"ambient","tag_usage":60},
{"tag_name":"adult","tag_usage":58},
{"tag_name":"top","tag_usage":58},
{"tag_name":"disco","tag_usage":54},
{"tag_name":"live","tag_usage":54},
{"tag_name":"reggae","tag_usage":54},
{"tag_name":"musique","tag_usage":53},
{"tag_name":"classical","tag_usage":53},
{"tag_name":"college","tag_usage":53},
{"tag_name":"blues","tag_usage":51},
{"tag_name":"the","tag_usage":50},
{"tag_name":"world","tag_usage":50},
{"tag_name":"salsa","tag_usage":46},
{"tag_name":"contemporary","tag_usage":46},
{"tag_name":"folk","tag_usage":45},
{"tag_name":"and","tag_usage":45},
{"tag_name":"punk","tag_usage":44},
{"tag_name":"40","tag_usage":44},
{"tag_name":"soul","tag_usage":44},
{"tag_name":"hardcore","tag_usage":44},
{"tag_name":"funk","tag_usage":43},
{"tag_name":"urban","tag_usage":42},
{"tag_name":"club","tag_usage":41},
{"tag_name":"chillout","tag_usage":39},
{"tag_name":"90s","tag_usage":39},
{"tag_name":"unspecified","tag_usage":38},
{"tag_name":"dubstep","tag_usage":37},
{"tag_name":"hit","tag_usage":37},
{"tag_name":"webradio","tag_usage":36},
{"tag_name":"new","tag_usage":36},
{"tag_name":"latin","tag_usage":35},
{"tag_name":"game","tag_usage":35},
{"tag_name":"deep","tag_usage":34},
{"tag_name":"70s","tag_usage":33},
{"tag_name":"b","tag_usage":33},
{"tag_name":"international","tag_usage":33},
{"tag_name":"community","tag_usage":32},
{"tag_name":"progressive","tag_usage":32},
{"tag_name":"fun","tag_usage":31},
{"tag_name":"video","tag_usage":31},
{"tag_name":"hiphop","tag_usage":30},
{"tag_name":"musica","tag_usage":30},
{"tag_name":"electronica","tag_usage":30},
{"tag_name":"r","tag_usage":29},
{"tag_name":"bass","tag_usage":28},
{"tag_name":"jungle","tag_usage":27},
{"tag_name":"sports","tag_usage":27},
{"tag_name":"smooth","tag_usage":26},
{"tag_name":"scanner","tag_usage":26},
{"tag_name":"mix","tag_usage":26},
{"tag_name":"best","tag_usage":26},
{"tag_name":"60s","tag_usage":25},
{"tag_name":"soulful","tag_usage":25},
{"tag_name":"drum","tag_usage":25},
{"tag_name":"religious","tag_usage":25},
{"tag_name":"ska","tag_usage":25},
{"tag_name":"garage","tag_usage":24},
{"tag_name":"downtempo","tag_usage":24},
{"tag_name":"retro","tag_usage":23},
{"tag_name":"minimal","tag_usage":23},
]
"""
