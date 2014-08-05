#
# api: streamtuner2
# title: Shoutcast.com
# description: Primary list of shoutcast servers (now managed by radionomy).
# type: channel
# category: radio
# priority: default
# version: 1.5
# depends: pq, re, http
# author: Mario
# original: Jean-Yves Lefort
#
# Shoutcast is a server software for audio streaming. It automatically spools
# station information on shoutcast.com
# It has been aquired by Radionomy in 2014, since then significant changes
# took place. The former YP got deprecated, now seemingly undeprecated.
#
#   http://wiki.winamp.com/wiki/SHOUTcast_Radio_Directory_API 
#
# But neither their Wiki nor Bulletin Board provide concrete information on
# the eligibility of open source desktop apps for an authhash.
#
# Therefore we'll be retrieving stuff from the homepage still. The new
# interface conveniently uses JSON already, so let's use that:
#
#   POST http://www.shoutcast.com/Home/BrowseByGenre {genrename: Pop}
#
# We do need a catmap now too, but that's easy to aquire and will be kept
# within the cache dirs.
#
#
#

import ahttp as http
from json import loads as json_decode
import re
from config import conf, __print__, dbg
from pq import pq
#from channels import *    # works everywhere but in this plugin(???!)
import channels
from compat2and3 import urllib



# SHOUTcast data module                                          ----------------------------------------
class shoutcast(channels.ChannelPlugin):

    # desc
    api = "streamtuner2"
    module = "shoutcast"
    title = "SHOUTcast"
    homepage = "http://www.shoutcast.com/" 
    base_url = "http://shoutcast.com/"
    listformat = "audio/x-scpls"

    # settings
    config = [
    ]
    
    # categories
    categories = []
    catmap = {"Choral": 35, "Winter": 275, "JROCK": 306, "Motown": 237, "Political": 290, "Tango": 192, "Ska": 22, "Comedy": 283, "Decades": 212, "European": 143, "Reggaeton": 189, "Islamic": 307, "Freestyle": 114, "French": 145, "Western": 53, "Dancepunk": 6, "News": 287, "Xtreme": 23, "Bollywood": 138, "Celtic": 141, "Kids": 278, "Filipino": 144, "Hanukkah": 270, "Greek": 146, "Punk": 21, "Spiritual": 211, "Industrial": 14, "Baroque": 33, "Talk": 282, "JPOP": 227, "Scanner": 291, "Mediterranean": 154, "Swing": 174, "Themes": 89, "IDM": 75, "40s": 214, "Funk": 236, "Rap": 110, "House": 74, "Educational": 285, "Caribbean": 140, "Misc": 295, "30s": 213, "Anniversary": 266, "Sports": 293, "International": 134, "Tribute": 107, "Piano": 41, "Romantic": 42, "90s": 219, "Latin": 177, "Grunge": 10, "Dubstep": 312, "Government": 286, "Country": 44, "Salsa": 191, "Hardcore": 11, "Afrikaans": 309, "Downtempo": 69, "Merengue": 187, "Psychedelic": 260, "Female": 95, "Bop": 167, "Tribal": 80, "Metal": 195, "70s": 217, "Tejano": 193, "Exotica": 55, "Anime": 277, "BlogTalk": 296, "African": 135, "Patriotic": 101, "Blues": 24, "Turntablism": 119, "Chinese": 142, "Garage": 72, "Dance": 66, "Valentine": 273, "Barbershop": 222, "Alternative": 1, "Technology": 294, "Folk": 82, "Klezmer": 152, "Samba": 315, "Turkish": 305, "Trance": 79, "Dub": 245, "Rock": 250, "Polka": 59, "Modern": 39, "Lounge": 57, "Indian": 149, "Hindi": 148, "Brazilian": 139, "Eclectic": 93, "Korean": 153, "Creole": 316, "Dancehall": 244, "Surf": 264, "Reggae": 242, "Goth": 9, "Oldies": 226, "Zouk": 162, "Environmental": 207, "Techno": 78, "Adult": 90, "Rockabilly": 262, "Wedding": 274, "Russian": 157, "Sexy": 104, "Chill": 92, "Opera": 40, "Emo": 8, "Experimental": 94, "Showtunes": 280, "Breakbeat": 65, "Jungle": 76, "Soundtracks": 276, "LoFi": 15, "Metalcore": 202, "Bachata": 178, "Kwanzaa": 272, "Banda": 179, "Americana": 46, "Classical": 32, "German": 302, "Tamil": 160, "Bluegrass": 47, "Halloween": 269, "College": 300, "Ambient": 63, "Birthday": 267, "Meditation": 210, "Electronic": 61, "50s": 215, "Chamber": 34, "Heartache": 96, "Britpop": 3, "Soca": 158, "Grindcore": 199, "Reality": 103, "00s": 303, "Symphony": 43, "Pop": 220, "Ranchera": 188, "Electro": 71, "Christmas": 268, "Christian": 123, "Progressive": 77, "Jazz": 163, "Trippy": 108, "Instrumental": 97, "Tropicalia": 194, "Fusion": 170, "Healing": 209, "Glam": 255, "80s": 218, "KPOP": 308, "Worldbeat": 161, "Mixtapes": 117, "60s": 216, "Mariachi": 186, "Soul": 240, "Cumbia": 181, "Inspirational": 122, "Impressionist": 38, "Gospel": 129, "Disco": 68, "Arabic": 136, "Idols": 225, "Ragga": 247, "Demo": 67, "LGBT": 98, "Honeymoon": 271, "Japanese": 150, "Community": 284, "Weather": 317, "Asian": 137, "Hebrew": 151, "Flamenco": 314, "Shuffle": 105}
    current = ""
    default = "Alternative"
    empty = ""
    
    # redefine
    streams = {}
    
        
    # Extracts the category list from www.shoutcast.com,
    # stores a catmap (title => id)
    def update_categories(self):
        html = http.get(self.base_url)
        #__print__( dbg.DATA, html )
        self.categories = []
        
        # Genre list in sidebar
        """  <li><a id="genre-90" href="/Genre?name=Adult" onclick="loadStationsByGenre('Adult', 90, 89); return false;">Adult</a></li> """
        rx = re.compile(r"loadStationsByGenre\(  '([^']+)' [,\s]* (\d+) [,\s]* (\d+)  \)", re.X)
        subs = rx.findall(html)

        # group
        current = []
        for (title, id, main) in subs:
            self.catmap[title] = int(id)
            if not int(main):
                self.categories.append(title)
                current = []
                self.categories.append(current)
            else:
                current.append(title)
        self.save()


    # downloads stream list from shoutcast for given category
    def update_streams(self, cat):

        if (cat not in self.catmap):
            __print__( dbg.ERR, "nocat" )
            return []
        id = self.catmap[cat]

        # page
        url = "http://www.shoutcast.com/Home/BrowseByGenre"
        params = { "genrename": cat }
        referer = None
        json = http.get(url, params=params, referer=referer, post=1, ajax=1)
        self.parent.status(0.75)

        # remap JSON
        entries = []
        for e in json_decode(json):
            entries.append({
                "id": int(e.get("ID", 0)),
                "genre": str(e.get("Genre", "")),
                "title": str(e.get("Name", "")),
                "playing": str(e.get("CurrentTrack", "")),
                "bitrate": int(e.get("Bitrate", 0)),
                "listeners": int(e.get("Listeners", 0)),
                "url": "http://yp.shoutcast.com/sbin/tunein-station.pls?id=%s" % e.get("ID", "0"),
                "homepage": "",
                "format": "audio/mpeg"
            })

        #__print__(dbg.DATA, entries)
        return entries


    # saves .streams and .catmap
    def save(self):
        channels.ChannelPlugin.save(self)
        conf.save("cache/catmap_" + self.module, self.catmap)

    # read previous channel/stream data, if there is any
    def cache(self):
        channels.ChannelPlugin.cache(self)
        self.catmap = conf.load("cache/catmap_" + self.module) or {}

