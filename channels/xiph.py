#
# api: streamtuner2
# title: Xiph.org
# description: Xiph/ICEcast radio directory
# version: 0.1
#
#
# Xiph.org maintains the Ogg streaming standard and Vorbis audio compression
# format, amongst others. The ICEcast server is an alternative to SHOUTcast.
# But it turns out, that Xiph lists only MP3 streams, no OGG. And the directory
# is less encompassing than Shoutcast.
#
#
#
#



# streamtuner2 modules
from config import conf
from mygtk import mygtk
import ahttp as http
from channels import *
from config import __print__, dbg

# python modules
import re
from xml.sax.saxutils import unescape as entity_decode, escape as xmlentities
import xml.dom.minidom



          
# I wonder what that is for                                             ---------------------------------------
class xiph (ChannelPlugin):

        # desc
        api = "streamtuner2"
        module = "xiph"
        title = "Xiph.org"
        version = 0.1
        homepage = "http://dir.xiph.org/"
        base_url = "http://dir.xiph.org/"
        yp = "yp.xml"
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


        # xml dom node shortcut to text content
        def x(self, entry, name):
            e = entry.getElementsByTagName(name)
            if (e):
                if (e[0].childNodes):
                    return e[0].childNodes[0].data
                    
        # convert bitrate string to integer
        # (also convert "Quality \d+" to pseudo bitrate)
        def bitrate(self, s):
            uu = re.findall("(\d+)", s)
            if uu:
                br = uu[0]
                if br > 10:
                    return int(br)
                else:
                    return int(br * 25.6)
            else:
                return 0

        # downloads stream list from shoutcast for given category
        def update_streams(self, cat, search=""):

            # there is actually just a single category to download,
            # all else are virtual
            if (cat == "all"):
            
                #-- get data
                yp = http.get(self.base_url + self.yp, 1<<22, feedback=self.parent.status)
                
                #-- extract
                l = []
                for entry in xml.dom.minidom.parseString(yp).getElementsByTagName("entry"):
                    bitrate = self.bitrate(self.x(entry, "bitrate"))
                    if conf.xiph_min_bitrate and bitrate and bitrate >= int(conf.xiph_min_bitrate):
                      l.append({
                        "title": str(self.x(entry, "server_name")),
                        "url": str(self.x(entry, "listen_url")),
                        "format": self.mime_fmt(str(self.x(entry, "server_type"))[6:]),
                        "bitrate": bitrate,
                        "channels": str(self.x(entry, "channels")),
                        "samplerate": str(self.x(entry, "samplerate")),
                        "genre": str(self.x(entry, "genre")),
                        "playing": str(self.x(entry, "current_song")),
                        "listeners": 0,
                        "max": 0,              # this information is in the html view, but not in the yp.xml (seems pretty static, we might as well make it a built-in list)
                        "homepage": "",
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

