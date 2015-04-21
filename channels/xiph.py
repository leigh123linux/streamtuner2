# encoding: UTF-8
# api: streamtuner2
# title: Xiph.org
# description: ICEcast radio directory. Now utilizes a cached JSON API.
# type: channel
# url: http://dir.xiph.org/
# version: 0.3
# category: radio
# config: 
#    { name: xiph_min_bitrate,  value: 64,  type: int,  description: "minimum bitrate, filter anything below",  category: filter }
# priority: standard
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAg5JREFUOI2lk1tIE2AUx3+7CG1tlmlG1rSEHrKgEUF7yO40taQiRj10I4qKkOaT4hIUItuTkC8hpJAQtJCICrFpzEKw
#   h61eQorGNBOTzbEt16ZrnR5Wq3mZD/3heziX//983znngyyov+eSbHEA5WKBhs4BKVy9gsqajqwiCwo0dA5IQX5u2s4moliMPPV1nCeDzxgNBFDHE2wsKMPzsGVefobjcnO7RMfeMuL341ZBrNEGRmPqqjdvsbbf
#   w7irO4Oj+rdywNNNucmERsLUVndR8uYRU13PCew6hpgP8W02xMpIsik++qk5oweW6y3yob8WnXacZDKJWh1Cp4OtRUHsh19TUlUGViv09RGqKAenU5QnLKm+rK88LjgcUnxmr/h8iNO5XYJBRAQZ/qiVeptGWjty
#   5cClDWLwugQRIRiU5UdPCoD6S89jhV6pks9WG6fuwtBtF5v72vC1v+B86SsM+jD56hjnyiM0lRrAbofeXjQJLdE/78jbXSU5166I6f5VeeDdKdq6GtlSd0QkVU+8XsQhlt9W6izbZ5aMKWgtp2WT/yUHd0xSYU7i
#   dsPQ+1WMKIsJD08wEV2HGLeRyNMjawqRxhuKBfdgz1m7fI/4mVX+ZGxmgniOoJv+QZHGAMC7p60ZnHkC8HfzZmLTBCd9af9ccnqMc9HTdmFe4kLkJbH/4h0xVtcu+SP/C78AL6btab6woPcAAAAASUVORK5CYII=
#
# Xiph.org maintains the Ogg streaming standard and Vorbis
# audio compression format, amongst others.  The ICEcast
# server is an alternative to SHOUTcast.
#
# It also provides a directory listing of known internet
# radio stations, only a handful of them using Ogg though.
#
# The category list is hardwired in this plugin.
#


from config import *
from uikit import uikit
import ahttp as http
from channels import *
#from xml.sax.saxutils import unescape as entity_decode, escape as xmlentities
#import xml.dom.minidom
import json
import re


          
# Xiph via I-O
#
#
# Xiph meanwhile provides a JSOL dump, which is faster to download and process.
# So we'll use that over the older yp.xml. (Sadly it also doesn't output
# homepage URLs, listeners, etc.)
#
# Xiphs JSON is a horrible mysqldump concatenation, not parseable. Thus it's
# refurbished on //api.include-once.org/xiph/cache.php for consumption. Which
# also provides compressed HTTP transfers and category slicing.
#
# Xiph won't be updating the directory for another while. The original feature
# request is now further delayed as summer of code project:
# · https://trac.xiph.org/ticket/1958
# · https://wiki.xiph.org/Summer_of_Code_2015#Stream_directory_API
#
class xiph (ChannelPlugin):

  # attributes
  listformat = "srv"
  has_search = True
  json_url = "http://api.include-once.org/xiph/cache.php"
  #xml_url = "http://dir.xiph.org/yp.xml"

  # content
  categories = [ "pop", "top40" ]
  
  
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
      #log.DATA(data)
      
      #-- extract
      l = []
      log.PROC( "processing api.dir.xiph.org JSON (via api.include-once.org cache)" )
      data = json.loads(data)
      for e in data:
          #log.DATA(e)
          bitrate = int(e["bitrate"])
          if conf.xiph_min_bitrate and bitrate and bitrate >= int(conf.xiph_min_bitrate):
              if not len(l) or l[-1]["title"] != e["stream_name"]:
                  l.append({
                    "title": e["stream_name"],
                    "url": e["listen_url"],
                    "format": e["type"],
                    "bitrate": bitrate,
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

