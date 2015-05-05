# encoding: UTF-8
# api: streamtuner2
# title: Compound★
# description: combines station lists from multiple channels
# version: 0.2
# type: channel
# category: virtual
# url: http://fossil.include-once.org/streamtuner2/
# config: -
#    { name: compound_channels, type: text, value: "shoutcast, internet_radio, xiph, surfmusik", description: "Channels to merge station lists from." }
#    { name: compound_genres, type: text, value: "Top 40", description: "Extract specific/favourite categories." }
#    { name: compound_intersect, type: boolean, value: 1, description: "Intersect genres which exist in 2 or more channels." }
# priority: unsupported
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABQAAAASCAYAAABb0P4QAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3wUFCigotf34ngAABGlJREFUOMttj++LVFUchz/f7znn3jtzZ+buzuzszv4SbbdVUTNp
#   o8DqXUFsUEFBBEFSr/ov8h8JJOhNWlFQhggJYWKaGZrruGW26e44O7/nztx77jmnF5b2oufl58XD86HuG7uQGzTRzU1i6tQmjh8/vhxF0dtpmq612+2VZrOZ77Tb/f5gcGVnZ+dEvV7/9MyZM3GtVoPWGkopZFmG3bt3AwBkxrn9iSq9yiLX+PqLz0qrq6vH+v3+wfX1de50OvH09HS2uLhYjOP4aKVSebZQKDwfBEFda50YY7aJaNkYcw7AOQCQ
#   rsgrEPigO7ekawuL1f4wLv5w/jyIOVtbW7vw+MpKJKWq9nvdX8MwfOn69evvJ0kSFwqFTQDXALwIwD4U2orSSRj09Auv747KU+GFi98gjuPOu8eOcSmQQ+/iR2CjPbf35R2bD52UEv9gATjnnAHg/h0Zk5yOapVRsHREpWmK+o3r8ZMHls9GExPG6LHzNk62/PonTU5aKYiclDITQmTOPXQQ/oO0kzJNaWLohxENW0PYdJAuzZeTNM2YWMJM5Xsu
#   cwK+lwrmpFqt/hyGYRUA43+QZta3zlDiYKw1BuWZXaXK4sFXtu78qAvi/iCclSmsSuALx0KkURTdY+bIOScexDHwqBYyOazyznYrjfZVQ1jBvn37uTYzW+x3Lg/vbX1sa4cwJaSskLExnCDnDD24SyBuGhZZ5uDso8IiicHABidPfcmjQQ2HDuwHM6M8cyi/0ZybbJduyyCQYTq4ZATfHRpdSoQ5CoBgghNDk/ulY7J8/FDYYlBzKNX9plajfgM3
#   byl0u10EfokSlL1te5sDCGn9s5q9Xkzj5SQazxqA0OUdOO6xpQyAA5OE3M6IxiWHoGyMjpWI4xiXfrqMPUsL6JrYNpmlchBwQsApAW6iUfiwD4KwGdyDnfmd196D9t+EbBiwDS1PPde7O/g8V56bnS212x1c/eqKa8m4MtxFXJyzSgIeFBQypyyPFADBJudDkrJjDoZ96cfjrpYNR6QtKToyvjlf3Qnmo+QpvzXq9aeuFc16YeWvb/cQLzWGKqI9
#   ak7m9e+5FXQnayiOTW5PNidmOcg2c0tRDQd8O7EhGwAlICFSkcfUyPtenU65Gf1pn+7sFXMT2/bGRORuLVZ0T62yb32MvCcoU8LM9nrxzFbFWfKoL2pCoEqONmTDEY0cCS8RJRgoLYXIs5CxE8L3rDHPbCfuMI/Cq9OtpBrXvIF/V5dHkYkSI6ygEYjzEjpnXGMUj2LZ0OChYJXXnIMDj0EUOaKOIy44Ym2ZdaRNcW+301nozJS2SvEoGoeA43wr
#   pJ4jjjzbX4ixXb9Rz+TOmMZ9QbeLDm0HYGSoZ9ndaloSCeFOCoTaUiED/tjJWGSgjdhS1wFUYLfVMuTSnKk/tuna84vzTnpXvXPlwHur2AoIAJJ8JoqdQPOmVPmBl2nPUiYN53uepr+UKnR9HeQD4eAQDFVGZanUgNu/bdfHpy9+h78Bc2RGfJQqXS8AAAAldEVYdGRhdGU6Y3JlYXRlADIwMTUtMDUtMDVUMTI6NDA6MTIrMDI6MDDJlQYgAAAA
#   JXRFWHRkYXRlOm1vZGlmeQAyMDE1LTA1LTA1VDEyOjQwOjEyKzAyOjAwuMi+nAAAAABJRU5ErkJggg==
# png-orig: https://openclipart.org/detail/215936/audio
# 
# Use this plugin to mix categories and their station entries from two
# or more different directory channels. It merges the lists, albeit in
# a simplistic way.
#
# Per default it lists only selected categories. But can be configured to
# merge just intersectioning categories/genres. Entry order is determined
# from station occourence count in channels AND their individual listener
# count (where available) using some guesswork to eliminate duplicates.


from channels import *
import action
from config import conf


# Merges categories from different channels
class compound (ChannelPlugin):

    # runtime options
    has_search = False
    listformat = "href"  # row entries will contain exact `listformat` classification
    audioformat = "audio/*"   # same as for correct encoding mime type
    
    # references
    parent = None
    
    # data
    streams = {}
    categories = []
    
    
    
    # Which categories
    def update_categories(self):

        # As-is category list
        cats = self.split(conf.compound_genres)
        self.categories = [c for c in cats if c != "x"]
        
        # Genre intersection requested
        if conf.compound_intersect:
            once = []
            for chan in self.channels():
                for add in self.flatten(self.parent.channels[chan].categories):
                    # second occourence in two channels
                    if add.lower() in once:
                        if add not in self.categories:
                            self.categories.append(add)
                    else: #if add not in self.categories:
                        once.append(add.lower())
                        
        
    # flatten our two-level categories list
    def flatten(self, a):
        return [i for sub in a for i in (sub if type(sub)==list else [sub])]


    # break up name lists        
    def split(self, s):
        return [s.strip() for s in s.split(",")]

    # List of channels
    def channels(self):

        # get list
        ls = self.split(conf.compound_channels)
      
        # resolve "*"
        if "*" in ls:
            ls = self.parent.channel_names  # includes bookmarks
            if self.module in ls:
                ls.remove(self.module)	    # but not compound

        return ls
          
          
    # Combine stream lists
    def update_streams(self, cat):
        r = []
        have = []
    
        # Look through channels
        if cat in self.categories:
            for cn in self.channels():
            
                # Get channel, refresh list
                c = self.parent.channels.get(cn)
                if not cn:
                    continue # skip misnamed pugins
                
                # 
                for row in self.get_streams(c, cat):

                    # copy
                    row = dict(row)
                    
                    #row["listeners"] = 1000 + row.get("listeners", 0) / 10
                    row["extra"] = cn  # or genre?
                    row["listformat"] = c.listformat

                    # duplicates                    
                    if row["title"].lower() in have or row["url"] in have:
                        for i,cmp in enumerate(r):
                            if cmp["title"].lower()==row["title"].lower() or cmp["url"].find(row["url"])>=0:
                                r[i]["listeners"] = row.get("listeners",0) + 5000
                        pass
                    else:
                        r.append(row)
                        have.append(row["title"].lower())  # we're comparing lowercase titles
                        have.append(row["url"][:row["url"].find("http://")])  # save last http:// part (internet-radio redirects to shoutcast urls)
                        
        # sort by listeners
        r = sorted(r, key=lambda x: -x.get("listeners", 0))
        return r


    # extract station list from other channel plugin    
    def get_streams(self, c, cat):

        # if empty?
        #c.load(cat)

        return c.streams.get(cat) \
            or c.update_streams(cat.replace(" ","")) \
            or []




    