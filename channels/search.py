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
        # Update (x) current_channel checkbox
        if not self.current or self.main.current_channel != "bookmarks":
            self.current = self.main.current_channel
            self.search_dialog_current.set_label("just %s" % self.main.channels[self.current].meta["title"])
        # Update icon
        if "finder" in dir(self) and self.finder:
            self.search_img.set_from_pixbuf(uikit.pixbuf(self.finder))
            self.finder = None


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
        # traverse all channels modules
        for c in self.targets:
            cn = self.main.channels[c]
            if cn.streams:  # skip disabled plugins
                # categories
                for cat in cn.streams.keys():
                    # stations
                    for row in cn.streams[cat]:
                        # assemble text fields to compare
                        text = " ".join([str(row.get(f, " ")) for f in fields])
                        if text.lower().find(self.q) >= 0:
                            row = copy(row)
                            row["genre"] = "%s %s" % (c or "", row.get("genre")  or "")
                            entries.append(row)
        uikit.do(self.show_results, entries)

    # display "search" in "bookmarks"
    def show_results(self, entries):
        self.main.status(1.0)
        self.main.status("")
        self.main.channel_switch_by_name("bookmarks")
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
                log.PROC("has_search:", cn.module)
                try:
                    add = cn.update_streams(cat=None, search=self.q)
                    for row in add:
                        row["genre"] = cn.meta["title"] + " " + row.get("genre", "")
                    entries += add
                except Exception as e:
                    log.WARN("server_search: update_streams error in {}:".format(cn.module), e)
                    continue
            #main.status(main, 1.0 * i / 15)
        uikit.do(self.show_results, entries)


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


    # #ifdef PKG_ZIP
    finder = """
    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
    """
    # #endif
    
