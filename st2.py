#!/usr/bin/env python
#
# encoding: UTF-8
# api: python
# type: application
# title: streamtuner2
# description: Directory browser for internet radio, audio and video streams
# version: 2.1.5
# state: beta
# author: Mario Salzer <mario@include-once.org>
# license: Public Domain
# url: http://freshcode.club/projects/streamtuner2
# config:  
#   { type: env, name: http_proxy, description: proxy for HTTP access }
#   { type: env, name: XDG_CONFIG_HOME, description: relocates user .config subdirectory }
# category: sound
# depends: pygtk | gi, threading, requests, pyquery, lxml
# id: streamtuner2
# pack: *.py, gtk*.xml, st2.py=/usr/bin/streamtuner2, channels/__init__.py, bundle/*.py,
#   streamtuner2.desktop=/usr/share/applications/, README=/usr/share/doc/streamtuner2/,
#   NEWS.gz=/usr/share/doc/streamtuner2/changelog.gz, help/streamtuner2.1=/usr/share/man/man1/,
#   help/*page=/usr/share/doc/streamtuner2/help/, help/img/*=/usr/share/doc/streamtuner2/help/img/,
#   streamtuner2.png, logo.png=/usr/share/pixmaps/streamtuner2.png,
# architecture: all
#
# Streamtuner2 is a GUI for browsing internet radio directories, music
# collections, and video services - grouped by genres or categories.
# It runs your preferred audio player, and streamripper for recording.
#
# It's an independent rewrite of streamtuner1. Being written in Python,
# can be more easily extended and fixed. The mix of JSON APIs, regex
# or PyQuery extraction makes list generation simpler and more robust.
#
# Primarily radio stations are displayed, some channels however are music
# collections. Commercial and sign-up services are not an objective.
#



# standard modules
import sys
import os
import re
from copy import copy
import inspect
import traceback
from threading import Thread

# add library path
sys.path.insert(0, "/usr/share/streamtuner2")   # pre-defined directory for modules
sys.path.insert(0, ".")   # development module path

# gtk modules
from uikit import pygtk, gtk, gobject, uikit, ui_xml, gui_startup, AboutStreamtuner2

# custom modules
from config import *   # initializes itself, so all conf.vars are available right away
import ahttp
import action
import logo
import favicon
import channels
import channels.bookmarks
import channels.configwin
import channels.streamedit
import channels.search



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
    meta = plugin_meta()

    # status variables
    channel_names = ["bookmarks"]    # order of channel notebook tabs
    current_channel = "bookmarks"    # currently selected channel name (as index in self.channels{})


    # constructor
    def __init__(self):
        
        # Load stylesheet, instantiate GtkBuilder in self, menu and logo hooks
        gui_startup(0/20.0), self.load_theme()
        gui_startup(1/20.0), gtk.Builder.__init__(self)
        gui_startup(1/20.0), gtk.Builder.add_from_string(self, ui_xml)
        gui_startup(3/20.0), self.extensionsCTM.set_submenu(self.extensions)  # duplicates Station>Extension menu into stream context menu
        self.img_logo.set_from_pixbuf(uikit.pixbuf(logo.png))

        # initialize built-in plugins
        self.channels = {
          "bookmarks": channels.bookmarks.bookmarks(parent=self),   # this the remaining built-in channel
        }
        # dialogs that are connected to main
        self.features = {
          "search": channels.search.search(self),
          "configwin": channels.configwin.configwin(self),
          "streamedit": channels.streamedit.streamedit(self),
        }
        gui_startup(4/20.0)
        # append other channel modules and plugins
        self.load_plugin_channels()


        # load application state (widget sizes, selections, etc.)
        try:
            winlayout = conf.load("window")
            if (winlayout):
                uikit.app_restore(self, winlayout)
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
        gui_startup(19.75/20.0)
        self.connect_signals(dict({
            "gtk_main_quit" : self.gtk_main_quit,                # close window
            # treeviews / notebook
            "on_stream_row_activated" : self.on_play_clicked,    # double click in a streams list
            "on_category_clicked": self.on_category_clicked,     # new selection in category list
            "on_notebook_channels_switch_page": self.channel_switch,   # channel notebook tab changed
            "station_context_menu": lambda tv,ev: self.station_context_menu(tv,ev),
            # toolbar
            "on_play_clicked" : self.on_play_clicked,
            "on_record_clicked": self.on_record_clicked,
            "on_homepage_stream_clicked": self.on_homepage_stream_clicked,
            "on_reload_clicked": self.on_reload_clicked,
            "on_stop_clicked": self.on_stop_clicked, #@TODO: button is long gone
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
            "menu_properties": self.configwin.open,
            "config_cancel": self.configwin.hide,
            "config_save": self.configwin.save,
            "config_play_list_edit_col0": lambda w,path,txt: (self.configwin.list_edit(self.config_play, path, 0, txt)),
            "config_play_list_edit_col1": lambda w,path,txt: (self.configwin.list_edit(self.config_play, path, 1, txt)),
            "config_record_list_edit_col0": lambda w,path,txt: (self.configwin.list_edit(self.config_record, path, 0, txt)),
            "config_record_list_edit_col1": lambda w,path,txt: (self.configwin.list_edit(self.config_record, path, 1, txt)),
            # else
            "update_categories": self.update_categories,
            "update_favicons": self.update_favicons,
            "app_state": self.app_state,
            "bookmark": self.bookmark,
            "save_as": self.save_as,
            "menu_about": lambda w: AboutStreamtuner2(self),
            "menu_help": action.action.help,
            "menu_onlineforum": lambda w: action.browser("http://sourceforge.net/projects/streamtuner2/forums/forum/1173108"),
            "menu_fossilwiki": lambda w: action.browser("http://fossil.include-once.org/streamtuner2/"),
            "menu_projhomepage": lambda w: action.browser("http://milki.include-once.org/streamtuner2/"),
           # "menu_bugreport": lambda w: BugReport(),
            "menu_copy": self.menu_copy,
            "delete_entry": self.delete_entry,
            # search dialog
            "quicksearch_set": self.search.quicksearch_set,
            "search_open": self.search.menu_search,
            "search_go": self.search.cache_search,
            "search_srv": self.search.server_search,
            "search_cancel": self.search.cancel,
            "true": lambda w,*args: True,
            # win_streamedit
            "streamedit_open": self.streamedit.open,
            "streamedit_save": self.streamedit.save,
            "streamedit_new": self.streamedit.new,
            "streamedit_cancel": self.streamedit.cancel,
        }, **self.add_signals))
        
        # actually display main window
        self.win_streamtuner2.show()
        gui_startup(1.0)
        

    #-- Shortcut for glade.get_widget()
    # Allows access to widgets as direct attributes instead of using .get_widget()
    # Also looks in self.channels[] for the named channel plugins
    def __getattr__(self, name):
        if (name in self.channels):
            return self.channels[name]     # like self.shoutcast
        elif (name in self.features):
            return self.features[name]     # like self.configwin
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
        __print__(dbg.ERR, "STOP is no longer available")
        #while self.working:
            #thread = self.working.pop()
            #thread.stop()

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
        fn = uikit.save_file("Save Stream", None, default_fn, [(".m3u","*m3u"),(".pls","*pls"),(".xspf","*xspf"),(".smil","*smil"),(".asx","*asx"),("all files","*")])
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
            uikit.do(lambda:self.statusbar.pop(sbar_cid))
        # progressbar
        if (type(text)==float):
            if (text >= 999.0/1000):  # completed
                uikit.do(lambda:self.progress.hide())
            else:  # show percentage
                uikit.do(lambda:self.progress.show() or self.progress.set_fraction(text))
                if (text <= 0):  # unknown state
                    uikit.do(lambda:self.progress.pulse())
        # add text
        elif (type(text)==str):
            sbar_msg.append(1)
            uikit.do(lambda:self.statusbar.push(sbar_cid, text))
        pass


    # load plugins from /usr/share/streamtuner2/channels/
    def load_plugin_channels(self):

        # initialize plugin modules (pre-ordered)
        ls = channels.module_list()
        for module in ls:
            gui_startup(4/20.0 + 13.5/20.0 * float(ls.index(module))/len(ls), "loading module "+module)
                            
            # skip module if disabled
            if conf.plugins.get(module, 1) == False:
                __print__(dbg.STAT, "disabled plugin:", module)
                continue
            # or if it's a built-in (already imported)
            elif module in self.features or module in self.channels:
                continue
            
            # load plugin
            try:
                plugin = __import__("channels."+module, globals(), None, [""])
                #print [name for name,c in inspect.getmembers(plugin) if inspect.isclass(c)]
                plugin_class = plugin.__dict__[module]
                plugin_obj = plugin_class(parent=self)
                
                # load .config settings from plugin
                conf.add_plugin_defaults(plugin_obj.meta["config"], module)

                # add and initialize channel
                if issubclass(plugin_class, channels.GenericChannel):
                    self.channels[module] = plugin_obj
                    if module not in self.channel_names:  # skip (glade) built-in channels
                        self.channel_names.append(module)
                # other plugin types
                else:
                    self.features[module] = plugin_obj
                
            except Exception as e:
                __print__(dbg.INIT, "load_plugin_channels: error initializing:", module, ", exception:")
                traceback.print_exc()

        # default plugins
        conf.add_plugin_defaults(self.channels["bookmarks"].config, "bookmarks")


    # store window/widget states (sizes, selections, etc.)
    def app_state(self, widget):
        # gtk widget states
        widgetnames = ["win_streamtuner2", "toolbar", "notebook_channels", ] \
                    + [id+"_list" for id in self.channel_names] \
                    + [id+"_cat" for id in self.channel_names]
        conf.save("window", uikit.app_state(wTree=self, widgetnames=widgetnames), nice=1)
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


    # Right clicking a stream/station in the treeview to make context menu pop out.
    def station_context_menu(self, treeview, event):
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
        # else pass on to normal left-button signal handler
        else:
            return False






#-- run main
if __name__ == "__main__":

    # graphical
    if len(sys.argv) < 2 or "--gtk3" in sys.argv:

        # prepare for threading in Gtk+ callbacks
        gobject.threads_init()

        # prepare main window
        main = StreamTunerTwo()

        # module coupling
        action.main = main      # action (play/record) module needs a reference to main window for gtk interaction and some URL/URI callbacks
        action = action.action  # shorter name
        ahttp.feedback = main.status  # http module gives status feedbacks too

        # first invocation
        if (conf.get("firstrun")):
            main.configwin.open(None)
            del conf.firstrun

        # run
        gtk.main()
        __print__(dbg.PROC, r"[31m gtk_main_quit [0m")
        
    # invoke command-line interface
    else:
        import cli
        cli.StreamTunerCLI()


