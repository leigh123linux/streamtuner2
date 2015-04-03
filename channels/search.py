# api: streamtuner2
# title: Search feature
# description: Provides the quick search box, and server/cache search window.
# version: 0.9
# type: feature
# category: ui
# config: -
# priority: core
# 
# Configuration dialog for audio applications,
# general settings, and plugin activation and
# associated options.
#
# Some plugins hook into the saving method. Most
# require a restart of streamtuner2 for changes
# to take effect.


from uikit import *
import channels
from config import *
from copy import copy


# Search window, and quicksearch box handler.
#
# Aux win: search dialog - keeps search text in self.q
# Quick search textbox - uses main.q instead
#
class search (AuxiliaryWindow):

    # either current channel, or last channel (avoid searching in bookmarks)
    current = None

    # show search dialog   
    def menu_search(self, w):
        self.search_dialog.show_all();
        if not self.current or self.main.current_channel != "bookmarks":
            self.current = self.main.current_channel
            self.search_dialog_current.set_label("just %s" % self.main.channels[self.current].meta["title"])


    # hide dialog box again
    def cancel(self, *args):
        self.search_dialog.hide()
        return True  # stop any other gtk handlers
        

    # prepare variables
    def prepare_search(self):
        self.main.status("Searching... Stand back.")
        self.cancel()
        self.q = self.search_full.get_text().lower()
        if self.search_dialog_all.get_active():
            self.targets = self.main.channels.keys()
        else:
            self.targets = [self.current]
        self.main.bookmarks.streams["search"] = []
        
    # perform search
    def cache_search(self, *w):
        self.prepare_search()
        entries = []
        # which fields?
        fields = ["title", "playing", "homepage"]
        for i,cn in enumerate([self.main.channels[c] for c in self.targets]):
            if cn.streams:  # skip disabled plugins
                # categories
                for cat in cn.streams.keys():
                    # stations
                    for row in cn.streams[cat]:
                        # assemble text fields to compare
                        text = " ".join([str(row.get(f, " ")) for f in fields])
                        if text.lower().find(self.q) >= 0:
                            row = copy(row)
                            row["genre"] = c + " " + row.get("genre", "")
                            entries.append(row)
        self.show_results(entries)

    # display "search" in "bookmarks"
    def show_results(self, entries):
        self.main.status(1.0)
        self.main.status("")
        self.main.channel_switch(self.main.notebook_channels, "bookmarks", 0)
        self.main.bookmarks.set_category("search")
        # insert data and show
        self.main.channels["bookmarks"].streams["search"] = entries   # we have to set it here, else .currentcat() might reset it 
        self.main.bookmarks.load("search")
        
        
    # live search on directory server homepages
    def server_search(self, w):
        self.prepare_search()
        entries = []
        for i,cn in enumerate([self.main.channels[c] for c in self.targets]):
            if cn.has_search:  # "search" in cn.update_streams.func_code.co_varnames:
                self.main.status("Server searching: " + cn.module)
                __print__(dbg.PROC, "has_search:", cn.module)
                try:
                    add = cn.update_streams(cat=None, search=self.q)
                    for row in add:
                        row["genre"] = cn.meta["title"] + " " + row.get("genre", "")
                    entries += add
                except:
                    continue
            #main.status(main, 1.0 * i / 15)
        self.show_results(entries)


    # search text edited in text entry box
    def quicksearch_set(self, w, *eat, **up):
        
        # keep query string
        self.main.q = self.search_quick.get_text().lower()

        # get streams
        c = self.main.channel()
        rows = c.stations()
        col = c.rowmap.index("search_col") # this is the gtk.ListStore index # which contains the highlighting color

        # callback to compare (+highlight) rows
        m = c.gtk_list.get_model()
        m.foreach(self.quicksearch_treestore, (rows, self.main.q, col, col+1))
    search_set = quicksearch_set
        
        
        
    # callback that iterates over whole gtk treelist,
    # looks for search string and applies TreeList color and flag if found
    def quicksearch_treestore(self, model, path, iter, extra_data):
        i = path[0]
        (rows, q, color, flag) = extra_data

        # compare against interesting content fields:
        text = rows[i].get("title", "") + " " + rows[i].get("homepage", "")
        # config.quicksearch_fields
        text = text.lower()

        # simple string match (probably doesn't need full search expression support)
        if len(q) and text.find(q) >= 0:
           model.set_value(iter, color, "#fe9")  # highlighting color
           model.set_value(iter, flag, True) # background-set flag
        # color = 12 in liststore, flag = 13th position
        else:
           model.set_value(iter, color, "")   # for some reason the cellrenderer colors get applied to all rows, even if we specify an iter (=treelist position?, not?)
           model.set_value(iter, flag, False)   # that's why we need the secondary -set option

        #??
        return False


