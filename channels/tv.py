#
# api: streamtuner2
# title: shoutcast TV
# description: TV listings from shoutcast
# version: 0.0
# stolen-from: Tunapie.sf.net
#
# As seen in Tunapie, there are still TV listings on Shoutcast. This module
# adds a separate tab for them. Streamtuner2 is centrally and foremost about
# radio listings, so this plugin will remain one of the few exceptions.
#
#   http://www.shoutcast.com/sbin/newtvlister.phtml?alltv=1
#
# Pasing with lxml is dead simple in this case, so we use etree directly
# instead of PyQuery. Like with the Xiph plugin, downloaded streams are simply
# stored in .streams["all"] pseudo-category.
#
# icon: http://cemagraphics.deviantart.com/art/Little-Tv-Icon-96461135

from channels import *
import http
import lxml.etree




# TV listings from shoutcast.com
class tv(ChannelPlugin):

	# desc
	api = "streamtuner2"
	module = "tv"
	title = "TV"
	version = 0.1
	homepage = "http://www.shoutcast.com/" 
	base_url = "http://www.shoutcast.com/sbin/newtvlister.phtml?alltv=1"
	play_url = "http://yp.shoutcast.com/sbin/tunein-station.pls?id="
	listformat = "audio/x-scpls"  # video streams are NSV linked in PLS format

        # settings
        config = [
        ]
        
        # categories
        categories = ["all", "video"]
        current = ""
        default = "all"
        empty = ""

        # redefine
        streams = {}


        # get complete list
        def all(self):
            r = []

            # retrieve
            xml = http.get(self.base_url)
            
            # split up <station> entries
            for station in lxml.etree.fromstring(xml):

                r.append({
                    "title": station.get("name"),
                    "playing": station.get("ct"),
                    "id": station.get("id"),
                    "url": self.play_url + station.get("id"),
                    "format": "video/nsv",
                    "time": station.get("rt"),
                    "extra": station.get("load"),
                    "genre": station.get("genre"),
                    "bitrate": int(station.get("br")),
                    "listeners": int(station.get("lc")),
                })
                              
            return r
         
            
        # genre switch
        def load(self, cat, force=False):
            if force or not self.streams.get("all"):
                self.streams["all"] = self.all()
            ChannelPlugin.load(self, cat, force)
        
            
        # update from the list
        def update_categories(self):

            # update it always here:  #if not self.streams.get("all"):
            self.streams["all"] = self.all()

            # enumerate categories
            c = {"all":100000}
            for row in self.streams["all"]:
                for genre in row["genre"].split(" "):
                    if len(genre)>2 and row["bitrate"]>=200:
                        c[genre] = c.get(genre, 0) + 1
            # append
            self.categories = sorted(c, key=c.get, reverse=True)



        # extract from big list
        def update_streams(self, cat, search=""):

            # autoload only if "all" category is missing
            if not self.streams.get("all"):
                self.streams["all"] = self.all()
    
            # return complete list as-is            
            if cat == "all":
                return self.streams[cat]
                
            # search for category
            else:
                return [row for row in self.streams["all"] if row["genre"].find(cat)>=0]






