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
        categories = ["all", [],           ]
        current = ""
        default = "all"
        empty = None
        
        
        # prepare category names
        def __init__(self, parent=None):
            
            self.categories = ["all"]
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
            g = {}
            for row in self.streams["all"]:
                for t in row["genre"].split():
                    if g.has_key(t):
                        g[t] += 1
                    else:
                        g[t] = 0
            g = [ [v[1],v[0]] for v in g.items() ]
            g.sort()
            g.reverse()
            for row in g:
                pass
                __print__( dbg.DATA, '        "' + row[1] + '", #' + str(row[0]) )



        # downloads stream list from xiph.org for given category
        def update_streams(self, cat, search=""):

            # there is actually just a single category to download,
            # all else are virtual
            if (cat == "all"):
            
                #-- get data
                data = http.get(self.json_url)
                __print__(dbg.DATA, data)
                
                #-- extract
                l = []
                __print__( dbg.DATA, "processing dir.xiph.org/experimental/full JSON" )
                for e in json.loads(data):
                    bitrate = e["bitrate"]
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
                
            # filter out a single subtree
            else:
                rx = re.compile(self.filter.get(cat.lower(), cat.lower()))
                l = []
                for i,row in enumerate(self.streams["all"]):
                    if rx.search(row["genre"]):
                        l.append(row)
            
            # send back the list 
            return l




        genres = [
            "scanner", #442
            "rock", #305
            [
              "metal|heavy", #36
            ],
            "various", #286
            [
              "mixed", #96
            ],
            "pop", #221
            [
              "top40|top|40|top 40", #32
              "charts|hits", #20+4
              "80s", #68
              "90s", #20
              "disco", #17
              "remixes", #10
            ],
            "electronic|electro", #33
            [
              "dance", #161
              "house", #106
              "trance", #82
              "techno", #72
              "chillout", #16
              "lounge", #12
            ],
            "alternative", #68
            [
              "college", #32
              "student", #20
              "progressive", #20
            ],
            "classical|classic", #58+20
            "live", #57
            "jazz", #42
            [
              "blues", #19
            ],
            "talk|spoken|speak", #41
            [
              "news", #39
              "public", #12
              "info", #5
            ],
            "world|international", #25
            [
              "latin", #34
              "reggae", #12
              "indie", #12
              "folk", #9
              "schlager", #14
              "jungle", #13
              "country", #7
              "russian", #6
            ],
            "hip hop|hip|hop", #34
            [
               "oldschool", #10
               "rap",
            ],
            "ambient", #34
            "adult", #33
           ## "music", #32
            "oldies", #31
            [
              "60s", #2
              "70s", #17
            ],
            "religious", #4
            [
              "christian|bible", #14
            ],
            "rnb|r&b", #12
            [
              "soul", #11
              "funk", #24
              "urban", #11
            ],
            "other", #25
            [
              "deep", #14
              "soft", #12
              "minimal", #12
              "eclectic", #12
              "drum", #12
              "bass", #12
              "experimental", #11
              "hard", #10
              "funky", #10
              "downtempo", #10
              "slow", #9
              "break", #9
              "electronica", #8
              "dub", #8
              "retro", #7
              "punk", #7
              "psychedelic", #7
              "goa", #7
              "freeform", #7
              "c64", #7
              "breaks", #7
              "anime", #7
              "variety", #6
              "psytrance", #6
              "island", #6
              "downbeat", #6
              "underground", #5
              "newage", #5
              "gothic", #5
              "dnb", #5
              "club", #5
              "acid", #5
              "video", #4
              "trip", #4
              "pure", #4
              "industrial", #4
              "groove", #4
              "gospel", #4
              "gadanie", #4
              "french", #4
              "dark", #4
              "chill", #4
              "age", #4
              "wave", #3
              "vocal", #3
              "tech", #3
              "studio", #3
              "relax", #3
              "rave", #3
              "hardcore", #3
              "breakbeat", #3
              "avantgarde", #3
              "swing", #2
              "soundtrack", #2
              "salsa", #2
              "italian", #2
              "independant", #2
              "groovy", #2
              "european", #2
              "darkwave", #2
            ],
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
