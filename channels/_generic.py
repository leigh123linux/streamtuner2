#
# encoding: UTF-8
# api: streamtuner2
# type: class
# title: channel objects
# description: base functionality for channel modules
# version: 1.0
# author: mario
# license: public domain
#
#
#  GenericChannel implements the basic GUI functions and defines
#  the default channel data structure. It implements base and
#  fallback logic for all other channel implementations.
#
#  Built-in channels derive directly from generic. Additional
#  channels don't have a pre-defined Notebook tab in the glade
#  file. They derive from the ChannelPlugins class instead, which
#  adds the required gtk Widgets manually.
#


import gtk
from mygtk import mygtk
from config import conf, __print__, dbg
import ahttp as http
import action
import favicon
import os.path
import xml.sax.saxutils
import re
import copy


# dict==object
class struct(dict):
        def __init__(self, *xargs, **kwargs):
                self.__dict__ = self
                self.update(kwargs)
                [self.update(x) for x in xargs]
        pass


# generic channel module                            ---------------------------------------
class GenericChannel(object):

        # desc
        api = "streamtuner2"
        module = "generic"
        title = "GenericChannel"
        version = 1.0
        homepage = "http://milki.inlcude-once.org/streamtuner2/"
        base_url = ""
        listformat = "audio/x-scpls"
        audioformat = "audio/mp3" # fallback value
        config = []
        has_search = False

        # categories
        categories = ["empty", ]
        current = ""
        default = "empty"
        shown = None     # last selected entry in stream list, also indicator if notebook tab has been selected once / stream list of current category been displayed yet

        # gui + data
        streams = {}      #meta information dicts
        liststore = {}    #gtk data structure
        gtk_list = None   #gtk widget
        gtk_cat = None    #gtk widget

        # mapping of stream{} data into gtk treeview/treestore representation
        datamap = [
           # coltitle   width	[ datasrc key, type, renderer, attrs ]	[cellrenderer2], ...
           ["",		20,	["state",	str,  "pixbuf",	{}],	],
           ["Genre",	65,	['genre',	str,	"t",	{}],	],
           ["Station Title",275,["title",	str,    "text",	{"strikethrough":11, "cell-background":12, "cell-background-set":13}],  ["favicon", gtk.gdk.Pixbuf, "pixbuf", {}], ],
           ["Now Playing",185,	["playing",	str,	"text",	{"strikethrough":11}],	],                                                                             #{"width":20}
           ["Listeners", 45,	["listeners",	int,	"t",	{"strikethrough":11}],	],
          #["Max",	45,	["max",		int,	"t",	{}],	],
           ["Bitrate",	35,	["bitrate",	int,	"t",	{}],	],
           ["Homepage",	160,	["homepage",	str,	"t",	{"underline":10}],	],
           [False,	25,	["url",		str,	"t",	{"strikethrough":11}],	],
           [False,	0,	["format",	str,	None,	{}],	],
           [False,	0,	["favourite",	bool,	None,	{}],	],
           [False,	0,	["deleted",	bool,	None,	{}],	],
           [False,	0,	["search_col",	str,	None,	{}],	],
           [False,	0,	["search_set",	bool,	None,	{}],	],
        ]
        rowmap = []   # [state,genre,title,...] field enumeration still needed separately
        titles = {}   # for easier adapting of column titles in datamap
        
        # regex            
        rx_www_url = re.compile("""(www(\.\w+[\w-]+){2,}|(\w+[\w-]+[ ]?\.)+(com|FM|net|org|de|PL|fr|uk))""", re.I)


        # constructor
        def __init__(self, parent=None):
        
            #self.streams = {}
            self.gtk_list = None
            self.gtk_cat = None

            # only if streamtuner2 is run in graphical mode        
            if (parent):
                self.cache()
                self.gui(parent)
            pass
            
            
        # called before application shutdown
        # some plugins might override this, to save their current streams[] data
        def shutdown(self):
            pass
        #__del__ = shutdown
            
            
        # returns station entries from streams[] for .current category
        def stations(self):
            return self.streams.get(self.current, [])
        def rowno(self):
            pass
        def row(self):
            pass
        

        # read previous channel/stream data, if there is any
        def cache(self):
            # stream list
            cache = conf.load("cache/" + self.module)
            if (cache):
                self.streams = cache
            # categories
            cache = conf.load("cache/categories_" + self.module)
            if (cache):
                self.categories = cache
            pass

            
        # initialize Gtk widgets / data objects
        def gui(self, parent):
            #print(self.module + ".gui()")

            # save reference to main window/glade API
            self.parent = parent
            self.gtk_list = parent.get_widget(self.module+"_list")
            self.gtk_cat = parent.get_widget(self.module+"_cat")
            
            # category tree
            self.display_categories()
            #mygtk.tree(self.gtk_cat, self.categories, title="Category", icon=gtk.STOCK_OPEN);
            
            # update column names
            for field,title in list(self.titles.items()):
                self.update_datamap(field, title=title)
            
            # prepare stream list
            if (not self.rowmap):
                for row in self.datamap:
                    for x in range(2, len(row)):
                        self.rowmap.append(row[x][0])

            # load default category
            if (self.current):
                self.load(self.current)
            else:
                mygtk.columns(self.gtk_list, self.datamap, [{}])
                
            # add to main menu
            mygtk.add_menu(parent.channelmenuitems, self.title, lambda w: parent.channel_switch(w, self.module) or 1)
            
            
        # make private copy of .datamap and modify field (title= only ATM)
        def update_datamap(self, search="name", title=None):
            if self.datamap == GenericChannel.datamap:
                self.datamap = copy.deepcopy(self.datamap)
            for i,row in enumerate(self.datamap):
                if row[2][0] == search:
                    row[0] = title


        # switch stream category,
        # load data,
        # update treeview content
        def load(self, category, force=False):
        
            # get data from cache or download
            if (force or not category in self.streams):
                new_streams = self.update_streams(category)
      
                if new_streams:
                
                    # modify
                    [self.postprocess(row) for row in new_streams]
      
                    # don't lose forgotten streams
                    if conf.retain_deleted:
                       self.streams[category] = new_streams + self.deleted_streams(new_streams, self.streams.get(category,[]))
                    else:
                       self.streams[category] = new_streams
      
                    # save in cache
                    self.save()
      
                    # invalidate gtk list cache
                    #if (self.liststore.has_key(category)):
                    #    del self.liststore[category]
      
                else:
                    # parse error
                    self.parent.status("category parsed empty.")
                    self.streams[category] = [{"title":"no contents found on directory server","bitrate":0,"max":0,"listeners":0,"playing":"error","favourite":0,"deleted":0}]
                    __print__(dbg.ERR, "Oooops, parser returned nothing for category " + category)
                    
            # assign to treeview model
            #self.streams[self.default] = []
            #if (self.liststore.has_key(category)):  # was already loded before
            #    self.gtk_list.set_model(self.liststore[category])
            #else:   # currently list is new, had not been converted to gtk array before
            #    self.liststore[category] = \
            mygtk.do(lambda:mygtk.columns(self.gtk_list, self.datamap, self.prepare(self.streams[category])))

            # set pointer
            self.current = category
            pass
            
        # store current streams data
        def save(self):
            conf.save("cache/" + self.module, self.streams, gz=1)


        # called occasionally while retrieving and parsing
        def update_streams_partially_done(self, entries):
            mygtk.do(lambda: mygtk.columns(self.gtk_list, self.datamap, entries))

            
        # finds differences in new/old streamlist, marks deleted with flag
        def deleted_streams(self, new, old):
            diff = []
            new = [row.get("url","http://example.com/") for row in new]
            for row in old:
                if ("url" in row and (row.get("url") not in new)):
                    row["deleted"] = 1
                    diff.append(row)
            return diff

        
        # prepare data for display
        def prepare(self, streams):
            for i,row in enumerate(streams):
                                            # oh my, at least it's working
                                            # at start the bookmarks module isn't fully registered at instantiation in parent.channels{} - might want to do that step by step rather
                                            # then display() is called too early to take effect - load() & co should actually be postponed to when a notebook tab gets selected first
                                            # => might be fixed now, 1.9.8
                # state icon: bookmark star
                if (conf.show_bookmarks and "bookmarks" in self.parent.channels and self.parent.bookmarks.is_in(streams[i].get("url", "file:///tmp/none"))):
                    streams[i]["favourite"] = 1
                
                # state icon: INFO or DELETE
                if (not row.get("state")):
                    if row.get("favourite"):
                        streams[i]["state"] = gtk.STOCK_ABOUT
                    if conf.retain_deleted and row.get("deleted"):
                        streams[i]["state"] = gtk.STOCK_DELETE
                      
                # guess homepage url  
                #self.postprocess(row)
                
                # favicons?
                if conf.show_favicons:
                    homepage_url = row.get("homepage")
                    # check for availability of PNG file, inject local icons/ filename
                    if homepage_url and favicon.available(homepage_url):
                        streams[i]["favicon"] = favicon.file(homepage_url)
                
            return streams

    
        # data preparations directly after reload        
        def postprocess(self, row):

            # remove non-homepages from shoutcast
            if row.get("homepage") and row["homepage"].find("//yp.shoutcast.")>0:
                row["homepage"] = ""
                
            # deduce homepage URLs from title
            # by looking for www.xyz.com domain names
            if not row.get("homepage"):
                url = self.rx_www_url.search(row.get("title", ""))
                if url:
                    url = url.group(0).lower().replace(" ", "")
                    url = (url if url.find("www.") == 0 else "www."+url)
                    row["homepage"] = http.fix_url(url)
            
            return row

            

        # reload current stream from web directory
        def reload(self):
            self.load(self.current, force=1)
        def switch(self):
            self.load(self.current, force=0)
            
            
        # display .current category, once notebook/channel tab is first opened
        def first_show(self):
            __print__(dbg.PROC, "first_show ", self.module, self.shown)

            if (self.shown != 55555):
            
                # if category tree is empty, initialize it
                if not self.categories:
                    __print__(dbg.PROC, "first_show: reload_categories");
                    #self.parent.thread(self.reload_categories)
                    self.reload_categories()
                    self.display_categories()
                    self.current = self.categories.keys()[0]
                    __print__(dbg.STAT, self.current)
                    self.load(self.current)
            
                # load current category
                else:
                    __print__(dbg.STAT, "first_show: load current category");
                    self.load(self.current)
                
                # put selection/cursor on last position
                try:
                    __print__(dbg.STAT, "first_show: select last known category treelist position")
                    self.gtk_list.get_selection().select_path(self.shown)
                except:
                    pass
                    
                # this method will only be invoked once
                self.shown = 55555


        # update categories, save, and display                
        def reload_categories(self):
        
            # get data and save
            self.update_categories()
            conf.save("cache/categories_"+self.module, self.categories)

            # display outside of this non-main thread            
            mygtk.do(self.display_categories)

        # insert content into gtk category list
        def display_categories(self):
        
            # remove any existing columns
            if self.gtk_cat:
                [self.gtk_cat.remove_column(c) for c in self.gtk_cat.get_columns()]
            # rebuild gtk.TreeView
            mygtk.tree(self.gtk_cat, self.categories, title="Category", icon=gtk.STOCK_OPEN);

            # if it's a short list of categories, there's probably subfolders
            if len(self.categories) < 20:
                self.gtk_cat.expand_all()
                
            # select any first element
            self.gtk_cat.get_selection().select_path("0") #set_cursor
            self.currentcat()

                
        # selected category
        def currentcat(self):
            (model, iter) = self.gtk_cat.get_selection().get_selected()
            if (type(iter) == gtk.TreeIter):
                self.current = model.get_value(iter, 0)
            return self.current




        #--------------------------- actions ---------------------------------

        # invoke action.play,
        # can be overridden to provide channel-specific "play" alternative
        def play(self, row):
            if row.get("url"):

                # parameters
                audioformat = row.get("format", self.audioformat)
                listformat = row.get("listformat", self.listformat)

                # invoke audio player
                action.action.play(row["url"], audioformat, listformat)




        #--------------------------- utility functions -----------------------

        

        # remove html <tags> from string        
        def strip_tags(self, s):
            return re.sub("<.+?>", "", s)
            
        # convert audio format nick/shortnames to mime types, e.g. "OGG" to "audio/ogg"
        def mime_fmt(self, s):
            # clean string
            s = s.lower().strip()
            # rename
            map = {
                "audio/mpeg":"audio/mp3",  # Note the real mime type is /mpeg, but /mp3 is more understandable in the GUI
                "ogg":"ogg", "ogm":"ogg", "xiph":"ogg", "vorbis":"ogg", "vnd.xiph.vorbis":"ogg",
                "mpeg":"mp3", "mp":"mp3", "mp2":"mp3", "mpc":"mp3", "mps":"mp3",
                "aac+":"aac", "aacp":"aac",
                "realaudio":"x-pn-realaudio", "real":"x-pn-realaudio", "ra":"x-pn-realaudio", "ram":"x-pn-realaudio", "rm":"x-pn-realaudio",
                # yes, we do video
                "flv":"video/flv", "mp4":"video/mp4",
            }
            map.update(action.action.lt)   # list type formats (.m3u .pls and .xspf)
            if map.get(s):
                s = map[s]
            # add prefix:
            if s.find("/") < 1:
                s = "audio/" + s
            #
            return s
        
        # remove SGML/XML entities
        def entity_decode(self, s):
            return xml.sax.saxutils.unescape(s)
        
        # convert special characters to &xx; escapes
        def xmlentities(self, s):
            return xml.sax.saxutils.escape(s)









# channel plugin without glade-pre-defined notebook tab
#
class ChannelPlugin(GenericChannel):

        module = "abstract"
        title = "New Tab"
        version = 0.1


        def gui(self, parent):
        
            # name id
            module = self.module

            if parent:
                # two panes
                vbox = gtk.HPaned()
                vbox.show()
                # category treeview
                sw1 = gtk.ScrolledWindow()
                sw1.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
                sw1.set_property("width_request", 150)
                sw1.show()
                tv1 = gtk.TreeView()
                tv1.set_property("width_request", 75)
                tv1.set_property("enable_tree_lines", True)
                tv1.connect("button_release_event", parent.on_category_clicked)
                tv1.show()
                sw1.add(tv1)
                vbox.pack1(sw1, resize=False, shrink=True)
                # stream list
                sw2 = gtk.ScrolledWindow()
                sw2.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
                sw2.show()
                tv2 = gtk.TreeView()
                tv2.set_property("width_request", 200)
                tv2.set_property("enable_tree_lines", True)
                tv2.connect("row_activated", parent.on_play_clicked)
                tv2.show()
                sw2.add(tv2)
                vbox.pack2(sw2, resize=True, shrink=True)

                # prepare label
                label = gtk.HBox()
                label.set_property("visible", True)
                fn = "/usr/share/streamtuner2/channels/" + self.module + ".png"
                if os.path.exists(fn):
                    icon = gtk.Image()
                    icon.set_property("pixbuf", gtk.gdk.pixbuf_new_from_file(fn))
                    icon.set_property("icon-size", 1)
                    icon.set_property("visible", True)
                    label.pack_start(icon, expand=False, fill=True)
                if self.title:
                    text = gtk.Label(self.title)
                    text.set_property("visible", True)
                    label.pack_start(text, expand=True, fill=True)
                    
                # pack it into an event container to catch double-clicks
                ev_label = gtk.EventBox()
                ev_label.add(label)
                ev_label.connect('event', parent.on_homepage_channel_clicked)



                # to widgets
                self.gtk_cat = tv1
                parent.widgets[module + "_cat"] = tv1
                self.gtk_list = tv2
                parent.widgets[module + "_list"] = tv2
                parent.widgets["v_" + module] = vbox
                parent.widgets["c_" + module] = ev_label
                tv2.connect('button-press-event', parent.station_context_menu)


                # try to initialize superclass now, before adding to channel tabs
                GenericChannel.gui(self, parent)


                # add notebook tab
                tab = parent.notebook_channels.append_page(vbox, ev_label)
                
                
                
                # double-click catch


                # add module to list            
                #parent.channels[module] = None
                #parent.channel_names.append(module)
                """ -> already taken care of in main.load_plugins() """





