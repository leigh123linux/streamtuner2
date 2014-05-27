#
# api: streamtuner2
# title: History
# description: List recently played stations under favourites > history.
# version: 1.0
# type: category
# category: ui
# priority: optional
# 
# Lists last activated streams in a new [history] tab in the favourites
# channel.
#
#
#



from config import conf, __print__, dbg
from channels import *



class history:

    # plugin info
    module = "history"
    title = "History"
    
    
    # configuration settings
    config = [
        {
            "name": "history",
            "type": "int",
            "value": "20",
            "description": "Number of last played streams to keep in history list.",
            "category": "limit"
        }
    ]
    
    # store
    bm = None


    # hook up to main tab
    def __init__(self, parent):

        # keep reference to main window    
        self.bm = parent.channels["bookmarks"]

        # create category
        self.bm.add_category("history");

        # hook up to .play event
        parent.hooks["play"].append(self.queue)

        
    # add to favourites/history stream list
    def queue(self, row):
    
        # assert a present store
        streams = self.bm.streams
        if not "history" in streams:
            streams["history"] = []
        hist = streams["history"]

        # only new entries get added
        if not row in hist:
            hist.insert(0, row)
        
        # limit number of entries
        max = int(conf.history)
        while max > 0 and  len(hist) > max:
            hist.pop()

        # update store
        self.bm.save()
        #if self.bm.current == "history":
        #   self.bm.load("history")
