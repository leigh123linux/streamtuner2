# encoding: UTF-8
# api: streamtuner2
# title: SomaFM
# description: Alternative radio, entirely community sponsored and non-advertisey.
# version: 0.9
# type: channel
# category: radio
# url: http://somafm.com/
# config:
#   { name: somafm_bitrate, value: 64, type: select, select: "130=AAC → 128 kbit/s|64=AAC → 64 kbit/s|32=AAC → 32 kbit/s|0=MP3 → 128 kbit/s|56=MP3 → 56 kbit/s|24=MP3 → 24 kbit/s", description: "Most streams are accessible in different bitrates." }
# priority: extra
# png:
#    iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAAAA3NCSVQICAjb4U/gAAACpUlEQVQokQXBS28bVRQA4HvOfcwd2xNP7caFtgiqkoglKyhCiFZiUSGxQcACdkis2SGx5lcgumFXhNoNGwpISGUZMKJSGtooStM4teOJXeOZufO4j8P3wZeff7r3z32tRaL7g/7Ikq/qXKEI4BZ5HnzYiJQn
#    50IAxuIkFe9/+NXDP+9JVr++tX3jk2/I29lkV0fd0DY741+z7PC9dz7Ki9XZ8kSrDudKSIBExx3ulVJJL5UcvVkoob0zm8Nzoc0uXnq1Mcuko9NewnkkgvNaMQVCQWirugz4w88/nUyPPrh+M9a9SGAIbVXWPlSmEkIxUeanArnkrLbNepX9vffw2x+/Z2Rni7PP3n0rjuLkxf7R8b+tMVYwaKzIJvuc
#    WkRE1j7dvX/77u0QcKOz8eDxnjk+2L6QDtLfpARXGssKEcVYtQwYcsCuiP74a7zzaB8Yy03DibXWjg+nv/9yz9fsP+NO182ybIRrV5aIA5ONOTw65oJrJQhCX8sYsSH+ZDopns8coyZU3Em8NNrUinMZT56vD+azWAkF1AUAS8vWrwKtnTuYZ97Zui7XdYkXh30GUqDczcPl0ebLg0HlnQZERkikOGFX
#    GuCmbvOynq8KzMoakaNKFMY3r11LtbKOeQYKMCZ4+3xyNWbzower9Vyx0JOI+4/GRWvLgq4Mo1Haq6pcCXBAAtl5bj9+I7313ddfvHkuNpkpKxaskI1Z1rp4NqWtV2ZPT04sAeeFBy4Di8W4rLaeHe+sxJ395aqcXhiN4LXtq6fZGSAQV0gEzMed/mJxmiYi1mIyMz1WV6itZ8G1/TTlqHRZFGVpgrcI
#    GIL3ntq2aRpXGAdEXkgOgMgiKTqdSLz0wqDo8UAEwIjIGF/VNun2iBEAU0pcHkYdBdaT9bA5TP8H6318x/9OSuUAAAAASUVORK5CYII=
#
# SomaFM is a non-commercial radio station project.
#
# Uses a static internal station list. Stream URLs are
# only rewritten depending on bitrate configuration.
#
# Note that only 64bit AAC and 128bit MP3 are guaranteed
# to be available. Most stations offer different bitrates,
# but not all of them!


from config import *
from channels import *
import re
import ahttp

# SomaFM radio stations
class somafm (ChannelPlugin):

    # description
    has_search = False
    listformat = "pls"
    audioformat = "audio/aac"
    titles = dict(listeners=False, playing="Description")

    categories = ["listen", "support"]
    streams = {
    "listen": [
        {'genre': 'ambient', 'listeners': 2187, 'title': 'Drone Zone', 'url': 'http://somafm.com/dronezone64.pls', 'bitrate': 64, 'homepage': 'http://somafm.com/dronezone/', 'playing': 'Served best chilled, safe with most medications. Atmospheric textures with minimal beats.'},
        {'genre': 'alternative', 'listeners': 420, 'title': 'Indie Pop Rocks!', 'url': 'http://somafm.com/indiepop64.pls', 'bitrate': 64, 'homepage': 'http://somafm.com/indiepop/', 'playing': 'New and classic favorite indie pop tracks.'},
        {'genre': 'electronica', 'listeners': 380, 'title': 'Lush', 'url': 'http://somafm.com/lush64.pls', 'bitrate': 64, 'homepage': 'http://somafm.com/lush/', 'playing': 'Sensuous and mellow vocals, mostly female, with an electronic influence.'},
        {'genre': 'lounge', 'listeners': 377, 'title': 'Secret Agent', 'url': 'http://somafm.com/secretagent64.pls', 'bitrate': 64, 'homepage': 'http://somafm.com/secretagent/', 'playing': 'The soundtrack for your stylish, mysterious, dangerous life. For Spies and PIs too!'},
        {'genre': 'electronica', 'listeners': 375, 'title': 'Space Station Soma', 'url': 'http://somafm.com/spacestation64.pls', 'bitrate': 64, 'homepage': 'http://somafm.com/spacestation/', 'playing': 'Tune in, turn on, space out. Spaced-out ambient and mid-tempo electronica.'},
        {'genre': 'americana', 'listeners': 337, 'title': 'Boot Liquor', 'url': 'http://somafm.com/bootliquor64.pls', 'bitrate': 64, 'homepage': 'http://somafm.com/bootliquor/', 'playing': 'Americana Roots music for Cowhands, Cowpokes and Cowtippers'},
        {'genre': 'ambient', 'listeners': 165, 'title': 'Deep Space One', 'url': 'http://somafm.com/deepspaceone64.pls', 'bitrate': 64, 'homepage': 'http://somafm.com/deepspaceone/', 'playing': 'Deep ambient electronic, experimental and space music. A soundtrack for inner and outer space exploration.'},
        {'genre': 'electronica', 'listeners': 149, 'title': 'Beat Blender', 'url': 'http://somafm.com/beatblender64.pls', 'bitrate': 64, 'homepage': 'http://somafm.com/beatblender/', 'playing': 'A late night blend of deep-house and downtempo chill.'},
        {'genre': 'alternative', 'listeners': 148, 'title': 'PopTron', 'url': 'http://somafm.com/poptron64.pls', 'bitrate': 64, 'homepage': 'http://somafm.com/poptron/', 'playing': 'Electropop and indie dance rock with sparkle and pop.'},
        {'genre': 'world', 'listeners': 121, 'title': 'Suburbs of Goa', 'url': 'http://somafm.com/suburbsofgoa64.pls', 'bitrate': 64, 'homepage': 'http://somafm.com/suburbsofgoa/', 'playing': 'Desi-influenced Asian world beats and beyond.'},
        {'genre': 'lounge', 'listeners': 112, 'title': 'Illinois Street Lounge', 'url': 'http://somafm.com/illstreet64.pls', 'bitrate': 64, 'homepage': 'http://somafm.com/illstreet/', 'playing': 'Classic bachelor pad, playful exotica and vintage music of tomorrow.'},
        {'genre': 'jazz', 'listeners': 111, 'title': 'Sonic Universe', 'url': 'http://somafm.com/sonicuniverse64.pls', 'bitrate': 64, 'homepage': 'http://somafm.com/sonicuniverse/', 'playing': 'Transcending the world of jazz with eclectic, avant-garde takes on tradition.'},
        {'genre': 'alternative', 'listeners': 92, 'title': 'BAGeL Radio', 'url': 'http://somafm.com/bagel64.pls', 'bitrate': 64, 'homepage': 'http://somafm.com/bagel/', 'playing': 'What alternative rock radio should sound like.'},
        {'genre': 'electronica', 'listeners': 89, 'title': 'The Trip', 'url': 'http://somafm.com/thetrip64.pls', 'bitrate': 64, 'homepage': 'http://somafm.com/thetrip/', 'playing': 'Progressive house / trance. Tip top tunes.'},
        {'genre': 'electronica', 'listeners': 87, 'title': 'Dub Step Beyond', 'url': 'http://somafm.com/dubstep64.pls', 'bitrate': 64, 'homepage': 'http://somafm.com/dubstep/', 'playing': 'Dubstep, Dub and Deep Bass. May damage speakers at high volume.'},
        {'genre': 'electronica', 'listeners': 77, 'title': 'cliqhop idm', 'url': 'http://somafm.com/cliqhop64.pls', 'bitrate': 64, 'homepage': 'http://somafm.com/cliqhop/', 'playing': u"Blips'n'beeps backed mostly w/beats. Intelligent Dance Music."},
        {'genre': 'alternative', 'listeners': 51, 'title': 'Seven Inch Soul', 'url': 'http://somafm.com/7soul64.pls', 'bitrate': 64, 'homepage': 'http://somafm.com/7soul/', 'playing': 'Vintage soul tracks from the original 45 RPM vinyl.'},
        {'genre': 'eclectic', 'listeners': 38, 'title': 'Black Rock FM', 'url': 'http://somafm.com/brfm64.pls', 'bitrate': 64, 'homepage': 'http://somafm.com/brfm/', 'playing': 'From the Playa to the world, for the 2014 Burning Man festival.'},
        {'genre': 'eclectic', 'listeners': 30, 'title': 'Covers', 'url': 'http://somafm.com/covers64.pls', 'bitrate': 64, 'homepage': 'http://somafm.com/covers/', 'playing': u"Just covers. Songs you know by artists you don't. We've got you covered."},
        {'genre': 'experimental', 'listeners': 14, 'title': 'Earwaves', 'url': 'http://somafm.com/earwaves64.pls', 'bitrate': 64, 'homepage': 'http://somafm.com/earwaves/', 'playing': 'Spanning the history of electronic and experimental music from the early pioneers to the latest innovators.'}
    ],
    "support": [
        {'genre': 'faq', 'listeners': 6398, 'title': 'Commercial-free, listener supported radio station.', 'url': 'https://youtube.com/v/DAjSPgRPhzw', 'format': 'video/youtube', 'bitrate': 256, 'homepage': 'http://somafm.com/support/', 'playing': 'Unique among music stations, SomaFM depends on community donations to operate. PS: SomaFM Loves You!!'}
    ]}

    # All static
    def update_categories(self):
        pass

    # Just update entries with bitrate setting
    def update_streams(self, cat, search=None):
        if not cat in self.categories:
            return
        
        # Just reuse
        rows = self.streams[cat] # or self._real_parse()
        
        # Overwrite bitrate
        bitreal = int(conf.somafm_bitrate) or 128
        biturl = int(conf.somafm_bitrate) or ""
        for i,row in enumerate(rows):
            rows[i]["format"] = "audio/mp3" if bitreal in (128,56,24) else "audio/aac"
            rows[i]["bitrate"] = int(bitreal)
            rows[i]["url"] = re.sub("\d*\.pls$", "%s.pls" % biturl, row["url"])
        
        # Resend stream list
        return rows

    # Disabled at runtime.
    def _real_parse(self):
        html = ahttp.get("http://somafm.com/listen/")
        ls = re.findall(r"""
            Listeners:\s(\d+) .*?
            <!-- .*? \((\w+)\)\s*--> .*?
            <h3>(.+?)</h3> .*?
            <p.*?>(.+?)</p> .*?
            href="(http://somafm.com/.+?.pls)" .*?
        """, html, re.X|re.S)
        rows = [
           dict(genre=g, title=t, playing=p, url=u, listeners=int(l), bitrate=128, homepage=re.sub("\d*\.pls$", "/", u))
            for l,g,t,p,u in ls
        ]
        #log.DATA(rows)
        return rows
        
