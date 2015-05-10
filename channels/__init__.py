# encoding: UTF-8
# api: streamtuner2
# type: class
# category: ui
# title: Channel plugins
# description: Base implementation for channels and feature plugins
# version: 1.5
# license: public domain
# author: mario
# url: http://fossil.include-once.org/streamtuner2/
# pack:
#    bookmarks.py, configwin.py, dirble.py, dnd.py, exportcat.py,
#    filtermusic.py, global_key.py, history.py, internet_radio.py,
#    itunes.py, jamendo.py, links.py, live365.py, modarchive.py,
#    myoggradio.py, pluginmanager2.py, radiobrowser.py, radionomy.py,
#    radiotray.py, search.py, shoutcast.py, somafm.py, streamedit.py,
#    surfmusik.py, timer.py, tunein.py, ubuntuusers.py,
#    useragentswitcher.py, xiph.py, youtube.py
# config: -
# priority: core
#
# GenericChannel implements the basic GUI functions and defines
# the default channel data structure. It implements fallback logic
# for all other channel implementations. Only `bookmarks` uses it
# directly.
#
# All other plugins don't have a pre-defined Notebook tab in the
# GtkBuilder description. They derive from ChannelPlugins therefore,
# which constructs and registers the required gtk widgets manually.


import gtk
from uikit import uikit, ver as gtk_ver
from config import *
import ahttp
import action
import os.path
import xml.sax.saxutils
import re
import copy
import inspect


# Only export plugin classes
__all__ = [
    "GenericChannel", "ChannelPlugin", "use_rx",
    "entity_decode", "strip_tags", "nl", "unhtml", "to_int"
]
#__path__.insert(0, "plugins")#conf.plugin_dir)



# generic channel module                            ---------------------------------------
class GenericChannel(object):

    # control attributes
    meta = { "config": [] }
    base_url = ""
    listformat = "pls"
    audioformat = "audio/mpeg" # fallback value
    has_search = False

    # categories
    categories = []
    catmap = {}
    shown = None      # last selected entry in stream list, also indicator if notebook tab has been selected once / stream list of current category been displayed yet

    # gui + data
    streams = {}      # Station list dict, associates each genre to a list of stream rows
    gtk_list = None   # Gtk widget for station treeview
    gtk_cat = None    # Gtk widget for category columns
    _ls = None        # ListStore for station treeview
    _rowmap = None    # Preserve streams-datamap
    _pix_entry = None # ListStore entry that contains favicon

    # mapping of stream{} data into gtk treeview/treestore representation
    datamap = [
       # coltitle   width	[ datasrc key, type, renderer, attrs ]	[cellrenderer2], ...
       ["",		20,	["state",	str,  "pixbuf",	{}],	],
       ["Genre",	65,	['genre',	str,	"t",	{}],	],
       ["Station Title",275,	["title",	str,    "text",	{"strikethrough":11, "cell-background":12, "cell-background-set":13}],  ["favicon", gtk.gdk.Pixbuf, "pixbuf", {}], ],
       ["Now Playing",	185,	["playing",	str,	"text",	{"strikethrough":11}],	],                                                                             #{"width":20}
       ["Listeners", 	45,	["listeners",	int,	"t",	{"strikethrough":11}],	],
      #["Max",		45,	["max",		int,	"t",	{}],	],
       ["Bitrate",	35,	["bitrate",	int,	"t",	{}],	],
       ["Homepage",	160,	["homepage",	str,	"t",	{"underline":10}],	],
       [False,		25,	["url",		str,	"t",	{"strikethrough":11}],	],
       [False,		20,	["format",	str,	None,	{}],	],
       [False,		0,	["favourite",	bool,	None,	{}],	],
       [False,		0,	["deleted",	bool,	None,	{}],	],
       [False,		0,	["search_col",	str,	None,	{}],	],
       [False,		0,	["search_set",	bool,	None,	{}],	],
    ]
    rowmap = []   # [state,genre,title,...] field enumeration still needed separately
    titles = {}   # for easier adapting of column titles in datamap

    # for empty grouping / categories
    placeholder = [dict(genre="./.", title="Subcategory placeholder", playing="./.", url="none:", listeners=0, bitrate=0, homepage="", state="gtkfolder")]
    empty_stub = [dict(genre="./.", title="No categories found (HTTP error)", playing="Try Channel→Reload Categories later..", url="none:", listeners=0, bitrate=0, homepage="", state="gtk-stop")]
    nothing_found = [dict(genre="./.", title="No contents found on directory server", playing="Notice", listeners=0, bitrate=0, state="gtk-info")]
    
    # regex            
    rx_www_url = re.compile("""(www(\.\w+[\w-]+){2,}|(\w+[\w-]+[ ]?\.)+(com|FM|net|org|de|PL|fr|uk))""", re.I)


    #-- keep track of currently selected genre/category
    __current = None
    @property
    def current(self):
        return self.__current
    @current.setter
    def current(self, newcat):
        log.PROC("{}.current:={} ← from {}".format(self.module, newcat, [inspect.stack()[x][3] for x in range(1,4)]))
        self.__current = newcat
        return self.__current


    #--------------------------- initialization --------------------------------


    # constructor
    def __init__(self, parent=None):
    
        #self.streams = {}
        self.gtk_list = None
        self.gtk_cat = None
        self.module = self.__class__.__name__
        self.meta = plugin_meta(src = inspect.getcomments(inspect.getmodule(self)))
        self.config = self.meta.get("config", [])
        self.title = self.meta.get("title", self.module)

        # add default options values to config.conf.* dict
        conf.add_plugin_defaults(self.meta, self.module)
        
        # Only if streamtuner2 is run in graphical mode        
        if (parent):
            self.cache()
            self.gui(parent)

        # Stub for ST2 main window / dispatcher
        else:
            self.parent = stub_parent(None)

        
    # initialize Gtk widgets / data objects
    def gui(self, parent):

        # save reference to main window/glade API
        self.parent = parent
        self.gtk_list = parent.get_widget(self.module+"_list")
        self.gtk_cat = parent.get_widget(self.module+"_cat")
        
        # last category, and prepare genre tree
        self.current = conf.state(self.module).get("current")
        self.display_categories()

        # update column names
        for field,title in list(self.titles.items()):
            self.update_datamap(field, title=title)
        
        # Initialize stations TreeView
        self.columns([])
        
        # add to main menu
        uikit.add_menu([parent.channelmenuitems], self.meta["title"], lambda w: parent.channel_switch_by_name(self.module) or 1)

    # Just wraps uikit.columns() to retain liststore, rowmap and pix_entry
    def columns(self, entries=None, pix_entry=False, typecast=0):
        self._ls, self._rowmap, self._pix_entry = uikit.columns(self.gtk_list, self.datamap, entries)

    # Statusbar stub (defers to parent/main window, if in GUI mode)
    def status(self, *args, **kw):
        if self.parent: self.parent.status(*args, **kw)
        else: log.INFO("status():", *v)


        
    #--------------------- streams/model data accesss ---------------------------

    # traverse category TreeModel to set current, expand parent nodes
    def select_current(self, name):
        log.UI("reselect .current category in treelist:", name)
        model = self.gtk_cat.get_model()
           # [Gtk3] Warning: g_object_ref_sink: assertion 'object->ref_count >= 1' failed
           # ERROR:../../gi/pygobject.c:688:pygobject_register_wrapper: assertion failed: (gself->obj->ref_count >= 1)
        iter = model.get_iter_first()
        self.iter_cats(name, model, iter)

    # iterate over children to find current category        
    def iter_cats(self, name, model, iter):
        while iter:
            val = model.get_value(iter, 0)
            if val == name:
                #log.UI("FOUND CATEGORY", name, "→select")
                self.gtk_cat.get_selection().select_iter(iter)
                self.gtk_cat.set_cursor(model.get_path(iter))
                self.gtk_cat.scroll_to_cell(model.get_path(iter), None)
                return True
            if model.iter_has_child(iter):
                found = self.iter_cats(name, model, model.iter_children(iter))
                if found:
                    self.gtk_cat.expand_row(model.get_path(iter), 0)
                    return True
            iter = model.iter_next(iter)
        
    # selected category
    def currentcat(self):
        (model, iter) = self.gtk_cat.get_selection().get_selected()
        if (type(iter) == gtk.TreeIter):
            self.current = model.get_value(iter, 0)
        return self.current
        
    # Get list of stations in current category
    def stations(self):
        return self.streams.get(self.current, [])

    # Convert ListStore iter to row number
    def rowno(self):
        (model, iter) = self.model_iter()
        return model.get_path(iter)[0]

    # Return ListStore object and Iterator for currently selected row in gtk.TreeView station list
    def model_iter(self):
        return self.gtk_list.get_selection().get_selected()

    # Currently selected entry in stations list, return complete data dict
    def row(self):
        return self.stations() [self.rowno()]
        
    # Fetches a single varname from currently selected station entry
    def selected(self, name="url"):
        return self.row().get(name)
    
    # Inject status icon into currently selected row (used by main.bookmark() call)
    def row_icon(self, gtkIcon = gtk.STOCK_ABOUT):
        try:
            # Updates gtk_list store, set icon in current display.
            # Since it is used by bookmarks, would be reshown with next display() anyhow,
            # and there's no need to invalidate the ls cache, because that's referenced by model anyhow.
            (model,iter) = self.model_iter()
            model.set_value(iter, 0, gtkIcon)
        except Exception as e:
            log.ERR_UIKIT("Couldn't set row_icon()", e)

    

    #------------------------ base implementations -----------------------------

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
        # catmap (optional)
        cache = conf.load("cache/catmap_" + self.module)
        if (cache):
            self.catmap = cache
        pass

        
    # make private copy of .datamap and modify field (title= only ATM)
    def update_datamap(self, search="name", title=None):
        if self.datamap == GenericChannel.datamap:
            self.datamap = copy.deepcopy(self.datamap)
        for i,row in enumerate(self.datamap):
            if row[2][0] == search:
                row[0] = title


    # Called on switching genre/category.
    # Either fetches new stream data, or displays list from cache.
    def load(self, category, force=False, y=None):

        # called to early
        if not category:
            log.ERR("load(None)")
            return
        self.current = category

        # get data from cache or download
        if force or not category in self.streams:
            log.PROC("load", "update_streams")
            self.status("Updating streams...")
            self.status(-0.1)
            if category == "empty":
                new_streams = self.empty_stub
            else:
                new_streams = self.update_streams(category)
  
            if new_streams:
                # check and modify entry;
                # assert that title and url are present
                modified = []
                for row in new_streams:
                    if len(set(["", None]) & set([row.get("title"), row.get("url")])):
                        continue
                    try:
                        modified.append( self.postprocess(row) )
                    except Exception as e:
                        log.DATA(e, "Missing title or url. Postprocessing failed:", row)
                new_streams = modified
  
                # don't lose forgotten streams
                if conf.retain_deleted:
                   self.streams[category] = new_streams + self.deleted_streams(new_streams, self.streams.get(category,[]))
                else:
                   self.streams[category] = new_streams
  
                # save in cache
                self.save()
  
            else:
                # parse error
                self.status("Category parsed empty.")
                self.streams[category] = self.nothing_found
                log.INFO("Oooops, parser returned nothing for category " + category)
                
        # Update treeview/model (if category is still selected)
        if self.current == category:
            log.UI("load() → uikit.columns({}.streams[{}])".format(self.module, category), [inspect.stack()[x][3] for x in range(1,5)])
            uikit.do(self.columns, self.prepare(self.streams[category]))
            if y:
                uikit.do(self.gtk_list.scroll_to_point, 0, y + 1)   # scroll to previous position, +1 px, because
                # somehow Gtk.TreeView else stumbles over itself when scrolling to the same position the 2nd time

        # unset statusbar
        self.status()

        
    # store current streams data
    def save(self):
        conf.save("cache/" + self.module, self.streams, gz=1)


    # called occasionally while retrieving and parsing
    def update_streams_partially_done(self, entries):
        if gtk_ver == 3 and not conf.nothreads:
            pass
        else:  # kills Gtk3 too easily
            uikit.do(self.columns, entries)

        
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
    #
    #  - favourite icon
    #  - or deleted icon
    #
    def prepare(self, streams):
        for i,row in enumerate(streams):
            # state icon: bookmark star
            if (conf.show_bookmarks and "bookmarks" in self.parent.channels and self.parent.bookmarks.is_in(streams[i].get("url", "file:///tmp/none"))):
                streams[i]["favourite"] = 1
            
            # state icon: INFO or DELETE
            if (not row.get("state")):
                if row.get("favourite"):
                    streams[i]["state"] = gtk.STOCK_ABOUT
                if conf.retain_deleted and row.get("deleted"):
                    streams[i]["state"] = gtk.STOCK_DELETE
            
            # Favicons? construct local cache filename, basically reimplements favicon.row_to_fn()
            if conf.show_favicons and "favicon" in self.parent.features:
                url = row.get("img") or row.get("homepage")
                if url:
                    # Normalize by stripping proto:// and non-alphanumeric chars
                    url = re.sub("[^\w._-]", "_", re.sub("^\w+://|/$", "", url.lower()))
                    streams[i]["favicon"] = "{}/icons/{}.png".format(conf.dir, url)

        return streams


    # data preparations directly after reload
    #
    # - drop shoutcast homepage links
    # - or find homepage name in title
    #
    def postprocess(self, row):
        # deduce homepage URLs from title
        # by looking for www.xyz.com domain names
        if not row.get("homepage"):
            url = self.rx_www_url.search(row.get("title", ""))
            if url:
                url = url.group(0).lower().replace(" ", "")
                url = (url if url.find("www.") == 0 else "www."+url)
                row["homepage"] = ahttp.fix_url(url)
        return row

        

    # reload current stream from web directory
    def reload(self):
        self.load(self.current, force=1)
    def switch(self):
        self.load(self.current, force=0)
    
    # update streams pane if currently selected (used by bookmarks.links channel)
    def reload_if_current(self, category):
        if self.current == category:
            self.reload()
    
        
    # display .current category, once notebook/channel tab is first opened
    def first_show(self):

        # Already processed
        if (self.shown == 55555):
            return
        log.PROC(self.module, "→ first_show()", ", current=", self.current, ", categories=", len(self.categories))
    
        # if category tree is empty, initialize it
        if not self.categories:
            log.PROC(self.module, "→ first_show() → reload_categories()");
            try:
                self.reload_categories()
            except:
                log.ERR("HTTP error or extraction failure.")
                self.categories = ["empty"]
            self.display_categories()

        # Select first category
        if not self.current:
            log.STAT(self.module, "→ first_show(); use first category as current =", self.current)
            self.current = self.str_from_struct(self.categories) or None

        # put selection/cursor on last position
        if True:
            uikit.do(self.select_current, self.current)

        # Show current category in any case
        log.UI(self.module, "→ first_show(); station list → load(", self.current, ")")
        self.load(self.current)
            
        # Invoke only once
        self.shown = 55555


    # Retrieve first list value, or key from dict (-- used to get first category on init)
    def str_from_struct(self, d):
        if isinstance(d, (str)):
            return d
        elif isinstance(d, (dict)):
            return self.str_from_struct(d.keys()) or self.str_from_struct(d.values())
        elif isinstance(d, (list, tuple)):
            return d[0] if len(d) else None


    # update categories, save, and display                
    def reload_categories(self):
    
        # get data and save
        self.update_categories()
        if self.categories:
            conf.save("cache/categories_"+self.module, self.categories)
        if self.catmap:
            conf.save("cache/catmap_" + self.module, self.catmap);

        # display outside of this non-main thread
        uikit.do(self.display_categories)


    # insert content into gtk category list
    def display_categories(self):
        log.UI("{}.display_categories(), uikit.tree(#{}), expand_all(#<20), select_current(={})".format(self.module, len(self.categories), self.current))
    
        # rebuild gtk.TreeView
        uikit.tree(self.gtk_cat, self.categories, title="Category", icon=gtk.STOCK_OPEN)

        # if it's a short list of categories, there's probably subfolders
        if len(self.categories) < 20:
            self.gtk_cat.expand_all()
            
        # Select last .current or any first element
        if self.current:
            uikit.do(self.select_current, self.current)
            #self.currentcat()
        #else: self.gtk_cat.get_selection().select_path("0") #set_cursor

            

    
    # Insert/append new station rows - used by importing/drag'n'drop plugins
    def insert_rows(self, rows, y=None):
        streams = self.streams[self.current]
        tv = self.gtk_list
        
        # Inserting at correct row requires deducing index from dnd `y` position
        if y is not None:
            i_pos = (tv.get_path_at_pos(10, y) or [[len(streams) + 1]])[0][0]
            for row in rows:
                streams.insert(i_pos - 1, row)
                i_pos = i_pos + 1
        else:
            streams += rows

        # Now appending to the liststore directly would be even nicer
        y = int(tv.get_vadjustment().get_value())
        self.load(self.current, y=y)





    #--------------------------- actions ---------------------------------

    # Invoke action.play() for current station.
    # Can be overridden to provide channel-specific "play" alternative
    def play(self):
        row = self.row()
        if row and "url" in row:
            # playlist and audio type
            audioformat = row.get("format", self.audioformat)
            listformat = row.get("listformat", self.listformat)
            # invoke audio player
            action.play(row, audioformat, listformat)
        else:
            self.status("No station selected for playing.")
        return row

    # Start streamripper/youtube-dl/etc
    def record(self):
        row = self.row()
        if row and "url" in row:
            audioformat = row.get("format", self.audioformat)
            listformat = row.get("listformat", self.listformat)
            action.record(row, audioformat, listformat)
        return row



    #--------------------------- utility functions -----------------------

    

        
    # convert audio format nick/shortnames to mime types, e.g. "OGG" to "audio/ogg"
    def mime_fmt(self, s):
        # clean string
        s = s.lower().strip()
        # rename
        map = {
            "audio/mp3":"audio/mpeg",  # Note the real mime type is /mpeg, but /mp3 is more understandable in the GUI
            "ogg":"ogg", "ogm":"ogg", "xiph":"ogg", "vorbis":"ogg", "vnd.xiph.vorbis":"ogg",
            "mp3":"mpeg", "mp":"mpeg", "mp2":"mpeg", "mpc":"mpeg", "mps":"mpeg",
            "aac+":"aac", "aacp":"aac",
            "realaudio":"x-pn-realaudio", "real":"x-pn-realaudio", "ra":"x-pn-realaudio", "ram":"x-pn-realaudio", "rm":"x-pn-realaudio",
            # yes, we do video
            "flv":"video/flv", "mp4":"video/mp4",
        }
        #map.update(action.listfmt_t)   # list type formats (.m3u .pls and .xspf)
        if map.get(s):
            s = map[s]
        # add prefix:
        if s.find("/") < 1:
            s = "audio/" + s
        #
        return s
    








# channel plugin without glade-pre-defined notebook tab
#
class ChannelPlugin(GenericChannel):

    module = "abstract"

    def gui(self, parent):

        if not parent:
            return

        module = self.__class__.__name__
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
        uikit.tree_column(tv1, "Category")
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
        pixbuf = None
        if "png" in self.meta:
            pixbuf = uikit.pixbuf(self.meta["png"])
        else:
            png = get_data("channels/" + self.module + ".png")
            pixbuf = uikit.pixbuf(png)
        if pixbuf:
            icon = gtk.image_new_from_pixbuf(pixbuf)
        else:
            icon = gtk.image_new_from_stock(gtk.STOCK_DIRECTORY, size=1)
        label = gtk.HBox()
        label.pack_start(icon, expand=False, fill=True)
        l = gtk.Label(self.meta.get("title", self.module))
        if self.meta.get("color"):
            l = uikit.bg(l, self.meta["color"])
        label.pack_start(l, expand=True, fill=True)
            
        # pack it into an event container to catch double-clicks
        ev_label = gtk.EventBox()
        ev_label.add(label)
        ev_label.connect('event', parent.on_homepage_channel_clicked)
        plain_label = gtk.Label(self.module)

        # to widgets
        self.gtk_cat = tv1
        parent.widgets[module + "_cat"] = tv1
        self.gtk_list = tv2
        parent.widgets[module + "_list"] = tv2
        ev_label.show_all()
        vbox.show_all()
        parent.widgets["v_" + module] = vbox
        parent.widgets["c_" + module] = ev_label
        tv2.connect('button-press-event', parent.station_context_menu)


        # try to initialize superclass now, before adding to channel tabs
        GenericChannel.gui(self, parent)

        # add notebook tab
        tab = parent.notebook_channels.insert_page_menu(vbox, ev_label, plain_label, -1)
        parent.notebook_channels.set_tab_reorderable(vbox, True)



# WORKAROUND for direct channel module imports,
# eases instantiations without GUI a little,
# reducing module dependencies (conf. / ahttp. / channels. / parent.) would be better
def stub_parent(object):
    def __setattr__(self, name, value):
        pass
    def __getattr__(self, name):
        return lambda *x: None
    def status(self, *x):
        pass


# Decorator
def use_rx(func):
    def try_both(*args, **kwargs):
        for method, use_rx in [("RX", not conf.pyquery), ("PQ", conf.pyquery)]:
            try:
                log.STAT(method)
                return func(*args, use_rx=not conf.pyquery, **kwargs)
            except Exception as e:
                log.ERR("{} extraction failed:".format(method), e)
                continue
        return []
    return try_both



#---------------- utility functions -------------------
# Used by raw page extraction in channel modules


# Strip html <tags> from string
def strip_tags(s):
    return re.sub("<.+?>", "", s)

# remove SGML/XML entities
def entity_decode(str):
    return re.sub('&(#?(x?))(\w+);', _entity, str)
def _entity(sym):
    num, hex, name = sym.groups()
    if hex:
        return unichr(int(name, base=16))
    elif num:
        return unichr(int(name))
    else:
        return unichr(htmlentitydefs_n2cp[name])

# Nay for the Py3 raft
htmlentitydefs_n2cp = {'aring': 229, 'gt': 62, 'sup': 8835, 'Ntilde': 209, 'upsih': 978, 'Yacute': 221,
'Atilde': 195, 'radic': 8730, 'otimes': 8855, 'aelig': 230, 'Psi': 936, 'Uuml': 220, 'Epsilon': 917, 'Icirc':
206, 'Eacute': 201, 'Lambda': 923, 'Prime': 8243, 'Kappa': 922, 'sigmaf': 962, 'lrm': 8206, 'cedil': 184,
'kappa': 954, 'AElig': 198, 'prime': 8242, 'Tau': 932, 'lceil': 8968, 'dArr': 8659, 'ge': 8805, 'sdot': 8901,
'lfloor': 8970, 'lArr': 8656, 'Auml': 196, 'brvbar': 166, 'Otilde': 213, 'Theta': 920, 'Pi': 928, 'OElig': 338,
'Scaron': 352, 'egrave': 232, 'sub': 8834, 'iexcl': 161, 'ordf': 170, 'sum': 8721, 'ntilde': 241, 'atilde':
227, 'theta': 952, 'nsub': 8836, 'hArr': 8660, 'Oslash': 216, 'THORN': 222, 'yuml': 255, 'Mu': 924, 'thinsp':
8201, 'ecirc': 234, 'bdquo': 8222, 'Aring': 197, 'nabla': 8711, 'permil': 8240, 'Ugrave': 217, 'eta': 951,
'Agrave': 192, 'forall': 8704, 'eth': 240, 'rceil': 8969, 'iuml': 239, 'Egrave': 200, 'divide': 247, 'igrave':
236, 'otilde': 245, 'pound': 163, 'frasl': 8260, 'ETH': 208, 'lowast': 8727, 'chi': 967, 'Aacute': 193, 'cent':
162, 'Beta': 914, 'perp': 8869, 'there4': 8756, 'pi': 960, 'empty': 8709, 'euml': 235, 'notin': 8713, 'uuml':
252, 'icirc': 238, 'bull': 8226, 'upsilon': 965, 'Oacute': 211, 'ensp': 8194, 'ccedil': 231, 'cap': 8745, 'mu':
956, 'deg': 176, 'tau': 964, 'emsp': 8195, 'hellip': 8230, 'ucirc': 251, 'ugrave': 249, 'cong': 8773, 'Iota':
921, 'quot': 34, 'rarr': 8594, 'Rho': 929, 'uacute': 250, 'acirc': 226, 'sim': 8764, 'phi': 966, 'diams': 9830,
'Euml': 203, 'Ccedil': 199, 'Eta': 919, 'Gamma': 915, 'euro': 8364, 'thetasym': 977, 'sect': 167, 'ldquo':
8220, 'hearts': 9829, 'oacute': 243, 'zwnj': 8204, 'yen': 165, 'ograve': 242, 'Chi': 935, 'trade': 8482, 'xi':
958, 'nbsp': 160, 'tilde': 732, 'lsaquo': 8249, 'oelig': 339, 'equiv': 8801, 'le': 8804, 'auml': 228, 'cup':
8746, 'Yuml': 376, 'lt': 60, 'Upsilon': 933, 'ndash': 8211, 'yacute': 253, 'real': 8476, 'psi': 968, 'rsaquo':
8250, 'darr': 8595, 'Alpha': 913, 'not': 172, 'amp': 38, 'oslash': 248, 'acute': 180, 'zwj': 8205, 'laquo':
171, 'rdquo': 8221, 'Igrave': 204, 'micro': 181, 'shy': 173, 'supe': 8839, 'szlig': 223, 'clubs': 9827,
'agrave': 224, 'Ocirc': 212, 'harr': 8596, 'larr': 8592, 'frac12': 189, 'prop': 8733, 'circ': 710, 'ocirc':
244, 'asymp': 8776, 'uml': 168, 'prod': 8719, 'reg': 174, 'rlm': 8207, 'infin': 8734, 'Sigma': 931, 'mdash':
8212, 'uarr': 8593, 'times': 215, 'rArr': 8658, 'or': 8744, 'gamma': 947, 'lambda': 955, 'rang': 9002, 'sup3':
179, 'dagger': 8224, 'Ouml': 214, 'image': 8465, 'alefsym': 8501, 'sube': 8838, 'alpha': 945, 'Nu': 925,
'plusmn': 177, 'sup1': 185, 'sup2': 178, 'frac34': 190, 'oline': 8254, 'Delta': 916, 'loz': 9674, 'iota': 953,
'iacute': 237, 'para': 182, 'ordm': 186, 'epsilon': 949, 'weierp': 8472, 'part': 8706, 'delta': 948, 'omicron':
959, 'copy': 169, 'Iuml': 207, 'Xi': 926, 'Dagger': 8225, 'Ograve': 210, 'Ucirc': 219, 'scaron': 353, 'lsquo':
8216, 'isin': 8712, 'Zeta': 918, 'minus': 8722, 'and': 8743, 'ang': 8736, 'curren': 164, 'int': 8747, 'rfloor':
8971, 'crarr': 8629, 'exist': 8707, 'oplus': 8853, 'Acirc': 194, 'piv': 982, 'ni': 8715, 'Phi': 934, 'Iacute':
205, 'Uacute': 218, 'Omicron': 927, 'ne': 8800, 'iquest': 191, 'sbquo': 8218, 'Ecirc': 202, 'zeta': 950,
'Omega': 937, 'nu': 957, 'macr': 175, 'frac14': 188, 'aacute': 225, 'uArr': 8657, 'beta': 946, 'fnof': 402,
'rho': 961, 'eacute': 233, 'omega': 969, 'middot': 183, 'lang': 9001, 'spades': 9824, 'rsquo': 8217, 'thorn':
254, 'ouml': 246, 'raquo': 187, 'sigma': 963, 'apos': 39}


# Extracts integer from string
def to_int(s):
    i = re.findall("\d+", s) or [0]
    return int(i[0])

# Strip newlines
rx_spc = re.compile("\s+")
def nl(str):
    return rx_spc.sub(" ", str).strip()

# Combine html tag, escapes and whitespace cleanup
def unhtml(str):
    return nl(entity_decode(strip_tags(str)))


