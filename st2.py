#!/usr/bin/env python
#
# encoding: UTF-8
# api: python
# type: application
# title: streamtuner2
# description: Directory browser for internet radio, audio and video streams
# version: 2.1.7
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
# pack: *.py, gtk3.xml.gz, bin, channels/__init__.py, bundle/*.py, CREDITS, help/index.page,
#   streamtuner2.desktop, README, help/streamtuner2.1=/usr/share/man/man1/,
#   NEWS=/usr/share/doc/streamtuner2/, icon.png=/usr/share/pixmaps/streamtuner2.png
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


# standard modules
import sys
import os
import re
from copy import copy
import inspect
import traceback
from threading import Thread

# add library path (either global setup, or pyzip basename)
if not os.path.dirname(__file__) in sys.path:
    sys.path.insert(0, os.path.dirname(__file__))

# initializes itself, so all conf.vars are available right away
from config import *

# gtk modules
from uikit import pygtk, gtk, gobject, uikit, ui_xml, gui_startup, AboutStreamtuner2

# custom modules
import ahttp
import action
import logo
import favicon
import channels
import channels.bookmarks
import channels.configwin
import channels.streamedit
import channels.search



# This represents the main window, dispatches Gtk events,
# and shares most application behaviour with the channel modules.
class StreamTunerTwo(gtk.Builder):

    # object containers
    widgets = {}     # non-glade widgets (any manually instantiated ones)
    channels = {}    # channel modules
    features = {}    # non-channel plugins
    working = []     # threads
    hooks = {
        "play": [favicon.download_playing],  # observers queue here
        "record": [],
        "init": [],
        "quit": [action.cleanup_tmp_files],
        "config_load": [],
        "config_save": [],
    }
    meta = plugin_meta()


    # status variables
    current_channel = "bookmarks"    # currently selected channel name (as index in self.channels{})

    # constructor
    def __init__(self):
        
        # Load stylesheet, instantiate GtkBuilder in self, menu and logo hooks
        gui_startup(1/20.0), gtk.Builder.__init__(self)
        gui_startup(1/20.0), gtk.Builder.add_from_string(self, ui_xml)
        gui_startup(3/20.0), self.img_logo.set_from_pixbuf(uikit.pixbuf(logo.png, decode=1, fmt="png"))

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

        # early module coupling
        action.main = self            # action (play/record) module needs a reference to main window for gtk interaction and some URL/URI callbacks
        ahttp.feedback = self.status  # http module gives status feedbacks too
        
        # load plugins
        self.load_plugin_channels()
        # restore app/widget states
        self.init_app_state()
        # and late plugin initializations
        [callback(self) for callback in self.hooks["init"]]

        # display current open channel/notebook tab
        gui_startup(18/20.0)
        self.current_channel = self.current_channel_gtk()
        try: self.channel().first_show()
        except: log.INIT("main.__init__: current_channel.first_show() initialization error")

  
        # bind gtk/glade event names to functions
        gui_startup(19.75/20.0)
        self.connect_signals({
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
            "app_state": self.save_app_state,
            "bookmark": self.bookmark,
            "save_as": self.save_as,
            "menu_about": lambda w: AboutStreamtuner2(self),
            "menu_help": action.help,
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
            "search_srv": lambda *w: self.thread(lambda: self.search.server_search(None)),
            "search_cancel": self.search.cancel,
            "true": lambda w,*args: True,
            # win_streamedit
            "streamedit_open": self.streamedit.open,
            "streamedit_save": self.streamedit.save,
            "streamedit_new": self.streamedit.new,
            "streamedit_cancel": self.streamedit.cancel,
        })
        
        # actually display main window
        self.update_title()
        self.win_streamtuner2.show_all()
        gui_startup(100.0)


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

            
    # Returns the currently selected directory/channel object (remembered position)
    def channel(self):
        return self.channels[self.current_channel]

    # List of module titles for channel tabs
    @property
    def channel_names(self):
        n = self.notebook_channels
        return [n.get_menu_label_text(n.get_nth_page(i)) for i in range(0, n.get_n_pages())]

    # Returns the currently selected directory/channel object (from gtk)
    def current_channel_gtk(self):
        return self.channel_names[self.notebook_channels.get_current_page()]
    
        
    # Notebook tab has been clicked (receives numeric page_num), but *NOT* yet changed (visually).
    def channel_switch(self, notebook, page, page_num=0, *args):
        self.current_channel = notebook.get_menu_label_text(notebook.get_nth_page(page_num))
        log.UI("main.channel_switch() :=", self.current_channel)
        self.update_title()
        # if first selected, load current category
        # (run in thread, to make it look speedy on first startup)
        self.thread( 
        self.channel().first_show
        )

    # Invoked from the menu instead, uses module name instead of numeric tab id
    def channel_switch_by_name(self, name):
        self.notebook_channels.set_current_page(self.channel_names.index(name))

    # Mirror selected channel tab into main window title
    def update_title(self):
        self.win_streamtuner2.set_title("Streamtuner2 - %s" % self.channel().meta.get("title"))


    # Channel: row{} dict for current station
    def row(self):
        return self.channel().row()
        
    # Channel: fetch single varname from station row{} dict
    def selected(self, name="url"):
        return self.row().get(name)


            
    # Play button
    def on_play_clicked(self, widget, event=None, *args):
        self.status("Starting player...")
        row = self.channel().play()
        self.status("")
        [callback(row) for callback in self.hooks["play"]]

    # Recording: invoke streamripper for current stream URL
    def on_record_clicked(self, widget):
        self.status("Recording station...")
        row = self.channel().record()
        [callback(row) for callback in self.hooks["record"]]

    # Open stream homepage in web browser
    def on_homepage_stream_clicked(self, widget):
        url = self.selected("homepage")
        if url and len(url): action.browser(url)
        else: self.status("No homepage URL present.")

    # Browse to channel homepage (double click on notebook tab)
    def on_homepage_channel_clicked(self, widget, event=2):
        if event == 2 or event.type == gtk.gdk._2BUTTON_PRESS:
            log.UI("dblclick")
            url = self.channel().meta.get("url", "https://duckduckgo.com/?q=" + self.channel().module)
            action.browser(url)

    # Reload stream list in current channel-category
    def on_reload_clicked(self, widget=None, reload=1):
        log.UI("on_reload_clicked()", "reload=", reload, "current_channel=", self.current_channel, "c=", self.channels[self.current_channel], "cat=", self.channel().current)
        category = self.channel().current
        self.thread(
                       #@TODO: should get a wrapper, for HTTP errors, and optionalize bookamrks
            lambda: (  self.channel().load(category,reload), reload and self.bookmarks.heuristic_update(self.current_channel,category)  )
        )

    # Thread a function, add to worker pool (for utilizing stop button)
    def thread(self, target, *args):
        thread = Thread(target=target, args=args)
        thread.start()
        self.working.append(thread)


    # Click in category list
    def on_category_clicked(self, widget, event, *more):
        category = self.channel().currentcat()
        log.UI("on_category_clicked", category, self.current_channel)
        self.on_reload_clicked(None, reload=0)
        pass

    # Add current selection to bookmark store
    def bookmark(self, widget):
        self.bookmarks.add(self.row())
        self.channel().row_icon(gtk.STOCK_ABOUT)
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
        fn = uikit.save_file("Save Stream", None, default_fn, [(".m3u","*m3u"),(".pls","*pls"),(".xspf","*xspf"),(".jspf","*jspf"),(".smil","*smil"),(".asx","*asx"),("all files","*")])
        if fn:
            source = row.get("listformat", self.channel().listformat)
            dest = (re.findall("\.(m3u|pls|xspf|jspf|json|smil|asx|wpl)8?$", fn) or ["pls"])[0]
            action.save_playlist(source=source, multiply=True).file(rows=[row], fn=fn, dest=dest)
        pass

    # Save current stream URL into clipboard
    def menu_copy(self, w):
        gtk.clipboard_get().set_text(self.selected("url"))

    # Remove a stream entry
    def delete_entry(self, w):
        cn = self.channel()
        n = cn.rowno()
        del cn.stations()[ n ]
        cn.switch()
        cn.save()

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
            uikit.do(self.statusbar.pop, sbar_cid, immediate=1)
        # progressbar
        if (type(text)==float):
            if text >= 0.999 or text < 0.0:  # completed
                uikit.do(self.progress.hide)
            else:  # show percentage
                uikit.do(self.progress.show, immediate=1)
                uikit.do(self.progress.set_fraction, text, immediate=1)
                if (text <= 0):  # unknown state
                    uikit.do(self.progress.pulse, immediate=1)
        # add text
        elif (type(text)==str):
            sbar_msg.append(1)
            uikit.do(self.statusbar.push, sbar_cid, text, immediate=1)
        pass


    # load plugins from /usr/share/streamtuner2/channels/
    def load_plugin_channels(self):

        # initialize plugin modules (pre-ordered)
        ls = module_list()
        for name in ls:
            gui_startup(4/20.0 + 13.5/20.0 * float(ls.index(name))/len(ls), "loading module "+name)

            # load defaults on first startup
            if not name in conf.plugins:
                conf.add_plugin_defaults(plugin_meta(module=name), name)
            
            # skip module if disabled
            if conf.plugins.get(name, 1) == False:
                log.STAT("disabled plugin:", name)
                continue
            # or if it's a built-in (already imported)
            elif name in self.features or name in self.channels:
                continue
            
            # load plugin
            try:
                plugin = __import__("channels."+name, globals(), None, [""])
                #print [name for name,c in inspect.getmembers(plugin) if inspect.isclass(c)]
                plugin_class = plugin.__dict__[name]
                plugin_obj = plugin_class(parent=self)

                # add to .channels{}
                if issubclass(plugin_class, channels.GenericChannel):
                    self.channels[name] = plugin_obj
                # or .features{} for other plugin types
                else:
                    self.features[name] = plugin_obj
                
            except Exception as e:
                log.INIT("load_plugin_channels: error initializing:", name, ", exception:")
                traceback.print_exc()

    # load application state (widget sizes, selections, etc.)
    def init_app_state(self):

        winlayout = conf.load("window")
        if (winlayout):
            try: uikit.app_restore(self, winlayout)
            except Exception as e: log.APPRESTORE(e) # may fail for disabled/reordered plugin channels

        winstate = conf.load("state")
        if (winstate):
            for id,prev in winstate.items():
                try: self.channels[id].current = prev["current"]
                except Exception as e: log.APPSTATE(e)

    # store window/widget states (sizes, selections, etc.)
    def save_app_state(self, widget):
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


    # end application and gtk+ main loop
    def gtk_main_quit(self, widget, *x):
        if conf.auto_save_appstate:
            try:  # doesn't work with gtk3 yet (probably just hooking at the wrong time)
                self.save_app_state(widget)
            except Exception as e:
                log.ERR(e)
        gtk.main_quit()


    # Right clicking a stream/station in the treeview to make context menu pop out.
    def station_context_menu(self, treeview, event):
        if treeview and event and event.button >= 3:
            path = treeview.get_path_at_pos(int(event.x), int(event.y))
            if not path:
                return False
            else:
                path = path[0]
            treeview.grab_focus()
            treeview.set_cursor(path, None, False)
            self.streamactions.popup(
                  parent_menu_shell=None, parent_menu_item=None, func=None,
                  button=event.button, activate_time=event.time,
                  data=None
            )
            return None
        # else pass on to normal left-button signal handler
        else:
            return False





# startup procedure
def main():

    # graphical
    if not len(conf.args.action):

        # prepare for threading in Gtk+ callbacks
        gobject.threads_init()

        # prepare main window
        main = StreamTunerTwo()

        # first invocation
        if (conf.get("firstrun")):
            main.configwin.open(None)
            del conf.firstrun

        # run
        gtk.main()
        [callback() for callback in main.hooks["quit"]]
        log.PROC(r"[31m gtk_main_quit [0m")
        
    # invoke command-line interface
    else:
        import cli
        cli.StreamTunerCLI(conf.args.action)

# run
if __name__ == "__main__":
    main()

