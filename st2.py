#!/usr/bin/env python
# encoding: UTF-8
# api: python
# type: application
# title: streamtuner2
# description: directory browser for internet radio / audio streams
# depends: gtk, pygtk, xml.dom.minidom, threading, lxml, pyquery, kronos
# version: 2.0.9
# author: mario salzer
# license: public domain
# url: http://freshmeat.net/projects/streamtuner2
# config: <env name="http_proxy" value="" description="proxy for HTTP access" />  <env name="XDG_CONFIG_HOME" description="relocates user .config subdirectory" />
# category: multimedia
# 
#
#
# Streamtuner2 is a GUI browser for internet radio directories. Various
# providers can be added, and streaming stations are usually grouped into
# music genres or categories. It starts external audio players for stream
# playing and streamripper for recording broadcasts.
#
# It's an independent rewrite of streamtuner1 in a scripting language. So
# it can be more easily extended and fixed. The use of PyQuery for HTML
# parsing makes this simpler and more robust.
#
# Stream lists are stored in JSON cache files.
#
#
#


""" project status """
#
# Cumulative development time is two months now, but the application
# runs mostly stable already. The GUI interfaces are workable.
# There haven't been any optimizations regarding memory usage and
# performance. The current internal API is acceptable. Documentation is
# coming up.
#
#  current bugs:
#   - audio- and list-format support is not very robust / needs better API
#   - lots of GtkWarning messages
#   - not all keyboard shortcuts work
#   - in-list search doesn't work in our treeviews (???)
#   - JSON files are only trouble: loading of data files might lead to more
#     errors now, even if pson module still falls back on old method
#     (unicode strings from json.load are useless to us, require typecasts)
#     (nonsupport of tuples led to regression in mygtk.app_restore)
#     (sometimes we receive 8bit-content, which the json module can't save)
#
#  features:
#   - treeview lists are created from datamap[] structure and stream{} dicts
#   - channel categories are built-in defaults (can be freshened up however)
#   - config vars and cache data get stored as JSON in ~/.config/streamtuner2/
#
#  missing:
#   - localization
#
#  security notes:
#   - directory scrapers use fragile regular expressions - which is probably
#     not a security risk, but might lead to faulty data
#   - MEDIUM: little integrity checking for .pls / .m3u references and files
#   - minimal XML/SGML entity decoding (-> faulty data)
#   - MEDIUM: if system json module is not available, pseudo-json uses eval()
#     to read the config data -> limited risk, since it's only local files
#   - HIGH RISK: no verification of downloaded favicon image files (ico/png),
#     as they are passed to gtk.gdk.Pixbuf (OTOH data pre-filtered by Google)
#   - MEDIUM: audio players / decoders are easily affected by buffer overflows
#     from corrupt mp3/stream data, and streamtuner2 executes them
#      - but since that's the purpose -> no workaround
#
#  still help wanted on:
#   - any of the above
#   - new plugins (local file viewer)
#   - nicer logo (or donations accepted to consult graphics designer)
#



# standard modules
import sys
import os, os.path
import re
import copy
import urllib

# threading or processing module
try:
    from processing import Process as Thread
except:
    from threading import Thread
    Thread.stop = lambda self: None

# gtk modules
import pygtk
import gtk
import gtk.glade
import gobject


# custom modules
sys.path.insert(0, "/usr/share/streamtuner2")   # pre-defined directory for modules
sys.path.insert(0, ".")   # pre-defined directory for modules
from config import conf   # initializes itself, so all conf.vars are available right away
from mygtk import mygtk   # gtk treeview
import http
import action  # needs workaround... (action.main=main)
from channels import *
from channels import __print__
import favicon
#from pq import pq



# this represents the main window
# and also contains most application behaviour
main = None
class StreamTunerTwo(gtk.Builder):


        # object containers
        widgets = {}     # non-glade widgets (the manually instantiated ones)
        channels = {}    # channel modules
        features = {}    # non-channel plugins
        working = []     # threads

        # status variables
        channel_names = ["bookmarks"]    # order of channel notebook tabs
        current_channel = "bookmarks"    # currently selected channel name (as index in self.channels{})


        # constructor
        def __init__(self):

            # gtkrc stylesheet
            self.load_theme(), gui_startup(0.05)

            # instantiate gtk/glade widgets in current object
            gtk.Builder.__init__(self)
            ui_file = [i for i in sum([[i, conf.share+"/"+i] for i in ["ui.xml", "st2.gtk"]], []) if os.path.exists(i)][0];
            gtk.Builder.add_from_file(self, ui_file), gui_startup(0.10)
            # manual gtk operations
            self.extensionsCTM.set_submenu(self.extensions)  # duplicates Station>Extension menu into stream context menu

            # initialize channels
            self.channels = {
              "bookmarks": bookmarks(parent=self),   # this the remaining built-in channel
              "shoutcast": None,#shoutcast(parent=self),
            }
            gui_startup(0.15)
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

            # display current open channel/notebook tab
            gui_startup(0.90)
            self.current_channel = self.current_channel_gtk()
            try: self.channel().first_show()
            except: print("channel .first_show() initialization error")

      
            # bind gtk/glade event names to functions
            gui_startup(0.95)
            self.connect_signals({
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
                # else
                "menu_properties": config_dialog.open,
                "config_cancel": config_dialog.hide,
                "config_save": config_dialog.save,
                "update_categories": self.update_categories,
                "update_favicons": self.update_favicons,
                "app_state": self.app_state,
                "bookmark": self.bookmark,
                "save_as": self.save_as,
                "menu_about": lambda w: AboutStreamtuner2(),
                "menu_help": action.action.help,
                "menu_onlineforum": lambda w: action.browser("http://sourceforge.net/projects/streamtuner2/forums/forum/1173108"),
               # "menu_bugreport": lambda w: BugReport(),
                "menu_copy": self.menu_copy,
                "delete_entry": self.delete_entry,
                "quicksearch_set": search.quicksearch_set,
                "search_open": search.menu_search,
                "search_go": search.start,
                "search_srv": search.start,
                "search_google": search.google,
                "search_cancel": search.cancel,
                "true": lambda w,*args: True,
                "streamedit_open": streamedit.open,
                "streamedit_save": streamedit.save,
                "streamedit_new": streamedit.new,
                "streamedit_cancel": streamedit.cancel,
            })
            
            # actually display main window
            gui_startup(0.99)
            self.win_streamtuner2.show()
            
            # WHY DON'T YOU WANT TO WORK?!
            #self.shoutcast.gtk_list.set_enable_search(True)
            #self.shoutcast.gtk_list.set_search_column(4)


          

        #-- Shortcut fo glade.get_widget()
        # allows access to widgets as direct attributes instead of using .get_widget()
        # also looks in self.channels[] for the named channel plugins
        def __getattr__(self, name):
            if (self.channels.has_key(name)):
                return self.channels[name]     # like self.shoutcast
            else:
                return self.get_object(name)   # or gives an error if neither exists

        # custom-named widgets are available from .widgets{} not via .get_widget()
        def get_widget(self, name):
            if self.widgets.has_key(name):
                return self.widgets[name]
            else:
                return gtk.Builder.get_object(self, name)
                


                
        # returns the currently selected directory/channel object
        def channel(self):
            #try:
                return self.channels[self.current_channel]
            #except Exception,e:
            #    print(e)
            #    self.notebook_channels.set_current_page(0)
            #    self.current_channel = "bookmarks"
            #    return self.channels["bookmarks"]
            
        def current_channel_gtk(self):
            i = self.notebook_channels.get_current_page()
            try: return self.channel_names[i]
            except: return "bookmarks"

        # notebook tab clicked
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
                print("try: .first_show", self.channel().module);
                print(self.channel().first_show)
                print(self.channel().first_show())
            except:
                print("channel .first_show() initialization error")




        # convert ListStore iter to row number
        def rowno(self):
            (model, iter) = self.model_iter()
            return model.get_path(iter)[0]

        # currently selected entry in stations list, return complete data dict
        def row(self):
            return self.channel().stations() [self.rowno()]
            
        # return ListStore object and Iterator for currently selected row in gtk.TreeView station list
        def model_iter(self):
            return self.channel().gtk_list.get_selection().get_selected()
            
        # fetches a single varname from currently selected station entry
        def selected(self, name="url"):
            return self.row().get(name)

                


        # play button
        def on_play_clicked(self, widget, event=None, *args):
            row = self.row()
            if row:
                self.channel().play(row)
                favicon.download_playing(row)

        # streamripper
        def on_record_clicked(self, widget):
            row = self.row()
            action.record(row.get("url"), "audio/mp3", "url/direct", row=row)

        # browse stream
        def on_homepage_stream_clicked(self, widget):
            url = self.selected("homepage")             
            action.browser(url)
             
        # browse channel
        def on_homepage_channel_clicked(self, widget, event=2):
            if event == 2 or event.type == gtk.gdk._2BUTTON_PRESS:
                __print__("dblclick")
                action.browser(self.channel().homepage)            

        # reload stream list in current channel-category
        def on_reload_clicked(self, widget=None, reload=1):
            __print__("reload", reload, self.current_channel, self.channels[self.current_channel], self.channel().current)
            category = self.channel().current
            self.thread(
                lambda: (  self.channel().load(category,reload), reload and self.bookmarks.heuristic_update(self.current_channel,category)  )
            )
            
        # thread a function, add to worker pool (for utilizing stop button)
        def thread(self, target, *args):
            thread = Thread(target=target, args=args)
            thread.start()
            self.working.append(thread)

        # stop reload/update threads
        def on_stop_clicked(self, widget):
            while self.working:
                thread = self.working.pop()
                thread.stop()
        
        # click in category list
        def on_category_clicked(self, widget, event, *more):
            category = self.channel().currentcat()
            __print__("on_category_clicked", category, self.current_channel)
            self.on_reload_clicked(None, reload=0)
            pass

        # add current selection to bookmark store
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

        # reload category tree
        def update_categories(self, widget):
            Thread(target=self.channel().reload_categories).start()
            
        # menu invocation: refresh favicons for all stations in current streams category
        def update_favicons(self, widget):
            entries = self.channel().stations()
            favicon.download_all(entries)

        # save a file            
        def save_as(self, widget):
            row = self.row()
            default_fn = row["title"] + ".m3u"
            fn = mygtk.save_file("Save Stream", None, default_fn, [(".m3u","*m3u"),(".pls","*pls"),(".xspf","*xspf"),(".smil","*smil"),(".asx","*asx"),("all files","*")])
            if fn:
                action.save(row, fn)
            pass

        # save current stream URL into clipboard
        def menu_copy(self, w):
            gtk.clipboard_get().set_text(self.selected("url"))

        # remove an entry
        def delete_entry(self, w):
            n = self.rowno()
            del self.channel().stations()[ n ]
            self.channel().switch()
            self.channel().save()

        # stream right click
        def station_context_menu(self, treeview, event):
            return station_context_menu(treeview, event) # wrapper to the static function
            




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
                if (text >= 1.0):  # completed
                    mygtk.do(lambda:self.progress.hide())
                else:  # show percentage
                    mygtk.do(lambda:self.progress.show() or self.progress.set_fraction(text))
                    if (text <= 0.0):  # unknown state
                        mygtk.do(lambda:self.progress.pulse())
            # add text
            elif (type(text)==str):
                sbar_msg.append(1)
                mygtk.do(lambda:self.statusbar.push(sbar_cid, text))
            pass

        # load plugins from /usr/share/streamtuner2/channels/
        def load_plugin_channels(self):

            # find plugin files
            ls = os.listdir(conf.share + "/channels/")
            ls = [fn[:-3] for fn in ls if re.match("^[a-z][\w\d_]+\.py$", fn)]
            
            # resort with tab order
            order = [module.strip() for module in conf.channel_order.lower().replace(".","_").replace("-","_").split(",")]
            ls = [module for module in (order) if (module in ls)] + [module for module in (ls) if (module not in order)]

            # step through
            for module in ls:
                gui_startup(0.2 + 0.7 * float(ls.index(module))/len(ls), "loading module "+module)
                                
                # skip module if disabled
                if conf.plugins.get(module, 1) == False:
                    __print__("disabled plugin:", module)
                    continue
                
                # load plugin
                try:
                    plugin = __import__("channels."+module, None, None, [""])
                    plugin_class = plugin.__dict__[module]
                
                    # load .config settings from plugin
                    conf.add_plugin_defaults(plugin_class.config, module)

                    # add and initialize channel
                    if issubclass(plugin_class, GenericChannel):
                        self.channels[module] = plugin_class(parent=self)
                        if module not in self.channel_names:  # skip (glade) built-in channels
                            self.channel_names.append(module)
                    # other plugin types
                    else:
                        self.features[module] = plugin_class(parent=self)
                    
                except Exception, e:
                    print("error initializing:", module)
                    print(e)

            # default plugins
            conf.add_plugin_defaults(self.channels["bookmarks"].config, "bookmarks")
            #conf.add_plugin_defaults(self.channels["shoutcast"].config, "shoutcast")

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
                self.app_state(widget)
            gtk.main_quit()






                




# auxiliary window: about dialog
class AboutStreamtuner2:
        # about us
        def __init__(self):
            a = gtk.AboutDialog()
            a.set_version("2.0.9")
            a.set_name("streamtuner2")
            a.set_license("Public Domain\n\nNo Strings Attached.\nUnrestricted distribution,\nmodification, use.")
            a.set_authors(["Mario Salzer <http://mario.include-once.org/>\n\nConcept based on streamtuner 0.99.99 from\nJean-Yves Lefort, of which some code remains\nin the Google stations plugin.\n<http://www.nongnu.org/streamtuner/>\n\nMyOggRadio plugin based on cooperation\nwith Christian Ehm. <http://ehm-edv.de/>"])
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
                main.streamactions.popup(None, None, None, event.button, event.time)
                return None
            # we need to pass on to normal left-button signal handler
            else:
                return False
# this works better as callback function than as class - because of False/Object result for event trigger




# encapsulates references to gtk objects AND properties in main window
class auxiliary_window(object):
        def __getattr__(self, name):
            if main.__dict__.has_key(name):
                return main.__dict__[name]
            elif StreamTunerTwo.__dict__.has_key(name):
                return StreamTunerTwo.__dict__[name]
            else:
                return main.get_widget(name)
""" allows to use self. and main. almost interchangably """



# aux win: search dialog (keeps search text in self.q)
# and also: quick search textbox (uses main.q instead)
class search (auxiliary_window):

        # show search dialog   
        def menu_search(self, w):
            self.search_dialog.show();

        # hide dialog box again
        def cancel(self, *args):
            self.search_dialog.hide()
            return True  # stop any other gtk handlers
            #self.search_dialog.hide() #if conf.hide_searchdialog
            
            
        # perform search
        def start(self, *w):
            self.cancel()
            
            # prepare variables
            self.q = self.search_full.get_text().lower()
            entries = []
            main.bookmarks.streams["search"] = []
            
            # which fields?
            fields = ["title", "playing", "genre", "homepage", "url", "extra", "favicon", "format"]
            if not self.search_in_all.get_active():
                fields = [f for f in fields if (main.get_widget("search_in_"+f) and main.get_widget("search_in_"+f).get_active())]
            # channels?
            channels = main.channel_names[:]
            if not self.search_channel_all.get_active():
                channels = [c for c in channels if main.get_widget("search_channel_"+c).get_active()]
            
            # step through channels
            for c in channels:
                if main.channels[c] and main.channels[c].streams:  # skip disabled plugins

                    # categories
                    for cat in main.channels[c].streams.keys():

                        # stations
                        for row in main.channels[c].streams[cat]:
                    
                            # assemble text fields
                            text = " ".join([row.get(f, " ") for f in fields])
                        
                            # compare
                            if text.lower().find(self.q) >= 0:

                                # add result
                                entries.append(row)

            
            # display "search" in "bookmarks"
            main.channel_switch(None, "bookmarks", 0)
            main.bookmarks.set_category("search")
            # insert data and show
            main.channels["bookmarks"].streams["search"] = entries   # we have to set it here, else .currentcat() might reset it 
            main.bookmarks.load("search")
            
            
        # live search on directory server homepages
        def server_query(self, w):
            "unimplemented"
            
        # don't search at all, open a web browser
        def google(self, w):
            self.cancel()
            action.browser("http://www.google.com/search?q=" + self.search_full.get_text())


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
            row = main.row()
            for name in ("title", "playing", "genre", "homepage", "url", "favicon", "format", "extra"):
                w = main.get_widget("streamedit_" + name) 
                if w:
                    w.set_text((str(row.get(name)) if row.get(name) else ""))
            self.win_streamedit.show()

        # copy widget contents to stream
        def save(self, w):
            row = main.row()
            for name in ("title", "playing", "genre", "homepage", "url", "favicon", "format", "extra"):
               w = main.get_widget("streamedit_" + name)
               if w:
                   row[name] = w.get_text()
            main.channel().save()
            self.cancel(w)
            
        # add a new list entry, update window
        def new(self, w):
            s = main.channel().stations()
            s.append({"title":"new", "url":"", "format":"audio/mp3", "genre":"", "listeners":1});
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

        # display win_config, pre-fill text fields from global conf. object
        def open(self, widget):
            self.add_plugins()
            self.apply(conf.__dict__, "config_", 0)
            #self.win_config.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#443399'))
            self.combobox_theme()
            self.win_config.show()

        def hide(self, *args):
            self.win_config.hide()
            return True
        
        # set/load values between gtk window and conf. dict
        def apply(self, config, prefix="config_", save=0):
            for key,val in config.iteritems():
                # map non-alphanumeric chars from config{} to underscores in according gtk widget names
                id = re.sub("[^\w]", "_", key)
                w = main.get_widget(prefix + id)
                __print__("config_save", save, prefix+id, w, val)
                # recurse into dictionaries, transform: conf.play.audio/mp3 => conf.play_audio_mp3
                if (type(val) == dict):
                    self.apply(val, prefix + id + "_", save)
                # load or set gtk.Entry text field
                elif (w and save and type(w)==gtk.Entry):
                    config[key] = w.get_text()
                elif (w and type(w)==gtk.Entry):
                    w.set_text(str(val))
                elif (w and save):
                    config[key] = w.get_active()
                elif (w):
                    w.set_active(bool(val))
            pass

        # fill combobox
        def combobox_theme(self):
           # self.theme.combo_box_new_text()
            # find themes
            themedirs = (conf.share+"/themes", conf.dir+"/themes", "/usr/share/themes")
            themes = ["no theme"]
            [[themes.append(e) for e in os.listdir(dir)] for dir in themedirs if os.path.exists(dir)]
            # add to combobox
            for num,themename in enumerate(themes):
                 self.theme.append_text(themename)
                 if conf.theme == themename:
                     self.theme.set_active(num)
            # erase this function, so it only ever gets called once
            self.combobox_theme = lambda: None

        # retrieve currently selected value
        def apply_theme(self):
            if self.theme.get_active() >= 0:
                conf.theme = self.theme.get_model()[ self.theme.get_active()][0]
                main.load_theme()

        # add configuration setting definitions from plugins
        once = 0
        def add_plugins(self):
            if self.once:
                return

            for name,enabled in conf.plugins.iteritems():

                # add plugin load entry
                if name:
                    label = ("enable ⎗ %s channel" if self.channels.get(name) else "use ⎗ %s plugin")
                    cb =  gtk.ToggleButton(label=label % name)
                    self.add_( "config_plugins_"+name, cb )#, label=None, color="#ddd" )

                # look up individual plugin options, if loaded
                if self.channels.get(name) or self.features.get(name):
                    c = self.channels.get(name) or self.features.get(name)
                    for opt in c.config:

                        # default values are already in conf[] dict (now done in conf.add_plugin_defaults)
                            
                        # display checkbox or text entry
                        if opt["type"] == "boolean":
                            cb = gtk.CheckButton(opt["description"])
                            #cb.set_line_wrap(True)
                            self.add_( "config_"+opt["name"], cb )
                        else:
                            self.add_( "config_"+opt["name"], gtk.Entry(), opt["description"] )

                # spacer 
                self.add_( "filler_pl_"+name, gtk.HSeparator() )
            self.once = 1

        # put gtk widgets into config dialog notebook
        def add_(self, id, w, label=None, color=""):
            w.set_property("visible", True)
            main.widgets[id] = w
            if label:
                w.set_width_chars(10)
                label = gtk.Label(label)
                label.set_property("visible", True)
                label.set_line_wrap(True) 
                label.set_size_request(250, -1)
                vbox = gtk.HBox(homogeneous=False, spacing=10)
                vbox.set_property("visible", True)
                vbox.pack_start(w, expand=False, fill=False)
                vbox.pack_start(label, expand=True, fill=True)
                w = vbox
            if color:
                w = mygtk.bg(w, color)
            self.plugin_options.pack_start(w)

        
        # save config
        def save(self, widget):
            self.apply(conf.__dict__, "config_", 1)
            self.apply_theme()
            conf.save(nice=1)
            self.hide()
                  
config_dialog = config_dialog()
# instantiates itself





























# class GenericChannel:
#
#   is in channels/__init__.py
#





#-- favourite lists                                            ------------------------------------------
#
# This module lists static content from ~/.config/streamtuner2/bookmarks.json;
# its data list is queried by other plugins to add 'star' icons.
#
# Some feature extensions inject custom categories[] into streams{}
# e.g. "search" adds its own category once activated, as does the "timer" plugin.
#
class bookmarks(GenericChannel):

        # desc
        api = "streamtuner2"
        module = "bookmarks"
        title = "bookmarks"
        version = 0.4
        base_url = "file:.config/streamtuner2/bookmarks.json"
        listformat = "*/*"
        
        # i like this
        config = [
            {"name":"like_my_bookmarks", "type":"boolean", "value":0, "description":"I like my bookmarks"},
        ]

        # content
        categories = ["favourite", ]
        current = "favourite"
        default = "favourite"
        streams = {"favourite":[], "search":[], "scripts":[], "timer":[], }
        
        # cache list, to determine if a PLS url is bookmarked
        urls = []


        # this channel does not actually retrieve/parse data from anywhere
        def update_categories(self):
            pass
        def update_streams(self, cat):
            return self.streams.get(cat, [])
            
        # initial display
        def first_show(self):
            if not self.streams["favourite"]:
                self.cache()
        # all entries just come from "bookmarks.json"
        def cache(self):
            # stream list
            cache = conf.load(self.module)
            if (cache):
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
                row["listformat"] = main.channel().listformat
               
            # append to storage
            self.streams["favourite"].append(row)
            self.save()
            self.load(self.default)
            self.urls.append(row["url"])


        # simplified gtk TreeStore display logic (just one category for the moment, always rebuilt)
        def load(self, category, force=False):
            #self.liststore[category] = \
#            print(category, self.streams.keys())
            mygtk.columns(self.gtk_list, self.datamap, self.prepare(self.streams.get(category,[])))


        # select a category in treeview
        def add_category(self, cat):
            if cat not in self.categories: # add category if missing
                self.categories.append(cat)
                self.display_categories()
        # change cursor
        def set_category(self, cat):
            self.add_category(cat)
            self.gtk_cat.get_selection().select_path(str(self.categories.index(cat)))
            return self.currentcat()
            
            
        # update bookmarks from freshly loaded streams data
        def heuristic_update(self, updated_channel, updated_category):

            if not conf.heuristic_bookmark_update: return
            save = 0
            fav = self.streams["favourite"]
        
            # First we'll generate a list of current bookmark stream urls, and then
            # remove all but those from the currently UPDATED_channel + category.
            # This step is most likely redundant, but prevents accidently re-rewriting
            # stations that are in two channels (=duplicates with different PLS urls).
            check = {"http//": "[row]"}
            check = dict((row["url"],row) for row in fav)
            # walk through all channels/streams
            for chname,channel in main.channels.iteritems():
                for cat,streams in channel.streams.iteritems():

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













#-- startup progress bar
progresswin, progressbar = 0, 0
def gui_startup(p=0.0, msg="streamtuner2 is starting"):
    global progresswin,progressbar
    if not progresswin:
        # GtkWindow "progresswin"
        progresswin = gtk.Window()
        progresswin.set_property("title", "streamtuner2")
        progresswin.set_property("default_width", 300)
        progresswin.set_property("width_request", 300)
        progresswin.set_property("default_height", 30)
        progresswin.set_property("height_request", 30)
        progresswin.set_property("window_position", "center")
        progresswin.set_property("decorated", False)
        progresswin.set_property("visible", True)
        # GtkProgressBar "progressbar"
        progressbar = gtk.ProgressBar()
        progressbar.set_property("visible", True)
        progressbar.set_property("show_text", True)
        progressbar.set_property("text", msg)
        progresswin.add(progressbar)
        progresswin.show_all()
    try:
      if p<1:
        progressbar.set_fraction(p)
        progressbar.set_property("text", msg)
        while gtk.events_pending(): gtk.main_iteration(False)
      else:
        progresswin.destroy()
    except: return




#-- run main                                ---------------------------------------------
if __name__ == "__main__":

    #-- global configuration settings
    "conf = Config()"       # already happened with "from config import conf"

    # graphical
    if len(sys.argv) < 2:
    
        
        # prepare for threading in Gtk+ callbacks
        gobject.threads_init()
        gui_startup(0.05)
        
        # prepare main window
        main = StreamTunerTwo()
        
        # module coupling
        action.main = main      # action (play/record) module needs a reference to main window for gtk interaction and some URL/URI callbacks
        action = action.action  # shorter name
        http.feedback = main.status  # http module gives status feedbacks too
        
        # first invocation
        if (conf.get("firstrun")):
            config_dialog.open(None)
            del conf.firstrun


        # run
        gui_startup(1.00)
        gtk.main()
        
        
    # invoke command-line interface
    else:
        import cli
        cli.StreamTunerCLI()




#
#
#
#
