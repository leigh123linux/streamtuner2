#
# api: streamtuner2
# title: MUSICGOAL channel
# description: musicgoal.com/.de combines radio and podcast listings
# version: 0.1
# status: experimental
# pre-config: <const name="api"/>
#
# Musicgoal.com is a radio and podcast directory. This plugin tries to use
# the new API for accessing listing data.
#
#



# st2 modules
from config import conf
from mygtk import mygtk
import ahttp as http
from channels import *

# python modules
import re
import json



          
# I wonder what that is for                                             ---------------------------------------
class musicgoal (ChannelPlugin):

        # desc
        module = "musicgoal"
        title = "MUSICGOAL"
        version = 0.1
        homepage = "http://www.musicgoal.com/"
        base_url = homepage
        listformat = "url/direct"

        # settings
        config = [
        ]
        api_podcast = "http://www.musicgoal.com/api/?todo=export&todo2=%s&cat=%s&format=json&id=1000259223&user=streamtuner&pass=tralilala"
        api_radio = "http://www.musicgoal.com/api/?todo=playlist&format=json&genre=%s&id=1000259223&user=streamtuner&pass=tralilala"

        # categories are hardcoded
        podcast = ["Arts", "Management", "Recreation", "Knowledge", "Nutrition", "Books", "Movies & TV", "Music", "News", "Business", "Poetry", "Politic", "Radio", "Science", "Science Fiction", "Religion", "Sport", "Technic", "Travel", "Health", "New"]
        radio = ["Top radios", "Newcomer", "Alternative", "House", "Jazz", "Classic", "Metal", "Oldies", "Pop", "Rock", "Techno", "Country", "Funk", "Hip hop", "R&B", "Reggae", "Soul", "Indian", "Top40", "60s", "70s", "80s", "90s", "Sport", "Various", "Radio", "Party", "Christmas", "Firewall", "Auto DJ", "Audio-aacp", "Audio-ogg", "Video", "MyTop", "New", "World", "Full"]
        categories = ["podcasts/", podcast, "radios/", radio]
        #catmap = {"podcast": dict((i+1,v) for enumerate(self.podcast)), "radio": dict((i+1,v) for enumerate(self.radio))}
        


        # nop
        def update_categories(self):
            pass


        # request json API
        def update_streams(self, cat, search=""):

            # category type: podcast or radio
            if cat in self.podcast:
                grp = "podcast"
                url = self.api_podcast % (grp, self.podcast.index(cat)+1)
            elif cat in self.radio:
                grp = "radio"
                url = self.api_radio % cat.lower().replace(" ","").replace("&","")
            else:
                return []
                
            # retrieve API data
            data = http.ajax(url, None)
            data = json.loads(data)
                
            # tranform datasets            
            if grp == "podcast":
                return [{
                    "genre": cat,
                    "title": row["titel"],
                    "homepage": row["url"],
                    "playing": str(row["typ"]),
                    #"id": row["id"],
                    #"listeners": int(row["2"]),
                    #"listformat": "text/html",
                    "url": "",
                } for row in data]
            else:
                return [{
                    "format": self.mime_fmt(row["ctype"]),
                    "genre": row["genre"] or cat,
                    "url": "http://%s:%s/%s" % (row["host"], row["port"], row["pfad"]),
                    "listformat": "url/direct",
                    "id": row["id"],
                    "title": row["name"],
                    "playing": row["song"],
                    "homepage": row.get("homepage") or row.get("url"),
                } for row in data]




