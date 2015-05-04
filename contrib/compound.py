# encoding: UTF-8
# api: streamtuner2
# title: Compound★
# description: combines station lists from multiple channels
# version: 0.1
# type: channel
# category: virtual
# url: http://fossil.include-once.org/streamtuner2/
# config: -
#    { name: compound_channels, type: text, value: "shoutcast, internet_radio, xiph, surfmusic", description: "Merge channels, or use all (*)" }
#    { name: compound_genres, type: text, value: "Top 40, x", description: "Extract categories, or just use intersection (x)" }
# priority: unsupported
# 
# Use this plugin to mix categories and their station entries from two
# or more different directory channels. It merges the lists, albeit in
# a rather crude way. (If anyone is interested, I could add a proper
# regex or something now.)
#
# Per default it lists only selected categories. But can be configured to
# merge just intersectioning categories/genres. Entry order is determined
# from station occourence count in channels AND their individual listener
# count (where available) using some guesswork to eliminate duplicates.



from channels import *
import action
from config import conf





# merging channel
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
    
    
    
    # which categories
    def update_categories(self):

        # as-is category list
        cats = self.split(conf.compound_genres)
        self.categories = [c for c in cats if c != "x"]
        
        # if intersection
        if "x" in cats:
            once = []
            for chan in self.channels():
                for add in self.flatten(self.parent.channels[chan].categories):
                    # second occourence in two channels
                    if add.lower() in once:
                        if add not in self.categories:
                            self.categories.append(add)
                    else: #if add not in self.categories:
                        once.append(add.lower())
        pass
                        
        
    # flatten our two-level categories list
    def flatten(self, a):
        return [i for sub in a for i in (sub if type(sub)==list else [sub])]


    # break up name lists        
    def split(self, s):
        return [s.strip() for s in s.split(",")]

    # get list of channels
    def channels(self):

        # get list
        ls = self.split(conf.compound_channels)
      
        # resolve "*"
        if "*" in ls:
            ls = self.parent.channel_names  # includes bookmarks
            if self.module in ls:
                ls.remove(self.module)	    # but not compound

        return ls
          
          
    # combine stream lists
    def update_streams(self, cat):
        r = []
        have = []
    
        # look through channels
        if cat in self.categories:
            for cn in self.channels():
            
                # get channel, refresh list
                c = self.parent.channels[cn]
                
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




    