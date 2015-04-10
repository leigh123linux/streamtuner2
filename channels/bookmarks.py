# encoding: UTF-8
# api: streamtuner2
# title: Bookmarks
# description: For collecting favourites. And provides some feature/category plugins.
# type: channel
# version: 1.5
# category: builtin
# priority: core
# config: { name: like_my_bookmarks,  type: boolean, value: 0, description: "I like my bookmarks" }
# url: http://freshcode.club/projects/streamtuner2
# 
# Favourite lists.
#
# This module lists static content from ~/.config/streamtuner2/bookmarks.json.
# Any bookmarked station will appear with a star ★ icon in other channels.
#
# Some feature extensions inject custom subcategories here. For example the
# "search" feature adds its own result list here, as does the "timer" plugin.


from config import *
from uikit import uikit
from channels import *



# The bookmarks tab is a core feature and built into the GtkBuilder
# layout. Which is why it derives from GenericChannel, and requires
# less setup.
#
# Furthermore it pretty much only handles a static streams{} list.
# Sub-plugins simply append a new category, and populate the streams
# list themselves.
#
# It's accessible as `parent.bookmarks` in the ST2 window and elsewhere.
#
class bookmarks(GenericChannel):

    # desc
    module = "bookmarks"
    title = "bookmarks"
    base_url = "file:.config/streamtuner2/bookmarks.json"
    listformat = "any"

    # content
    categories = ["favourite", ]  # timer, links, search, and links show up as needed
    current = "favourite"
    default = "favourite"
    finder_song = { "genre": "Youtube ", "format": "video/youtube", "playing": "current_", "title": "The Finder song", "url": "http://youtube.com/v/omyZy4H8y9M", "homepage": "http://youtu.be/omyZy4H8y9M" }
    streams = {"favourite":[finder_song], "search":[], "scripts":[], "timer":[], "history":[], }


    # cache list, to determine if a PLS url is bookmarked
    urls = []


    def gui(self, parent):
        GenericChannel.gui(self, parent)
        parent.notebook_channels.set_menu_label_text(parent.v_bookmarks, "bookmarks")


    # this channel does not actually retrieve/parse data from anywhere
    def update_categories(self):
        pass
        
    # but category sub-plugins might provide a hook
    category_plugins = {}
    def update_streams(self, cat):
        if cat in self.category_plugins:
            return self.category_plugins[cat].update_streams(cat) or []
        else:
            return self.streams.get(cat, [])

        
    # streams are already loaded at instantiation
    def first_show(self):
        pass


    # all entries just come from "bookmarks.json"
    def cache(self):
        # stream list
        cache = conf.load(self.module)
        if (cache):
            __print__(dbg.PROC, "load bookmarks.json")
            self.streams = cache
        


    # save to cache file
    def save(self):
        conf.save(self.module, self.streams, nice=1)


    # checks for existence of an URL in bookmarks store,
    # this method is called by other channel modules' display() method
    def is_in(self, url, once=1):
        if (not self.urls):
            self.urls = [row.get("url","urn:x-streamtuner2:no") for row in self.streams["favourite"]]
        return url in self.urls


    # called from main window / menu / context menu,
    # when bookmark is to be added for a selected stream entry
    def add(self, row):

        # normalize data (this row originated in a gtk+ widget)
        row["favourite"] = 1
        if row.get("favicon"):
           row["favicon"] = favicon.file(row.get("homepage"))
        if not row.get("listformat"):
            row["listformat"] = self.parent.channel().listformat
           
        # append to storage
        self.streams["favourite"].append(row)
        self.save()
        self.load(self.default)
        self.urls.append(row["url"])


    # simplified gtk TreeStore display logic (just one category for the moment, always rebuilt)
    def load(self, category, force=False):
        self.streams[category] = self.update_streams(category)
        #self.liststore[category] = \
        uikit.columns(self.gtk_list, self.datamap, self.prepare(self.streams[category]))


    # add a categories[]/streams{} subcategory, update treeview
    def add_category(self, cat, plugin=None):
        if cat not in self.categories: # add category if missing
            self.categories.append(cat)
            self.display_categories()
        if cat not in self.streams:
            self.streams[cat] = []
        if plugin:
            self.category_plugins[cat] = plugin


    # change cursor
    def set_category(self, cat):
        self.add_category(cat)
        self.gtk_cat.get_selection().select_path(str(self.categories.index(cat)))
        return self.currentcat()
        
        
    # update bookmarks from freshly loaded streams data
    def heuristic_update(self, updated_channel, updated_category):

        if not conf.heuristic_bookmark_update: return
        __print__(dbg.PROC, "heuristic bookmark update")
        save = 0
        fav = self.streams["favourite"]

        # First we'll generate a list of current bookmark stream urls, and then
        # remove all but those from the currently UPDATED_channel + category.
        # This step is most likely redundant, but prevents accidently re-rewriting
        # stations that are in two channels (=duplicates with different PLS urls).
        check = {"http//": "[row]"}
        check = dict((row.get("url", "http//"),row) for row in fav)
        # walk through all channels/streams
        for chname,channel in self.parent.channels.items():
            for cat,streams in channel.streams.items():

                # keep the potentially changed rows
                if (chname == updated_channel) and (cat == updated_category):
                    freshened_streams = streams

                # remove unchanged urls/rows
                else:
                    unchanged_urls = (row.get("url") for row in streams)
                    for url in unchanged_urls:
                        if url in check:
                            del check[url]
                            # directory duplicates could unset the check list here,
                            # so we later end up doing a deep comparison


        # now the real comparison,
        # where we compare station titles and homepage url to detect if a bookmark is an old entry
        for row in freshened_streams:
            url = row.get("url")
            
            # empty entry (google stations), or stream still in current favourites
            if not url or url in check:
                pass

            # need to search
            else:
                title = row.get("title")
                homepage = row.get("homepage")
                for i,old in enumerate(fav):

                    # skip if new url already in streams
                    if url == old.get("url"):
                        pass   # This is caused by channel duplicates with identical PLS links.
                    
                    # on exact matches (but skip if url is identical anyway)
                    elif title == old["title"] and homepage == old.get("homepage",homepage):
                        # update stream url
                        fav[i]["url"] = url
                        save = 1
                        
                    # more text similarity heuristics might go here
                    else:
                        pass
        
        # if there were changes
        if save: self.save()

