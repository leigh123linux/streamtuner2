# encoding: UTF-8
# api: streamtuner2
# title: Xiph.org
# description: ICEcast radios. Scans per JSON API, slow XML, or raw directory.
# type: channel
# url: http://dir.xiph.org/
# version: 0.5
# category: radio
# config: 
#    { name: xiph_source, value: web, type: select, select: "cache=JSON cache srv|xml=Clunky XML blob|web=Forbidden fruits", description: "Source for station list extraction." }
# priority: standard
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAg5JREFUOI2lk1tIE2AUx3+7CG1tlmlG1rSEHrKgEUF7yO40taQiRj10I4qKkOaT4hIUItuTkC8hpJAQtJCICrFpzEKw
#   h61eQorGNBOTzbEt16ZrnR5Wq3mZD/3heziX//983znngyyov+eSbHEA5WKBhs4BKVy9gsqajqwiCwo0dA5IQX5u2s4moliMPPV1nCeDzxgNBFDHE2wsKMPzsGVefobjcnO7RMfeMuL341ZBrNEGRmPqqjdvsbbf
#   w7irO4Oj+rdywNNNucmERsLUVndR8uYRU13PCew6hpgP8W02xMpIsik++qk5oweW6y3yob8WnXacZDKJWh1Cp4OtRUHsh19TUlUGViv09RGqKAenU5QnLKm+rK88LjgcUnxmr/h8iNO5XYJBRAQZ/qiVeptGWjty
#   5cClDWLwugQRIRiU5UdPCoD6S89jhV6pks9WG6fuwtBtF5v72vC1v+B86SsM+jD56hjnyiM0lRrAbofeXjQJLdE/78jbXSU5166I6f5VeeDdKdq6GtlSd0QkVU+8XsQhlt9W6izbZ5aMKWgtp2WT/yUHd0xSYU7i
#   dsPQ+1WMKIsJD08wEV2HGLeRyNMjawqRxhuKBfdgz1m7fI/4mVX+ZGxmgniOoJv+QZHGAMC7p60ZnHkC8HfzZmLTBCd9af9ccnqMc9HTdmFe4kLkJbH/4h0xVtcu+SP/C78AL6btab6woPcAAAAASUVORK5CYII=
#
# Xiph.org maintains the Ogg streaming standard and Vorbis,
# Opus, FLAC audio, and Theora video compression formats.
# The ICEcast server is an open alternative to SHOUTcast.
#
# It also provides a directory listing of known internet
# radio stations; only a handful of them using Ogg though.
# The category list is hardwired in this plugin. And there
# are three station fetching modes now:
#
#  → "JSON cache" retrieves a refurbished JSON station list,
#    both sliceable genres and searchable.
#
#  → "Clunky XML" fetches the olden YP.XML, which is really
#    slow, then slices out genres. No search. With the secret
#    "buffy" mode keeps all streams buffered.
#
#  → "Forbidden Fruits" extracts from dir.xiph.org HTML pages,
#    with homepages and listener/max infos available. Also
#    enables live server searching.
#
# The previous bitrate filter is now a separate plugin, but
# available for all channels.


from config import *
from uikit import uikit
import ahttp
from channels import *
import xml.dom.minidom
import json
import re


          
# Xiph directory service
class xiph (ChannelPlugin):

  # attributes
  listformat = "srv"
  has_search = True
  json_url = "http://api.include-once.org/xiph/cache.php"
  xml_url = "http://dir.xiph.org/yp.xml"
  web_url = "http://dir.xiph.org/"

  # content
  categories = []


  # Categories are basically just the static .genre list
  def update_categories(self):
      self.categories = [
         g.title() if isinstance(g, str) else [s.title() for s in g]
         for g in self.genres
      ]  # entries contain no "|" search patterns anymore


  # Switch to JSON, XML or HTML extractor
  def update_streams(self, cat=None, search=None):
      if cat:
          cat = cat.lower()

      # retrieval module
      if conf.xiph_source in ("cache", "json"):
          log.PROC("Xiph mode: processing api.dir.xiph.org JSON (via api.include-once.org cache)")
          r = self.from_json_cache(cat, search)
      elif conf.xiph_source in ("xml", "buffy"):
          log.PROC("Xiph mode: xml.dom.minidom to traverse yp.xml")
          r = self.from_yp_xml(cat, search)
      else:
          log.PROC("Xiph mode: extract from dir.xiph.org HTML listings")
          r = self.from_raw_html(cat, search)

      return r
      



  # Retrieve partial stream list from api.include-once.org cache / JSON API wrapper
  #
  # The server interface is specifically designed for streamtuner2. It refurbishes
  # Xiphs JSOL dump (which is impossible to fix in Python, but easier per PHP).
  # It doesn't contain homepage links, etc either.
  # While Xiph.org promised fixing their very own JSON API, it's delayed through
  # summer of code again. <https://trac.xiph.org/ticket/1958>
  #
  def from_json_cache(self, cat, search=None):

      # With the new JSON cache API on I-O, we can load categories individually:
      params = dict(search=search) if search else dict(cat=cat)
      data = ahttp.get(self.json_url, params=params)
      #log.DATA(data)
      
      #-- extract
      l = []
      data = json.loads(data)
      for e in data:
          if not len(l) or l[-1]["title"] != e["stream_name"]:
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



  # Extract complete YP.XML, but just filter for genre/cat
  def from_yp_xml(self, cat, search=None, buffy=[]):

      # Theoretically we could really buffer the extracted station lists.
      # But it's a huge waste of memory to keep it around for unused
      # categories.  Extracting all streams{} at once would be worse. Yet
      # enabling this buffer method prevents partial reloading..
      if conf.xiph_source != "buffy":
          buffy = []

      # Get XML blob
      if not buffy:
          yp = ahttp.get(self.xml_url, encoding="utf-8", statusmsg="Brace yourselves, still downloading the yp.xml blob.")
      else:
          yp = "<none/>"
      self.status("Yes, XML parsing isn't much faster either.", timeout=20)
      for entry in xml.dom.minidom.parseString(yp).getElementsByTagName("entry"):
          buffy.append({
              "title": x(entry, "server_name"),
              "url": x(entry, "listen_url"),
              "format": mime_fmt(x(entry, "server_type")[6:]),
              "bitrate": bitrate(x(entry, "bitrate")),
              "channels": x(entry, "channels"),
              "samplerate": x(entry, "samplerate"),
              "genre": x(entry, "genre"),
              "playing": x(entry, "current_song"),
              "listeners": 0,
              "max": 0,
              "homepage": "",
          })
      self.status("This. Is. Happening. Now.")

      # Filter out a single subtree
      l = []
      if cat:
          rx = re.compile(cat.lower())
          l = [row for row in buffy if rx.search(row["genre"])]

      # Search is actually no problem. Just don't want to. Nobody is using the YP.XML mode anyway..
      elif search:
          pass
        
      # Result category
      return l



  # Fetch directly from website. Which Xiph does not approve of; but
  # hey, it's a fallback option here. And the only way to actually
  # uncover station homepages.
  #@use_rx
  def from_raw_html(self, cat, search=None, use_rx=False):

      # Build request URL
      by_format = {t.lower(): t for t in self.categories[-1]}
      if search:
          url = "http://dir.xiph.org/search?search={}".format(search)
          cat = "search"
      elif by_format.get(cat):
          url = "http://dir.xiph.org/by_format/{}".format(by_format[cat])
      elif cat:
          url = "http://dir.xiph.org/by_genre/{}".format(cat.title())

      # Collect all result pages
      html = ahttp.get(url)
      for i in range(1,4):
          if html.find('page={}">{}</a></li>'.format(i, i+1)) < 0:
              break
          self.status(i/5.1)
          html += ahttp.get(url, {"search": cat.title(), "page": i})
      try: html = html.encode("raw_unicode_escape").decode("utf-8")
      except: pass

      # Find streams
      r = []
      #for row in re.findall("""<tr class="row[01]">(.+?)</tr>""", html, re.X|re.S):
      #    pass
      ls = re.findall("""
          <tr\s+class="row[01]">
          .*? class="name">
               <a\s+href="(.*?)"[^>]*>
                (.*?)</a>
          .*? "listeners">\[(\d+)
          .*? "stream-description">(.*?)<
          .*? Tags: (.*?) </div>
          .*? href="(/listen/\d+/listen.xspf)"
          .*? class="format"\s+title="([^"]+)"
          .*? /by_format/([^"]+)
      """, html, re.X|re.S)
            
      # Assemble
      for homepage, title, listeners, playing, tags, url, bits, fmt in ls:
          r.append(dict(
              genre = unhtml(tags),
              title = unhtml(title),
              homepage = ahttp.fix_url(homepage),
              playing = unhtml(playing),
              url = "http://dir.xiph.org{}".format(url),
              listformat = "xspf",
              listeners = int(listeners),
              bitrate = bitrate(bits),
              format = mime_fmt(guess_format(fmt)),
          ))
      return r



  # Static list of categories
  genres = [
        "pop",
        [
            "top40", "90s", "80s", "britpop", "disco", "urban", "party",
            "mashup", "kpop", "jpop", "lounge", "softpop", "top", "popular",
            "schlager",
        ],
        "rock",
        [
            "alternative", "electro", "country", "mixed", "metal",
            "eclectic", "folk", "anime", "hardcore", "pure", "jrock"
        ],
        "dance",
        [
            "electronic", "deephouse", "dancefloor", "elektro", "eurodance",
            "rnb",
        ],
        "hits",
        [
            "russian", "hit", "star"
        ],
        "radio",
        [
            "live", "community", "student", "internet", "webradio",
        ],
        "classic",
        [
             "classical", "ebu", "vivaldi", "piano", "opera", "classix",
             "chopin", "renaissance", "classique",
        ],
        "talk",
        [
            "news", "politics", "medicine", "health", "sport", "education",
            "entertainment", "podcast",
        ],
        "various",
        [
            "hits", "ruhit", "mega"
        ],
        "house",
        [
            "lounge", "trance", "techno", "handsup", "gay", "breaks", "dj",
            "electronica",
        ],
        "trance",
        [
            "clubbing", "electronical"
        ],
        "jazz",
        [
            "contemporary"
        ],
        "oldies",
        [
            "golden", "decades", "info", "70s", "60s"
        ],
        "religious",
        [
            "spiritual", "inspirational", "christian", "catholic",
            "teaching", "christmas", "gospel",
        ],
        "music",
        "unspecified",
        "misc",
        "adult",
        "indie",
        [
            "reggae", "blues", "college", "soundtrack"
        ],
        "mixed",
        [
            "disco", "mainstream", "soulfull"
        ],
        "funk",
        "hiphop",
        [
            "rap", "dubstep", "hip", "hop"
        ],
        "top",
        [
            "urban"
        ],
        "musica",
        "ambient",
        [
            "downtempo", "dub"
        ],
        "promodj",
        "world",    # REGIONAL
        [
            "france", "greek", "german", "westcoast", "bollywood", "indian",
            "nederlands", "europa", "italia", "brazilian", "tropical",
            "korea", "seychelles", "black", "japanese", "ethnic", "country",
            "americana", "western", "cuba", "afrique", "paris", "celtic",
            "ambiance", "francais", "liberte", "anglais", "arabic",
            "hungary", "folklore", "latin", "dutch", "italy"
        ],
        "artist",   # ARTIST NAMES
        [
            "mozart", "beatles", "michael", "nirvana", "elvis", "britney",
            "abba", "madonna", "depeche",
        ],
        "salsa",
        "love",
        "la",
        "soul",
        "techno",
        [
            "club", "progressive", "deep", "electro",
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
            "lovesongs", "relaxmusic"
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
            "best80", "70er", "80er", "60er", "chart",
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
        "/FORMAT",
        ["Ogg_Vorbis", "Ogg_Theora", "Opus", "NSV", "WebM"],
    ]



# Helper functions for XML extraction mode

# Shortcut to get text content from XML subnode by name
def x(node, name):
    e = node.getElementsByTagName(name)
    if (e):
        if (e[0].childNodes):
            return str(e[0].childNodes[0].data)
    return ""

# Convert bitrate string or "Quality \d+" to integer
def bitrate(str):
    uu = re.findall("(\d+)", str)
    if uu:
        br = int(uu[0])
        if br > 10:
            return int(br)
        else:
            return int(br * 25.6)
    else:
        return 0


# Extract mime type from text
rx_fmt = re.compile("ogg|mp3|mp4|theora|nsv|webm|opus|mpeg")
def guess_format(str):
    return rx_fmt.findall(str.lower() + "mpeg")[0]

