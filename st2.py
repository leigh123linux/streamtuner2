#!/usr/bin/env python
# encoding: UTF-8
# api: python
# type: application
# title: streamtuner2
# description: Directory browser for internet radio, audio and video streams
# version: 2.2.0-rc4
# state: stable
# author: Mario Salzer <mario@include-once.org>
# license: Public Domain
# url: http://freshcode.club/projects/streamtuner2
# config:  
#   { type: env, name: HTTP_PROXY, description: proxy for HTTP access }
#   { type: env, name: XDG_CONFIG_HOME, description: relocates user .config subdirectory }
# category: sound
# depends: pygtk | gi, threading, requests, pyquery, lxml
# alias: streamtuner2, main
# id: st2
# pack: *.py, gtk3.xml.gz, bin, channels/__init__.py, bundle/*.py, CREDITS, help/index.page,
#   streamtuner2.desktop, README, help/streamtuner2.1=/usr/share/man/man1/,
#   NEWS=/usr/share/doc/streamtuner2/, icon.png=/usr/share/pixmaps/streamtuner2.png
# architecture: all
#
# Streamtuner2 is a GUI for browsing internet radio directories,
# music collections, and video services - grouped by genres or
# categories. It runs your preferred audio player or streamripper
# for recording.
#
# It's an independent rewrite of streamtuner1. Being written in
# Python, can be more easily extended and fixed. The mix of
# JSON APIs, regex or PyQuery extraction simplifies collecting
# station lists.
#
# Primarily radio stations are displayed, some channels however
# are music collections. Commercial and sign-up services are not
# an objective.


# standard modules
import sys
import os
import re
from copy import copy
import inspect
import traceback
from threading import Thread
import time
from compat2and3 import *

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
    #working = []     # threads
    hooks = {
        "play": [],  # observers queue here
        "record": [],
        "switch": [],
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
        gui_startup(3/20.0), self.logo_scale(1.0)

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
        try:
            self.channel().first_show()
        except Exception as e:
            log.INIT("main.__init__: current_channel.first_show() initialization error:", e)

  
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
            "menu_toolbar_size_small": lambda w: (self.toolbar.set_icon_size(gtk.ICON_SIZE_SMALL_TOOLBAR), self.logo_scale(0.40)),
            "menu_toolbar_size_medium": lambda w: (self.toolbar.set_icon_size(gtk.ICON_SIZE_DND), self.logo_scale(0.75)),
            "menu_toolbar_size_large": lambda w: (self.toolbar.set_icon_size(gtk.ICON_SIZE_DIALOG), self.logo_scale(1.0)),
            "menu_notebook_pos_top": lambda w: self.notebook_channels.set_tab_pos(2),
            "menu_notebook_pos_left": lambda w: self.notebook_channels.set_tab_pos(0),
            "menu_notebook_pos_right": lambda w: self.notebook_channels.set_tab_pos(1),
            "menu_notebook_pos_bottom": lambda w: self.notebook_channels.set_tab_pos(3),
            # win_config
            "menu_properties": self.configwin.open,
            "config_cancel": self.configwin.hide,
            "config_save": self.configwin.save,
            "config_play_list_edit_col0": (uikit.liststore_edit, (self.config_play, 0)),
            "config_play_list_edit_col1": (uikit.liststore_edit, (self.config_play, 1)),
            "config_record_list_edit_col0": (uikit.liststore_edit, (self.config_record, 0)),
            "config_record_list_edit_col1": (uikit.liststore_edit, (self.config_record, 1)),
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
        if conf.window_title:
            self.update_title()
        self.win_streamtuner2.show_all()
        gui_startup(100.0)


    #-- Shortcut for glade.get_widget()
    # Allows access to widgets as direct attributes instead of using .get_widget()
    # Also looks in self.channels[] for the named channel plugins
    def __getattr__(self, name):
        if name in self.channels:
            return self.channels[name]     # like self.shoutcast
        elif name in self.features:
            return self.features[name]     # like self.configwin
        else:
            return self.get_object(name)   # or gives an error if neither exists

    # Custom-named widgets are available from .widgets{} not via .get_widget()
    def get_widget(self, name):
        if name in self.widgets:
            return self.widgets[name]
        else:
            return gtk.Builder.get_object(self, name)


    # Run function in separate thread.
    # Often used in conjunction with uikit.do() for Gtk interactions.
    def thread(self, target, *args, **kwargs):
        if conf.nothreads:
            return target(*args, **kwargs)
        thread = Thread(target=target, args=args, kwargs=kwargs)
        thread.start()

            
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
        # update window title, call plugin (e.g. channel link in toolbar)
        if conf.window_title:
            uikit.do(self.update_title)
        # if first selected, load current category
        # (run in thread, to make it look speedy on first startup)
        self.thread(self.channel().first_show)

    # Invoked from the menu instead, uses module name instead of numeric tab id
    def channel_switch_by_name(self, name):
        self.notebook_channels.set_current_page(self.channel_names.index(name))

    # Mirror selected channel tab into main window title
    def update_title(self, *x, **y):
        meta = self.channel().meta
        self.win_streamtuner2.set_title("Streamtuner2 - %s" % meta.get("title"))
        [cb(meta) for cb in self.hooks["switch"]]


    # Channel: row{} dict for current station
    def row(self):
        return self.channel().row()
        
    # Channel: fetch single varname from station row{} dict
    def selected(self, name="url"):
        return self.row().get(name)


            
    # Play button
    def on_play_clicked(self, widget, event=None, *args):
        self.status("Starting player...", timeout=1.25)
        channel = self.channel()
        row = channel.play()
        #self.status("")
        [callback(row, channel=channel) for callback in self.hooks["play"]]

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

    # Browse to channel homepage (@BROKEN: double click on notebook tab)
    def on_homepage_channel_clicked(self, widget, event=2):
        if event == 2 or event.type == gtk.gdk._2BUTTON_PRESS:
            log.UI("dblclick")
            url = self.channel().meta.get("url", "https://duckduckgo.com/?q=" + self.channel().module)
            action.browser(url)

    # Reload stream list in current channel-category
    def on_reload_clicked(self, widget=None, reload=1):
        log.UI("on_reload_clicked()", "reload=", reload, "current_channel=", self.current_channel, "c=", self.channels[self.current_channel], "cat=", self.channel().current)
        self.thread(self._on_reload, self.channel(), reload)
    def _on_reload(self, channel, reload):
        self.channel().load(channel.current, force=reload)
        if reload:
            try: self.bookmarks.heuristic_update(self.current_channel, channel.category)
            except: pass

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
        self.thread(self.channel().reload_categories)

    # Menu invocation: refresh favicons for all stations in current streams category
    def update_favicons(self, widget):
        if "favicon" in self.features:
            ch = self.channel()
            self.features["favicon"].update_all(entries=ch.stations(), channel=ch)

    # Save stream to file (.m3u)
    def save_as(self, widget):
        row = self.row()
        default_fn = row["title"] + ".m3u"
        fn = uikit.save_file("Save Stream", None, default_fn, [(".m3u","*m3u"),(".pls","*pls"),(".xspf","*xspf"),(".jspf","*jspf"),(".smil","*smil"),(".asx","*asx"),("all files","*")])
        if fn:
            source = row.get("listformat", self.channel().listformat)
            dest = (re.findall("\.(m3u|pls|xspf|jspf|json|smil|asx|wpl|qtl)8?$", fn) or ["pls"])[0]
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

    # Change notebook channel tabs between TOP and LEFT position
    def switch_notebook_tabs_position(self, w, pos):
        self.notebook_channels.set_tab_pos(pos);




    # Shortcut to statusbar and progressbar (receives either a string, or a float).
    def status(self, text=None, timeout=3, markup=False):
        self.status_last = time.time() + timeout
        gobject.timeout_add(int(timeout*1000), self.status_clear)
        #log.UI("progressbar := %s" %text)
        # progressbar
        if isinstance(text, (int, float)):
            if (text <= 0):  # unknown state
                uikit.do(self.progress.pulse, immediate=1)
            elif text >= 0.999 or text < 0.0:  # completed
                uikit.do(self.progress.hide)
            else:  # show percentage
                uikit.do(self.progress.show, immediate=1)
                uikit.do(self.progress.set_fraction, text, immediate=1)
        # add text
        elif isinstance(text, (str, unicode)):
            uikit.do(self.statusbar.set_markup if markup else self.statusbar.set_text, text)
        # clean up
        else:
            self.status_clear(anyway=True)

    # Clean up after 3 seconds
    def status_clear(self, anyway=False):
        if anyway or time.time() >= self.status_last:
            #log.UI("progressbar.hide()")
            self.statusbar.set_text("")
            self.progress.hide()
            return False
        else:
            return True


    # load plugins from /usr/share/streamtuner2/channels/
    def load_plugin_channels(self):

        # initialize plugin modules (pre-ordered)
        ls = module_list()
        for name in ls:
            gui_startup(4/20.0 + 13.5/20.0 * float(ls.index(name))/len(ls), "loading module "+name)

            # load defaults - on first startup - or with -D in any case
            if not name in conf.plugins or conf.debug:
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


    # Redraw logo        
    def logo_scale(self, r=1.0, map=None):
        pix = uikit.pixbuf(logo.png, decode=1, fmt="png")
        if map and map in (2,5,0):  # gtk.ICON_SIZE_SMALL_TOOLBAR / _DND / _DIALOG
            r = { 2: 0.45, 5: 0.75, 0: 1.0 }[map]
        if r != 1.0:
            pix = pix.scale_simple(int(321*r), int(115*r), gtk.gdk.INTERP_BILINEAR)
        self.img_logo.set_from_pixbuf(pix)

    # load application state (widget sizes, selections, etc.)
    def init_app_state(self):
        winlayout = conf.load("window")
        if (winlayout):
            try:
                uikit.app_restore(self, winlayout)
                self.logo_scale(map=winlayout["toolbar"]["icon_size"])
            except Exception as e:
                log.APPSTATE_RESTORE(e) # may fail for disabled/reordered plugin channels


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
                log.ERR("st2.gtk_main_quit", e)
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

