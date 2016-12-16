#
# api: streamtuner2
# title: History
# description: List recently played stations under favourites > history.
# version: 1.0
# type: group
# category: ui
# config:
#     { name: history,  type: int,  value: 20,  description: Number of last played streams to keep in history list.,  category: limit }
# priority: optional
#
# Lists recently played streams in a new [history] tab in the
# bookmarks channel.


from config import *
from channels import *


class history (object):

    # plugin attributes
    module = 'history'
    meta = plugin_meta()
    
    # store
    bm = None


    # hook up to main tab
    def __init__(self, parent):
        self.config = self.meta["config"]
        conf.add_plugin_defaults(self.meta, self.module)

        # keep reference to main window    
        self.bm = parent.channels["bookmarks"]

        # create category
        self.bm.add_category("history");
        self.bm.reload_if_current(self.module)

        # hook up to .play event
        parent.hooks["play"].append(self.queue)

        
    # add to favourites/history stream list
    def queue(self, row, *x, **y):
    
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
        self.bm.reload_if_current(self.module)




