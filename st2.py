#!/usr/bin/env python
#
# encoding: UTF-8
# api: python
# type: application
# title: streamtuner2
# description: Directory browser for internet radio / audio streams
# depends: pygtk | gi, threading, requests, pyquery, lxml, deb:python-pyquery, deb:python-requests, deb:python-gtk2
# version: 2.1.4
# author: Mario Salzer <milky@users.sf.net>
# license: public domain
# url: http://freshcode.club/projects/streamtuner2
# config:  
#   { type: env, name: http_proxy, description: proxy for HTTP access }
#   { type: env, name: XDG_CONFIG_HOME, description: relocates user .config subdirectory }
# category: sound
# id: streamtuner2
# pack: *.py, gtk*.xml, st2.py=/usr/bin/streamtuner2, channels/__init__.py, bundle/*.py,
#   streamtuner2.desktop=/usr/share/applications/, README=/usr/share/doc/streamtuner2/,
#   NEWS.gz=/usr/share/doc/streamtuner2/changelog.gz, help/streamtuner2.1=/usr/share/man/man1/,
#   help/*page=/usr/share/doc/streamtuner2/help/, help/img/*=/usr/share/doc/streamtuner2/help/img/,
#   streamtuner2.png, logo.png=/usr/share/pixmaps/streamtuner2.png,
# architecture: all
#
# Streamtuner2 is a GUI browser for internet radio directories. Various
# providers can be added, and streaming stations are usually grouped into
# music genres or categories. It starts external audio players for stream
# playing, and defaults to streamripper for recording broadcasts.
#
# It's an independent rewrite of streamtuner1. Being written in Python,
# can be more easily extended and fixed. The mix of JSON APIs, regex
# or PyQuery extraction makes list generation simpler and more robust.
#
# Primarily radio stations are displayed, some channels however are music
# collections. Commercial and sign-up services are not the target purpose.
#



# standard modules
import sys
import os, os.path
import re
from collections import namedtuple
from copy import copy

# threading or processing module
try:
    from processing import Process as Thread
except:
    from threading import Thread
    Thread.stop = lambda self: None

# add library path
sys.path.insert(0, "/usr/share/streamtuner2")   # pre-defined directory for modules
sys.path.append(   "/usr/share/streamtuner2/bundle")   # external libraries
sys.path.insert(0, ".")   # development module path

# gtk modules
from mygtk import pygtk, gtk, gobject, ui_file, mygtk, ver as GTK_VER, ComboBoxText, gui_startup

# custom modules
from config import conf   # initializes itself, so all conf.vars are available right away
from config import __print__, dbg
import ahttp
import action  # needs workaround... (action.main=main)
import channels
from channels import *
import favicon
import channels.bookmarks

__version__ = "2.1.4"


# this represents the main window
# and also contains most application behaviour
main = None
class StreamTunerTwo(gtk.Builder):


        # object containers
        widgets = {}     # non-glade widgets (the manually instantiated ones)
        channels = {}    # channel modules
        features = {}    # non-channel plugins
        working = []     # threads
        add_signals = {} # channel gtk-handler signals
        hooks = {
            "play": [favicon.download_playing],  # observers queue here
            "init": [],
            "config_load": [],
            "config_save": [],
        }

        # status variables
        channel_names = ["bookmarks"]    # order of channel notebook tabs
        current_channel = "bookmarks"    # currently selected channel name (as index in self.channels{})


        # constructor
        def __init__(self):

            # gtkrc stylesheet
            self.load_theme(), gui_startup(1/20.0)

            # instantiate gtk/glade widgets in current object
            gtk.Builder.__init__(self)
            gtk.Builder.add_from_file(self, conf.find_in_dirs([".", conf.share], ui_file)), gui_startup(2/20.0)
            # manual gtk operations
            self.extensionsCTM.set_submenu(self.extensions)  # duplicates Station>Extension menu into stream context menu

            # initialize channels
            self.channels = {
              "bookmarks": channels.bookmarks.bookmarks(parent=self),   # this the remaining built-in channel
              #"shoutcast": None,#shoutcast(parent=self),
            }
            gui_startup(3/20.0)
            self.load_plugin_channels()   # append other channel modules / plugins


            # load application state (widget sizes, selections, etc.)
            try:
                winlayout = conf.load("window")
                if (winlayout):
                    mygtk.app_restore(self, winlayout)
                # selection values
                winstate = conf.load("state")
                if (winstate):
                    for id in winstate.keys():
                        self.channels[id].current = winstate[id]["current"]
                        self.channels[id].shown = winlayout[id+"_list"].get("row:selected", 0)   # actually just used as boolean flag (for late loading of stream list), selection bar has been positioned before already
            except:
                pass # fails for disabled/reordered plugin channels

            # late plugin initializations
            gui_startup(17/20.0)
            [callback(self) for callback in self.hooks["init"]]

            # display current open channel/notebook tab
            gui_startup(18/20.0)
            self.current_channel = self.current_channel_gtk()
            try: self.channel().first_show()
            except: __print__(dbg.INIT, "main.__init__: current_channel.first_show() initialization error")

      
            # bind gtk/glade event names to functions
            gui_startup(19/20.0)
            self.connect_signals(dict( list({
                "gtk_main_quit" : self.gtk_main_quit,                # close window
                # treeviews / notebook
                "on_stream_row_activated" : self.on_play_clicked,    # double click in a streams list
                "on_category_clicked": self.on_category_clicked,     # new selection in category list
                "on_notebook_channels_switch_page": self.channel_switch,   # channel notebook tab changed
                "station_context_menu": lambda tv,ev: station_context_menu(tv,ev),
                # toolbar
                "on_play_clicked" : self.on_play_clicked,
                "on_record_clicked": self.on_record_clicked,
                "on_homepage_stream_clicked": self.on_homepage_stream_clicked,
                "on_reload_clicked": self.on_reload_clicked,
                "on_stop_clicked": self.on_stop_clicked,
                "on_homepage_channel_clicked" : self.on_homepage_channel_clicked,
                "double_click_channel_tab": self.on_homepage_channel_clicked,
                # menu
                "menu_toolbar_standard": lambda w: (self.toolbar.unset_style(), self.toolbar.unset_icon_size()),
                "menu_toolbar_style_icons": lambda w: (self.toolbar.set_style(gtk.TOOLBAR_ICONS)),
                "menu_toolbar_style_both": lambda w: (self.toolbar.set_style(gtk.TOOLBAR_BOTH)),
                "menu_toolbar_size_small": lambda w: (self.toolbar.set_icon_size(gtk.ICON_SIZE_SMALL_TOOLBAR)),
                "menu_toolbar_size_medium": lambda w: (self.toolbar.set_icon_size(gtk.ICON_SIZE_DND)),
                "menu_toolbar_size_large": lambda w: (self.toolbar.set_icon_size(gtk.ICON_SIZE_DIALOG)),
                "menu_notebook_pos_top": lambda w: self.notebook_channels.set_tab_pos(2),
                "menu_notebook_pos_left": lambda w: self.notebook_channels.set_tab_pos(0),
                "menu_notebook_pos_right": lambda w: self.notebook_channels.set_tab_pos(1),
                "menu_notebook_pos_bottom": lambda w: self.notebook_channels.set_tab_pos(3),
                # win_config
                "menu_properties": config_dialog.open,
                "config_cancel": config_dialog.hide,
                "config_save": config_dialog.save,
                "config_play_list_edit_col0": lambda w,path,txt: (config_dialog.list_edit(self.config_play, path, 0, txt)),
                "config_play_list_edit_col1": lambda w,path,txt: (config_dialog.list_edit(self.config_play, path, 1, txt)),
                "config_record_list_edit_col0": lambda w,path,txt: (config_dialog.list_edit(self.config_record, path, 0, txt)),
                "config_record_list_edit_col1": lambda w,path,txt: (config_dialog.list_edit(self.config_record, path, 1, txt)),
                # else
                "update_categories": self.update_categories,
                "update_favicons": self.update_favicons,
                "app_state": self.app_state,
                "bookmark": self.bookmark,
                "save_as": self.save_as,
                "menu_about": lambda w: AboutStreamtuner2(),
                "menu_help": action.action.help,
                "menu_onlineforum": lambda w: action.browser("http://sourceforge.net/projects/streamtuner2/forums/forum/1173108"),
                "menu_fossilwiki": lambda w: action.browser("http://fossil.include-once.org/streamtuner2/"),
                "menu_projhomepage": lambda w: action.browser("http://milki.include-once.org/streamtuner2/"),
               # "menu_bugreport": lambda w: BugReport(),
                "menu_copy": self.menu_copy,
                "delete_entry": self.delete_entry,
                # search dialog
                "quicksearch_set": search.quicksearch_set,
                "search_open": search.menu_search,
                "search_go": search.cache_search,
                "search_srv": search.server_search,
                "search_cancel": search.cancel,
                "true": lambda w,*args: True,
                # win_streamedit
                "streamedit_open": streamedit.open,
                "streamedit_save": streamedit.save,
                "streamedit_new": streamedit.new,
                "streamedit_cancel": streamedit.cancel,
            }.items() ) + list( self.add_signals.items() ) ))
            
            # actually display main window
            gui_startup(98.9/100.0)
            self.win_streamtuner2.show()
            

        #-- Shortcut for glade.get_widget()
        # Allows access to widgets as direct attributes instead of using .get_widget()
        # Also looks in self.channels[] for the named channel plugins
        def __getattr__(self, name):
            if (name in self.channels):
                return self.channels[name]     # like self.shoutcast
            else:
                return self.get_object(name)   # or gives an error if neither exists

        # Custom-named widgets are available from .widgets{} not via .get_widget()
        def get_widget(self, name):
            if name in self.widgets:
                return self.widgets[name]
            else:
                return gtk.Builder.get_object(self, name)
                
        # returns the currently selected directory/channel object (remembered position)
        def channel(self):
            return self.channels[self.current_channel]

        # returns the currently selected directory/channel object (from gtk)
        def current_channel_gtk(self):
            i = self.notebook_channels.get_current_page()
            try: return self.channel_names[i]
            except: return "bookmarks"

        # Notebook tab clicked
        def channel_switch(self, notebook, page, page_num=0, *args):

            # can be called from channelmenu as well:
            if type(page) == str:
                self.current_channel = page
                self.notebook_channels.set_current_page(self.channel_names.index(page))
            # notebook invocation:
            else: #if type(page_num) == int:
                self.current_channel = self.channel_names[page_num]
            
            # if first selected, load current category
            try:
                __print__(dbg.PROC, "channel_switch: try .first_show", self.channel().module);
                self.channel().first_show()
            except:
                __print__(dbg.INIT, "channel .first_show() initialization error")

        # Convert ListStore iter to row number
        def rowno(self):
            (model, iter) = self.model_iter()
            return model.get_path(iter)[0]

        # Currently selected entry in stations list, return complete data dict
        def row(self):
            return self.channel().stations() [self.rowno()]

            
        # return ListStore object and Iterator for currently selected row in gtk.TreeView station list
        def model_iter(self):
            return self.channel().gtk_list.get_selection().get_selected()
            
        # Fetches a single varname from currently selected station entry
        def selected(self, name="url"):
            return self.row().get(name)


                
        # Play button
        def on_play_clicked(self, widget, event=None, *args):
            row = self.row()
            if row:
                self.channel().play(row)
                [callback(row) for callback in self.hooks["play"]]

        # Recording: invoke streamripper for current stream URL
        def on_record_clicked(self, widget):
            row = self.row()
            action.record(row.get("url"), row.get("format", "audio/mpeg"), "url/direct", row=row)

        # Open stream homepage in web browser
        def on_homepage_stream_clicked(self, widget):
            url = self.selected("homepage")             
            action.browser(url)

        # Browse to channel homepage (double click on notebook tab)
        def on_homepage_channel_clicked(self, widget, event=2):
            if event == 2 or event.type == gtk.gdk._2BUTTON_PRESS:
                __print__(dbg.UI, "dblclick")
                action.browser(self.channel().homepage)            

        # Reload stream list in current channel-category
        def on_reload_clicked(self, widget=None, reload=1):
            __print__(dbg.UI, "reload", reload, self.current_channel, self.channels[self.current_channel], self.channel().current)
            category = self.channel().current
            self.thread(
                lambda: (  self.channel().load(category,reload), reload and self.bookmarks.heuristic_update(self.current_channel,category)  )
            )

        # Thread a function, add to worker pool (for utilizing stop button)
        def thread(self, target, *args):
            thread = Thread(target=target, args=args)
            thread.start()
            self.working.append(thread)

        # Stop reload/update threads
        def on_stop_clicked(self, widget):
            while self.working:
                thread = self.working.pop()
                thread.stop()

        # Click in category list
        def on_category_clicked(self, widget, event, *more):
            category = self.channel().currentcat()
            __print__(dbg.UI, "on_category_clicked", category, self.current_channel)
            self.on_reload_clicked(None, reload=0)
            pass

        # Add current selection to bookmark store
        def bookmark(self, widget):
            self.bookmarks.add(self.row())
            # code to update current list (set icon just in on-screen liststore, it would be updated with next display() anyhow - and there's no need to invalidate the ls cache, because that's referenced by model anyhow)
            try:
                (model,iter) = self.model_iter()
                model.set_value(iter, 0, gtk.STOCK_ABOUT)
            except:
                pass
            # refresh bookmarks tab
            self.bookmarks.load(self.bookmarks.default)

        # Reload category tree
        def update_categories(self, widget):
            Thread(target=self.channel().reload_categories).start()

        # Menu invocation: refresh favicons for all stations in current streams category
        def update_favicons(self, widget):
            entries = self.channel().stations()
            favicon.download_all(entries)

        # Save stream to file (.m3u)
        def save_as(self, widget):
            row = self.row()
            default_fn = row["title"] + ".m3u"
            fn = mygtk.save_file("Save Stream", None, default_fn, [(".m3u","*m3u"),(".pls","*pls"),(".xspf","*xspf"),(".smil","*smil"),(".asx","*asx"),("all files","*")])
            if fn:
                action.save(row, fn)
            pass

        # Save current stream URL into clipboard
        def menu_copy(self, w):
            gtk.clipboard_get().set_text(self.selected("url"))

        # Remove a stream entry
        def delete_entry(self, w):
            n = self.rowno()
            del self.channel().stations()[ n ]
            self.channel().switch()
            self.channel().save()

        # Richt clicking a stream opens an action content menu
        def station_context_menu(self, treeview, event):
            return station_context_menu(treeview, event) # wrapper to the static function

        # Alternative Notebook channel tabs between TOP and LEFT position
        def switch_notebook_tabs_position(self, w, pos):
            self.notebook_channels.set_tab_pos(pos);
            




        # shortcut to statusbar
        # (hacked to work from within threads, circumvents the statusbar msg pool actually)
        def status(self, text="", sbar_msg=[]):
            # init
            sbar_cid = self.get_widget("statusbar").get_context_id("messages")
            # remove text
            while ((not text) and (type(text)==str) and len(sbar_msg)):
                sbar_msg.pop()
                mygtk.do(lambda:self.statusbar.pop(sbar_cid))
            # progressbar
            if (type(text)==float):
                if (text >= 999.0/1000):  # completed
                    mygtk.do(lambda:self.progress.hide())
                else:  # show percentage
                    mygtk.do(lambda:self.progress.show() or self.progress.set_fraction(text))
                    if (text <= 0):  # unknown state
                        mygtk.do(lambda:self.progress.pulse())
            # add text
            elif (type(text)==str):
                sbar_msg.append(1)
                mygtk.do(lambda:self.statusbar.push(sbar_cid, text))
            pass


        # load plugins from /usr/share/streamtuner2/channels/
        def load_plugin_channels(self):

            # find and order plugin files
            ls = channels.module_list()

            # step through
            for module in ls:
                gui_startup(2/10.0 + 7/10.0 * float(ls.index(module))/len(ls), "loading module "+module)
                                
                # skip module if disabled
                if conf.plugins.get(module, 1) == False:
                    __print__(dbg.STAT, "disabled plugin:", module)
                    continue
                
                # load plugin
                try:
                    plugin = __import__("channels."+module, None, None, [""])
                    plugin_class = plugin.__dict__[module]
                    plugin_obj = plugin_class(parent=self)
                    
                    # load .config settings from plugin
                    conf.add_plugin_defaults(plugin_obj.meta["config"], module)

                    # add and initialize channel
                    if issubclass(plugin_class, GenericChannel):
                        self.channels[module] = plugin_obj
                        if module not in self.channel_names:  # skip (glade) built-in channels
                            self.channel_names.append(module)
                    # other plugin types
                    else:
                        self.features[module] = plugin_obj
                    
                except Exception as e:
                    __print__(dbg.INIT, "load_plugin_channels: error initializing:", module, ", exception:")
                    import traceback
                    traceback.print_exc()

            # default plugins
            conf.add_plugin_defaults(self.channels["bookmarks"].config, "bookmarks")


        # store window/widget states (sizes, selections, etc.)
        def app_state(self, widget):
            # gtk widget states
            widgetnames = ["win_streamtuner2", "toolbar", "notebook_channels", ] \
                        + [id+"_list" for id in self.channel_names] + [id+"_cat" for id in self.channel_names]
            conf.save("window", mygtk.app_state(wTree=self, widgetnames=widgetnames), nice=1)
            # object vars
            channelopts = {} #dict([(id, {"current":self.channels[id].current}) for id in self.channel_names])
            for id in self.channels.keys():
                if (self.channels[id]):
                    channelopts[id] = {"current":self.channels[id].current}
            conf.save("state", channelopts, nice=1)


        # apply gtkrc stylesheet
        def load_theme(self):
            if conf.get("theme"):
                for dir in (conf.dir, conf.share, "/usr/share"):
                    f = dir + "/themes/" + conf.theme + "/gtk-2.0/gtkrc"
                    if os.path.exists(f):
                        gtk.rc_parse(f)
                pass


        # end application and gtk+ main loop
        def gtk_main_quit(self, widget, *x):
            if conf.auto_save_appstate:
                try:  # doesn't work with gtk3 yet (probably just hooking at the wrong time)
                    self.app_state(widget)
                except:
                    None
            gtk.main_quit()






                




# auxiliary window: about dialog
class AboutStreamtuner2:
        # about us
        def __init__(self):
            a = gtk.AboutDialog()
            a.set_version(__version__)
            a.set_name("streamtuner2")
            a.set_license("Public Domain\n\nNo Strings Attached.\nUnrestricted distribution,\nmodification, use.")
            a.set_authors(["Mario Salzer <http://mario.include-once.org/>\n\nConcept based on streamtuner 0."+"99."+"99 from\nJean-Yves Lefort, of which some code remains\nin the Google stations plugin.\n<http://www.nongnu.org/streamtuner/>\n\nMyOggRadio plugin based on cooperation\nwith Christian Ehm. <http://ehm-edv.de/>"])
            a.set_website("http://milki.include-once.org/streamtuner2/")
            a.connect("response", lambda a, ok: ( a.hide(), a.destroy() ) )
            a.show()
            

            
# right click in streams/stations TreeView
def station_context_menu(treeview, event):
            # right-click ?
            if event.button >= 3:
                path = treeview.get_path_at_pos(int(event.x), int(event.y))[0]
                treeview.grab_focus()
                treeview.set_cursor(path, None, False)
                main.streamactions.popup(
                      parent_menu_shell=None, parent_menu_item=None, func=None,
                      button=event.button, activate_time=event.time,
                      data=None
                )
                return None
            # we need to pass on to normal left-button signal handler
            else:
                return False
# this works better as callback function than as class - because of False/Object result for event trigger




# encapsulates references to gtk objects AND properties in main window
class auxiliary_window(object):
        def __getattr__(self, name):
            if name in main.__dict__:
                return main.__dict__[name]
            elif name in StreamTunerTwo.__dict__:
                return StreamTunerTwo.__dict__[name]
            else:
                return main.get_widget(name)
""" allows to use self. and main. almost interchangably """



# aux win: search dialog (keeps search text in self.q)
# and also: quick search textbox (uses main.q instead)
class search (auxiliary_window):

        # either current channel, or last channel (avoid searching in bookmarks)
        current = None

        # show search dialog   
        def menu_search(self, w):
            self.search_dialog.show();
            if not self.current or main.current_channel != "bookmarks":
                self.current = main.current_channel
                self.search_dialog_current.set_label("just %s" % main.channels[self.current].title)


        # hide dialog box again
        def cancel(self, *args):
            self.search_dialog.hide()
            return True  # stop any other gtk handlers
            

        # prepare variables
        def prepare_search(self):
            main.status("Searching... Stand back.")
            self.cancel()
            self.q = self.search_full.get_text().lower()
            if self.search_dialog_all.get_active():
                self.targets = main.channels.keys()
            else:
                self.targets = [self.current]
            main.bookmarks.streams["search"] = []
            
        # perform search
        def cache_search(self, *w):
            self.prepare_search()
            entries = []
            # which fields?
            fields = ["title", "playing", "homepage"]
            for i,cn in enumerate([main.channels[c] for c in self.targets]):
                if cn.streams:  # skip disabled plugins
                    # categories
                    for cat in cn.streams.keys():
                        # stations
                        for row in cn.streams[cat]:
                            # assemble text fields to compare
                            text = " ".join([row.get(f, " ") for f in fields])
                            if text.lower().find(self.q) >= 0:
                                row = copy(row)
                                row["genre"] = c + " " + row.get("genre", "")
                                entries.append(row)
            self.show_results(entries)

        # display "search" in "bookmarks"
        def show_results(self, entries):
            main.status(1.0)
            main.channel_switch(None, "bookmarks", 0)
            main.bookmarks.set_category("search")
            # insert data and show
            main.channels["bookmarks"].streams["search"] = entries   # we have to set it here, else .currentcat() might reset it 
            main.bookmarks.load("search")
            
            
        # live search on directory server homepages
        def server_search(self, w):
            self.prepare_search()
            entries = []
            for i,cn in enumerate([main.channels[c] for c in self.targets]):
                if cn.has_search:  # "search" in cn.update_streams.func_code.co_varnames:
                    __print__(dbg.PROC, "has_search:", cn.module)
                    try:
                        add = cn.update_streams(cat=None, search=self.q)
                        for row in add:
                            row["genre"] = cn.title + " " + row.get("genre", "")
                        entries += add
                    except:
                        continue
                #main.status(main, 1.0 * i / 15)
            self.show_results(entries)


        # search text edited in text entry box
        def quicksearch_set(self, w, *eat, **up):
            
            # keep query string
            main.q = self.search_quick.get_text().lower()

            # get streams
            c = main.channel()
            rows = c.stations()
            col = c.rowmap.index("search_col") # this is the gtk.ListStore index # which contains the highlighting color

            # callback to compare (+highlight) rows
            m = c.gtk_list.get_model()
            m.foreach(self.quicksearch_treestore, (rows, main.q, col, col+1))
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



search = search()
# instantiates itself




# aux win: stream data editing dialog
class streamedit (auxiliary_window):


        # show stream data editing dialog
        def open(self, mw):
            config_dialog.load_config(main.row(), "streamedit_")
            self.win_streamedit.show()


        # copy widget contents to stream
        def save(self, w):
            config_dialog.save_config(main.row(), "streamedit_")
            main.channel().save()
            self.cancel(w)

            
        # add a new list entry, update window
        def new(self, w):
            s = main.channel().stations()
            s.append({"title":"new", "url":"", "format":"audio/mpeg", "genre":"", "listeners":1});
            main.channel().switch() # update display
            main.channel().gtk_list.get_selection().select_path(str(len(s)-1)); # set cursor to last row
            self.open(w)


        # hide window
        def cancel(self, *w):
            self.win_streamedit.hide()
            return True

streamedit = streamedit()
# instantiates itself





# aux win: settings UI
class config_dialog (auxiliary_window):


        # Display win_config, pre-fill text fields from global conf. object
        def open(self, widget):
            if self.first_open:
                self.add_plugins()
                self.combobox_theme()
                self.first_open = 0
                self.win_config.resize(565, 625)
            self.load_config(conf.__dict__, "config_")
            self.load_config(conf.plugins, "config_plugins_")
            [callback() for callback in self.hooks["config_load"]]
            self.win_config.show()
        first_open = 1

        # Hide window
        def hide(self, *args):
            self.win_config.hide()
            return True

        
        # Load values from conf. store into gtk widgets
        def load_config(self, config, prefix="config_"):
            for key,val in config.items():
                w = main.get_widget(prefix + key)
                if w:
                    # input field
                    if type(w) is gtk.Entry:
                        w.set_text(str(val))
                    # checkmark
                    elif type(w) is gtk.CheckButton:
                        w.set_active(bool(val))
                    # dropdown
                    elif type(w) is ComboBoxText:
                        w.set_default(val)
                    # list
                    elif type(w) is gtk.ListStore:
                        w.clear()
                        for k,v in val.items():
                            w.append([k, v, True])
                        w.append(["", "", True])
                __print__(dbg.CONF, "config load", prefix+key, val, type(w))

        # Store gtk widget valus back into conf. dict
        def save_config(self, config, prefix="config_", save=0):
            for key,val in config.items():
                w = main.get_widget(prefix + key)
                if w:
                    # text
                    if type(w) is gtk.Entry:
                        config[key] = w.get_text()
                    # pre-defined text
                    elif type(w) is ComboBoxText:
                        config[key] = w.get_active_text()
                    # boolean
                    elif type(w) is gtk.CheckButton:
                        config[key] = w.get_active()
                    # dict
                    elif type(w) is gtk.ListStore:
                        config[key] = {}
                        for row in w:
                            if row[0] and row[1]:
                                config[key][row[0]] = row[1]
                __print__(dbg.CONF, "config save", prefix+key, val)

        
        # Generic Gtk callback to update ListStore when entries get edited
        def list_edit(self, liststore, path, column, new_text):
            liststore[path][column] = new_text
            # The signal_connect() dict actually prepares individual lambda functions
            # to bind the correct ListStore and column id.
            

        # list of Gtk themes in dropdown
        def combobox_theme(self):
            # find themes
            themedirs = (conf.share+"/themes", conf.dir+"/themes", "/usr/share/themes")
            themes = ["no theme"]
            [[themes.append(e) for e in os.listdir(dir)] for dir in themedirs if os.path.exists(dir)]
            __print__(dbg.STAT, themes)
            # add dropdown
            main.widgets["theme"] = ComboBoxText(themes)
            self.theme_cb_placeholder.pack_start(self.theme)
            self.theme_cb_placeholder.pack_end(mygtk.label(""))


        # retrieve currently selected value
        def apply_theme(self):
            conf.theme = self.theme.get_active_text()
            main.load_theme()


        # iterate over channel and feature plugins
        def add_plugins(self):
            for name,plugin in main.channels.iteritems():
                self.add_plg(name, plugin, plugin.meta)
            self.plugin_options.pack_start(mygtk.label("\n<b>Feature</b> plugins add categories, submenu entries, or other extensions.\n", 500, 1))
            for name,plugin in main.features.iteritems():
                self.add_plg(name, plugin, plugin.meta)

        # add configuration setting definitions from plugins
        def add_plg(self, name, c, meta):
            # add plugin load entry
            cb = gtk.CheckButton(name)
            cb.get_children()[0].set_markup("<b>%s</b> <i>(%s)</i> %s\n<small>%s</small>" % (meta["title"], meta["type"], meta.get("version", ""), meta["description"]))
            self.add_( "config_plugins_"+name, cb )

            # default values are already in conf[] dict (now done in conf.add_plugin_defaults)
            for opt in meta["config"]:
                color = opt.get("color", None)
                # display checkbox
                if opt["type"] == "boolean":
                    cb = gtk.CheckButton(opt["description"])
                    self.add_( "config_"+opt["name"], cb, color=color )
                # drop down list
                elif opt["type"] == "select":
                    cb = ComboBoxText(ComboBoxText.parse_options(opt["select"])) # custom mygtk widget
                    self.add_( "config_"+opt["name"], cb, opt["description"], color )
                # text entry
                else:
                    self.add_( "config_"+opt["name"], gtk.Entry(), opt["description"], color )

            # spacer 
            self.add_( "filler_pl_"+name, gtk.HSeparator() )


        # Put config widgets into config dialog notebook
        def add_(self, id, w, label=None, color=""):
            w.set_property("visible", True)
            main.widgets[id] = w
            if label:
                if type(w) is gtk.Entry:
                    w.set_width_chars(11)
                w = mygtk.hbox(w, mygtk.label(label))
            if color:
                w = mygtk.bg(w, color)
            self.plugin_options.pack_start(w)
        
        # save config
        def save(self, widget):
            self.save_config(conf.__dict__, "config_")
            self.save_config(conf.plugins, "config_plugins_")
            [callback() for callback in main.hooks["config_save"]]
            config_dialog.apply_theme()
            conf.save(nice=1)
            self.hide()
                  
config_dialog = config_dialog()
# instantiates itself





#-- run main                                ---------------------------------------------
if __name__ == "__main__":


    # graphical
    if len(sys.argv) < 2 or "--gtk3" in sys.argv:
    
        
        # prepare for threading in Gtk+ callbacks
        gobject.threads_init()
        gui_startup(1/100.0)
        
        # prepare main window
        main = StreamTunerTwo()
        
        # module coupling
        action.main = main      # action (play/record) module needs a reference to main window for gtk interaction and some URL/URI callbacks
        action = action.action  # shorter name
        ahttp.feedback = main.status  # http module gives status feedbacks too
        
        # first invocation
        if (conf.get("firstrun")):
            config_dialog.open(None)
            del conf.firstrun


        # run
        gui_startup(100/100.0)
        gtk.main()
        __print__(dbg.PROC, r"[31m gtk_main_quit [0m")
        
        
    # invoke command-line interface
    else:
        import cli
        cli.StreamTunerCLI()




#
#
#
#
