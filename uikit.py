# encoding: UTF-8
# api: python
# type: functions
# title: uikit helper functions
# description: simplify usage of some gtk widgets
# version: 1.9
# author: mario
# license: public domain
#
# Wrappers around gtk methods. The TreeView method .columns() allows
# to fill a treeview. It adds columns and data rows with a mapping
# dictionary (which specifies many options and data positions).
#
# The .tree() method is a trimmed-down variant of that, creates a
# single column, but has threaded entries.
#
# With the methodes .app_state() and .app_restore() named gtk widgets
# can be queried for attributes. The methods return a saveable dict,
# which contain current layout options for a few Widget types. Saving
# and restoring must be handled elsewhere.


# debug
from config import *

# system
import os.path
import copy
import sys
import re
import base64
import inspect
from compat2and3 import unicode, xrange, PY3, gzip_decode


# gtk version (2=gtk2, 3=gtk3, 7=tk;)
ver = 2
# if running on Python3 or with commandline flag
if PY3 or conf.args.gtk3:
    ver = 3
# load gtk modules
if ver==3:
    from gi import pygtkcompat as pygtk
    pygtk.enable() 
    pygtk.enable_gtk(version='3.0')
    from gi.repository import Gtk as gtk
    from gi.repository import GObject as gobject
    from gi.repository import GdkPixbuf
    log.STAT(gtk)
    log.STAT(gobject)
else:
    import pygtk
    import gtk
    import gobject
    GdkPixbuf = gtk.gdk

# prepare gtkbuilder data
ui_xml = get_data("gtk3.xml.gz", decode=True, gz=True) #or get_data("gtk3.xml", decode=True)
if ver == 2:
    ui_xml = ui_xml.replace('version="3.0"', 'version="2.16"')


# simplified gtk constructors               ---------------------------------------------
class uikit:


         
    #-- fill a treeview
    #
    # Adds treeviewcolumns/cellrenderers and liststore from a data dictionary.
    # Its datamap and the table contents can be supplied in one or two steps.
    # When new data gets applied, the columns aren't recreated.
    #
    # The columns are created according to the datamap, which describes cell
    # mapping and layout. Columns can have multiple cellrenderers, but usually
    # there is a direct mapping to a data source key from entries.
    #
    # datamap = [  #  title   width    dict-key    type,  renderer,  attrs  
    #               ["Name",   150,  ["titlerow",   str,    "text",    {} ]  ],
    #               [False,     0,   ["interndat",  int,     None,     {} ]  ],
    #               ["Desc",   200,  ["descriptn",  str,    "text",    {} ],  ["icon",str,"pixbuf",{}]  ],
    #
    # An according entries list then would contain a dictionary for each row:
    #   entries = [ {"titlerow":"first", "interndat":123}, {"titlerow":"..."}, ]
    # Keys not mentioned in the datamap get ignored, and defaults are applied
    # for missing cols. All values must already be in the correct type however.
    #
    @staticmethod
    def columns(widget, datamap=[], entries=None, show_favicons=True, pix_entry=False, fixed_size=24):

        # create treeviewcolumns?
        if not widget.get_column(0):
            # loop through titles
            datapos = 0
            for n_col, desc in enumerate(datamap):

                # check for title
                if not isinstance(desc[0], str):
                    datapos += 1  # if there is none, this is just an undisplayed data column
                    continue
                # new tvcolumn
                col = gtk.TreeViewColumn(desc[0])  # title
                col.set_resizable(True)
                # width
                if (desc[1] > 0):
                    col.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
                    col.set_fixed_width(desc[1])

                # loop through cells
                for var in range(2, len(desc)):
                    cell = desc[var]
                    # cell renderer
                    if (cell[2] == "pixbuf"):
                        rend = gtk.CellRendererPixbuf()  # img cell
                        # stock icons
                        if cell[1] == str:  # only match for literal `str`
                            cell[3]["stock_id"] = datapos
                            expand = False
                        # pixbufs
                        else:
                            pix_entry = datapos
                            cell[3]["pixbuf"] = datapos
                            if fixed_size:
                                if not isinstance(fixed_size, list):
                                    fixed_size = [fixed_size, fixed_size]
                                rend.set_fixed_size(*fixed_size)
                    else:
                        rend = gtk.CellRendererText()    # text cell
                        cell[3]["text"] = datapos
                        #col.set_sort_column_id(datapos)  # only on textual cells

                    # attach cell to column
                    col.pack_end(rend, expand=cell[3].get("expand",True))
                    # apply attributes
                    for attr,val in list(cell[3].items()):
                        col.add_attribute(rend, attr, val)
                    # next
                    datapos += 1
                    #log.INFO(cell, len(cell))

                # add column to treeview
                #log.E(col)
                widget.append_column(col)
           
        # add data?
        if (entries is not None):
            #- expand datamap
            vartypes = []  #(str, str, bool, str, int, int, gtk.gdk.Pixbuf, str, int)
            rowmap = []    #["title", "desc", "bookmarked", "name", "count", "max", "img", ...]
            for desc in datamap:
                for var in xrange(2, len(desc)):
                    vartypes.append(desc[var][1])  # content types
                    rowmap.append(desc[var][0])    # dict{} column keys in entries[] list
            # create gtk array storage
            #log.UI(vartypes, len(vartypes))
            ls = gtk.ListStore(*vartypes)   # could be a TreeStore, too
            #log.DATA(rowmap, len(rowmap))
 
            # prepare for missing values, and special variable types
            defaults = {
                str: "",
                unicode: "",
                bool: False,
                int: 0,
                gtk.gdk.Pixbuf: empty_pixbuf
            }
            if gtk.gdk.Pixbuf in vartypes:
                pix_entry = vartypes.index(gtk.gdk.Pixbuf) 
            
            # sort data into gtk liststore array
            for row in entries:

                # preset some values if absent
                row.setdefault("deleted", False)
                row.setdefault("search_col", "#ffffff")
                row.setdefault("search_set", False)

                # generate ordered list from dictionary, using rowmap association
                row = [   row.get( skey , defaults[vartypes[i]] )   for i,skey   in enumerate(rowmap)   ]

                # map Python2 unicode to str
                row = [ str(value) if type(value) is unicode else value  for value in row ]

                # autotransform string -> gtk image object
                if (pix_entry and type(row[pix_entry]) == str):
                    pix = None
                    try:
                        if show_favicons and os.path.exists(row[pix_entry]):
                            pix = gtk.gdk.pixbuf_new_from_file(row[pix_entry])
                    except Exception as e:
                        log.ERR("uikik.columns: Pixbuf fail,", e)
                    row[pix_entry] = pix or defaults[gtk.gdk.Pixbuf]

                try:
                    # add
                    ls.append(row)   # had to be adapted for real TreeStore (would require additional input for grouping/level/parents)

                except:
                    # brute-force typecast
                    ls.append( [va  if ty==gtk.gdk.Pixbuf  else ty(va)   for va,ty in zip(row,vartypes)]  )

            #if entries:
            #     log.ROWS(row, len(row))
            
            # apply array to widget
            widget.set_model(ls)
            return ls, rowmap, pix_entry
            
        pass




    #-- treeview for categories
    #
    # simple two-level treeview display in one column
    # with entries = [main,[sub,sub], title,[...],...]
    #
    @staticmethod     
    def tree(widget, entries, title="category", icon=gtk.STOCK_DIRECTORY):

        # list types
        ls = gtk.TreeStore(str, str)
        #log.DATA(".tree", entries)

        # add entries
        main = None
        for entry in entries:
            if isinstance(entry, (str,unicode)):
                main = ls.append(None, [str(entry), icon])
            else:
                for sub_title in entry:
                    ls.append(main, [str(sub_title), icon])

        # finalize
        widget.set_model(ls)
        widget.set_search_column(0)
        #tvcolumn.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        #tvcolumn.set_fixed_width(125])
        #widget.expand_all()
        #widget.expand_row("3", False)
        #print(widget.row_expanded("3"))
        return ls


    @staticmethod
    def tree_column(widget, title="Category"):
        # just one column
        tvcolumn = gtk.TreeViewColumn(title);
        widget.append_column(tvcolumn)

        # inner display: icon & string
        pix = gtk.CellRendererPixbuf()
        txt = gtk.CellRendererText()

        # position
        tvcolumn.pack_start(pix, expand=False)
        tvcolumn.pack_end(txt, expand=True)

        # select array content source in treestore
        tvcolumn.add_attribute(pix, "stock_id", 1)
        tvcolumn.add_attribute(txt, "text", 0)
        tvcolumn.set_sort_column_id(0)



    #-- save window size and widget properties
    #
    # needs a list of widgetnames
    # e.g. pickle.dump(uikit.app_state(...), open(os.environ["HOME"]+"/.config/app_winstate", "w"))
    #
    @staticmethod
    def app_state(wTree, widgetnames=["window1", "treeview2", "vbox17"]):
        r = {} # restore array
        for wn in widgetnames:
            r[wn] = {}
            w = wTree.get_widget(wn)
            t = type(w)
        #    print(wn, w, t)
            # extract different information from individual widget types
            if t == gtk.Window:
                r[wn]["size"] = list(w.get_size())
                #print("WINDOW SIZE", list(w.get_size()), r[wn])
            if t == gtk.Widget:
                r[wn]["name"] = w.get_name()
            # gtk.TreeView
            if t == gtk.TreeView:
                r[wn]["columns:width"] = []
                for col in w.get_columns():
                    r[wn]["columns:width"].append( col.get_width() )
                # - Rows
                r[wn]["rows:expanded"] = []
                for i in xrange(0,50):
                    if w.row_expanded(treepath(i)):   # Gtk.TreePath for Gtk3
                        r[wn]["rows:expanded"].append(i)
                # - selected
                (model, paths) = w.get_selection().get_selected_rows()
                if paths:
                    r[wn]["row:selected"] = treepath_to_str(paths[0])
            # gtk.Toolbar
            if t == gtk.Toolbar:
                r[wn]["icon_size"] = int(w.get_icon_size())
                r[wn]["style"] = int(w.get_style())
            # gtk.Notebook
            if t == gtk.Notebook:
                r[wn]["tab_pos"] = int(w.get_tab_pos())
                r[wn]["tab_order"] = [w.get_menu_label_text(w.get_nth_page(i)) for i in xrange(0, w.get_n_pages())]
                r[wn]["tab_current"] = w.get_menu_label_text(w.get_nth_page(w.get_current_page()))
        #print(r)
        return r

    gtk_position_type_enum = [gtk.POS_LEFT, gtk.POS_RIGHT, gtk.POS_TOP, gtk.POS_BOTTOM]


    #-- restore window and widget properties
    #
    # requires only the previously saved widget state dict
    #
    @staticmethod
    def app_restore(wTree, r=None):
        for wn in r.keys():  # widgetnames
            w = wTree.get_widget(wn)
            if (not w):
                continue
            t = type(w)
            for method,args in r[wn].items():
                # gtk.Window
                if method == "size":
                    w.resize(args[0], args[1])
                # gtk.TreeView
                if method == "columns:width":
                    for i,col in enumerate(w.get_columns()):
                        if (i < len(args)):
                            col.set_fixed_width(args[i])
                #  - Rows
                if method == "rows:expanded":
                    w.collapse_all()
                    for i in args:
                        w.expand_row(treepath(i), False)
                #  - selected
              #  if method == "row:selected":
              #      w.get_selection().select_path(treepath(args))
                # gtk.Toolbar
                if method == "icon_size":
                    w.set_icon_size(args)
                if method == "style":
                    w.set_style(args)
                # gtk.Notebook
                if method == "tab_pos":
                    w.set_tab_pos(r[wn]["tab_pos"])
                if method == "tab_order":
                    tab_current = r[wn].get("tab_current")
                    for pos,ord_tabname in enumerate(args):
                        # compare current label list on each reordering round
                        for i in range(0, w.get_n_pages()):
                            w_tab = w.get_nth_page(i)
                            w_label = w.get_menu_label_text(w_tab)
                            if w_label == ord_tabname:
                                w.reorder_child(w_tab, pos)
                            if tab_current == ord_tabname:
                                w.set_current_page(pos)
        pass



    #-- Save-As dialog
    #
    @staticmethod
    def save_file(title="Save As", parent=None, fn="", formats=[("*.pls", "*.pls"), ("*.xspf", "*.xpsf"), ("*.m3u", "*.m3u"), ("*.jspf", "*.jspf"), ("*.asx", "*.asx"), ("*.json", "*.json"), ("*.smil", "*.smil"), ("*.desktop", "*.desktop"), ("*","*")]):

        # With overwrite confirmation
        c = gtk.FileChooserDialog(title, parent, action=gtk.FILE_CHOOSER_ACTION_SAVE,
                buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        c.set_do_overwrite_confirmation(True)

        # Params
        if fn:
            c.set_current_name(fn)
            fn = ""
        for fname,ftype in formats:
            f = gtk.FileFilter()
            f.set_name(fname)
            f.add_pattern(ftype)
            c.add_filter(f)
        # Yes, that's how to retrieve signals for changed filter selections
        try:
            filterbox = c.get_children()[0].get_children()[0]
            filterbox.connect("notify::filter", lambda *w: uikit.save_file_filterchange(c))
        except: pass
        
        # Filter handlers don't work either.

        # Display and wait
        if c.run():
            fn = c.get_filename()  # return filaname
        c.destroy()
        return fn

    # Callback for changed FileFilter, updates current filename extension
    @staticmethod
    def save_file_filterchange(c):
        fn, ext = c.get_filename(), c.get_filter().get_name()
        if fn and ext:
            fn = os.path.basename(fn)
            c.set_current_name(re.sub(r"\.(m3u|pls|xspf|jspf|asx|json|smil|desktop|url|wpl)8?$", ext.strip("*"), fn))
        
    

    # Spool gtk update calls from non-main threads (optional immediate=1 flag to run task next, not last)
    @staticmethod
    def do(callback, *args, **kwargs):
        name = inspect.getsource(callback).strip() if callback.__name__=='<lambda>' else str(callback)
        if kwargs.get("immediate"):
            del kwargs["immediate"]
            pos = 0
        else:
            pos = len(uikit.idle_tasks)
        # Run callback right away
        if uikit.in_idle or conf.nothreads:
            log.UIKIT_RUN_NOW(name)
            callback(*args, **kwargs)
        # Spool them for Gtk idle handling
        else:
            #log.UIKIT_SPOOL(name)
            uikit.idle_tasks.insert(pos, [lambda: callback(*args, **kwargs), name])
            gobject.idle_add(uikit.idle_do)
    
    # Collect tasks to perform in gtk.main loop
    idle_tasks = []
    in_idle = False
    
    # Execute UI updating tasks in order
    @staticmethod
    def idle_do():
        uikit.in_idle = True
        if uikit.idle_tasks:
            task, name = uikit.idle_tasks.pop(0)
            log.UIKIT_EXEC(name)
            task()
        uikit.in_idle = False
        return len(uikit.idle_tasks) > 0
        


    # Adds background color to widget,
    # eventually wraps it into a gtk.EventBox, if it needs a container
    @staticmethod
    def bg(w, color="", where=["bg"], wrap=1):
        """ this method should be called after widget creation, and before .add()ing it to container """
        if color:
            # wrap unstylable widgets into EventBox
            if wrap and not isinstance(w, (gtk.Window, gtk.EventBox)):
                wrap = gtk.EventBox()
                wrap.add(w)
                w = wrap
            # copy style object, modify settings
            try: # Gtk2
                c = w.get_colormap().alloc_color(color)
            except: # Gtk3
                p, c = gtk.gdk.Color.parse(color)
            for state in (gtk.STATE_NORMAL, gtk.STATE_SELECTED, gtk.STATE_ACTIVE):
                w.modify_bg(state, c)
        # return modified or wrapped widget
        return w


    # Create GtkLabel
    @staticmethod
    def label(text, size=305, markup=0):
        label = gtk.Label(text)
        if markup:
            label.set_markup(text)
        #######label.set_property("visible", True)
        label.set_line_wrap(True) 
        label.set_size_request(size, -1)
        return label

    # Wrap two widgets in horizontal box
    @staticmethod
    def hbox(w1, w2, exr=True):
        b = gtk.HBox(homogeneous=False, spacing=5)
        ######b.set_property("visible", True)
        b.pack_start(w1, expand=not exr, fill=not exr)
        b.pack_start(w2, expand=exr, fill=exr)
        return b


    # Wrap entries/checkboxes with extra label, background, images, etc.
    @staticmethod
    def wrap(widgetstore=None, id=None, w=None, label=None, color=None, image=None, align=1, label_size=305, label_markup=0):
        if id:
            widgetstore[id] = w
        if label:
            if type(w) is gtk.Entry:
                w.set_width_chars(11)
            w = uikit.hbox(w, uikit.label(label, size=label_size, markup=label_markup))
        if image:
            pix = gtk.image_new_from_pixbuf(uikit.pixbuf(image))
            if pix:
                w = uikit.hbox(w, pix, exr=False)
        if color:
            w = uikit.bg(w, color)
        if align:
            a = gtk.Alignment()
            a.set_padding(0, 0, align, 0)
            a.add(w)
            w = a
        w.show_all()
        return w
    
    
    # Config win table (editable dictionary, two columns w/ executable indicator pixbuf)
    @staticmethod
    def config_treeview(opt, columns=["Icon", "Command"]):
        lno = len(columns)
        if lno == 2:
            liststore = gtk.ListStore(str, str, str)
        else:
            liststore = gtk.ListStore(*[str for i in range(0, lno)])
        w = gtk.TreeView(liststore)
        # two text columns and renderers
        for i in range(0, lno):
            c = gtk.TreeViewColumn(columns[i])
            c.set_resizable(True)
            c.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            c.set_fixed_width(int(430/lno))
            r = gtk.CellRendererText()
            c.pack_end(r, expand=True)
            r.set_property("editable", True)
            r.connect("edited", uikit.liststore_edit, (liststore, i))
            c.add_attribute(r, "text", i)
            #c.add_attribute(r, "editable", 2)
            w.append_column(c)
        # add pixbuf holder to last column
        if lno < 3:
            r = gtk.CellRendererPixbuf()
            c.pack_start(r, expand=False)
            c.add_attribute(r, "stock_id", 2)
        w.set_property("width_request", 450)
        w.set_property("height_request", 115)
        return w, liststore
        
    # Generic Gtk callback to update ListStore when entries get edited.
    # where user_data = (liststore, column #id)
    @staticmethod
    def liststore_edit(cell, row, text, user_data):
        #log.EDIT(cell, row, text, user_data)
        row = int(row)
        liststore, column = user_data
        liststore[row][column] = text
        # update executable-indicator pixbuf
        if column == 1 and len(liststore[0]) == 3 and liststore[row][2].startswith("gtk-"):
            liststore[row][2] = uikit.app_bin_check(text)
        # add new row when editing last one
        if len(text) and (row + 1) == len(liststore):
            liststore.append(["", "", "gtk-new"])

    # return OK or CANCEL depending on availability of app
    @staticmethod
    def app_bin_check(v):
        bin = re.findall(r"(?<![$(`%-;/$])\b(\w+(?:-\w+)*)", v)
        if bin:
            bin = [find_executable(bin) for bin in bin]
            if not None in bin:
                return gtk.STOCK_MEDIA_PLAY
            else:
                return gtk.STOCK_CANCEL
        else:
            return gtk.STOCK_NEW


    # Attach textual menu entry and callback
    @staticmethod
    def add_menu(menuwidget, label, action, insert=None):
        for where in list(menuwidget):
            m = gtk.MenuItem(label)
            m.connect("activate", action)
            m.show()
            if insert:
                where.insert(m, insert)
            else:
                where.add(m)
        

    # gtk.messagebox
    @staticmethod
    def msg(text, style=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_CLOSE, yes=None):
        m = gtk.MessageDialog(None, 0, style, buttons, message_format=text)
        m.show()
        if yes:
            response = m.run()
            m.destroy()
            return response in (gtk.RESPONSE_OK, gtk.RESPONSE_ACCEPT, gtk.RESPONSE_YES)
        else:
            m.connect("response", lambda *w: m.destroy())
        pass
        

    # manual signal binding with a dict of { (widget, signal): callback }
    @staticmethod
    def add_signals(builder, map):
        for (widget,signal),func in map.items():
            builder.get_widget(widget).connect(signal, func)

        
    # Pixbug loader (from inline string, as in `logo.png`, automatic base64 decoding, and gunzipping of raw data)
    @staticmethod
    def pixbuf(buf, fmt="png", decode=True, gzip=False):
        if not buf or len(buf) < 16:
            return None
        if fmt and ver==3:
            p = GdkPixbuf.PixbufLoader.new_with_type(fmt)
        elif fmt:
            p = GdkPixbuf.PixbufLoader(fmt)
        else:
            p = GdkPixbuf.PixbufLoader()
        if decode and re.match("^[\w+/=\s]+$", str(buf)):
            buf = base64.b64decode(buf)  # inline encoding
        if gzip:
            buf = gzip_decode(buf)
        if buf:
            p.write(buf)
        pix = p.get_pixbuf()
        p.close()
        return pix
            

# Transparent png            
empty_pixbuf = uikit.pixbuf(
    """iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAA
    B6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAABmJLR0QA/wD/AP+gvaeTAAAAB3RJTUU
    H3wQLEAE6zgxuGAAAABFJREFUOBFjGAWjYBSMAigAAAQQAAFWMn04AAAAAElFTkSuQmCC"""
)



#-- Gtk3 wrappers

# Use a str of "1:2:3" as treepath,
# literally in Gtk2, TreePath-wrapped for Gtk3
def treepath(ls):
    if isinstance(ls, (list,tuple)):
        ls = ":".join(map(str, ls))
    if ver==2:
        return ls
    else:
        return gtk.TreePath.new_from_string(str(ls))
#
def treepath_to_str(tp):
    if ver==2:
        return tp
    else:
        return tp.to_string()
        


# Text-only dropdown list.
#
# Necessary because gtk.ComboBoxText binding is absent in debian packages
# https://bugzilla.gnome.org/show_bug.cgi?id=660659
#
# This one implements a convenience method `.set_default()` to define the active
# selection by value, rather than by index.
#
# Can use a list[] of entries or a key->value dict{}, where the value becomes
# display text, and the key the internal value.
#
class ComboBoxText(gtk.ComboBox):

    ls = None

    def __init__(self, entries, no_scroll=1):

        # prepare widget
        gtk.ComboBox.__init__(self)
        ########self.set_property("visible", True)
        cell = gtk.CellRendererText()
        self.pack_start(cell, True)
        self.add_attribute(cell, "text", 1)
        if no_scroll:
            self.connect("scroll_event", self.no_scroll)

        # collect entries
        self.ls = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.set_model(self.ls)
        if type(entries[0]) is not tuple:
            entries = zip(entries, entries)
        for key,value in entries:
            self.ls.append([key, value])
        
    # activate dropdown of given value
    def set_default(self, value):
        for index,row in enumerate(self.ls):
            if value in row:
                return self.set_active(index)
        # add as custom entry
        self.ls.append([value, value])
        self.set_active(index + 1)

    # fetch currently selected text entry
    def get_active_text(self):
        index = self.get_active()
        if index >= 0:
            return self.ls[index][0]

    # Signal/Event callback to prevent hover scrolling of ComboBox widgets
    def no_scroll(self, widget, event, data=None):
        return True


    # Expand A=a|B=b|C=c option list into (key,value) tuple list, or A|B|C just into a list.
    @staticmethod
    def parse_options(opts, sep="|", assoc="="):
        if opts.find(assoc) >= 0:
            return [ (k,v) for k,v in (x.split(assoc, 1) for x in opts.split(sep)) ]
        else:
            return opts.split(sep) #dict( (v,v) for v in opts.split(sep) )





#-- startup progress bar
progresswin, progressbar = None, None
def gui_startup(p=0/100.0, msg="streamtuner2 is starting"):
    global progresswin, progressbar
    
    if not progresswin:

        # GtkWindow "progresswin"
        progresswin = gtk.Window()
        progresswin.set_property("title", "streamtuner2")
        progresswin.set_property("default_width", 300)
        progresswin.set_property("width_request", 300)
        progresswin.set_property("default_height", 30)
        progresswin.set_property("height_request", 30)
        #progresswin.set_property("window_position", "center")
        progresswin.set_property("decorated", False)
        #######progresswin.set_property("visible", True)

        # GtkProgressBar "progressbar"
        progressbar = gtk.ProgressBar()
        #########progressbar.set_property("visible", True)
        progressbar.set_property("show_text", True)
        progressbar.set_property("text", msg)
        progresswin.add(progressbar)
        progresswin.show_all()

    try:
      if p <= 0.0:
        pass
      elif p < 1.0:
        progressbar.set_fraction(p)
        progressbar.set_property("text", msg)
        while gtk.events_pending(): gtk.main_iteration()
      else:
        progresswin.hide()
    except Exception as e:
        log.ERR("gui_startup()", e)




# Encapsulates references to gtk objects AND properties in main window,
# which allows to use self. and main. almost interchangably.
#
# This is a kludge to keep gtkBuilder widgets accessible; so just one
# instance has to be built. Also ties main.channels{} or .features{}
# dicts together for feature windows. Used by search, config, streamedit.
#
class AuxiliaryWindow(object):

    def __init__(self, parent):
        self.main = parent
        self.module = self.__class__.__name__
        self.meta = plugin_meta(None, inspect.getcomments(inspect.getmodule(self)))
        
    def __getattr__(self, name):
        if name in self.main.__dict__:
            return self.main.__dict__[name]
        elif name in self.main.__class__.__dict__:
            return self.main.__class__.__dict__[name]
        else:
            return self.main.get_widget(name)




# Auxiliary window: about dialog
#
class AboutStreamtuner2(AuxiliaryWindow):
    def __init__(self, parent):
        a = gtk.AboutDialog()
        a.set_name(parent.meta["id"])
        a.set_version(parent.meta["version"])
        a.set_license(parent.meta["license"])
        a.set_authors((get_data("CREDITS") or parent.meta["author"]).split("\n"))
        a.set_website(parent.meta["url"])
        a.connect("response", lambda a, ok: ( a.hide(), a.destroy() ) )
        a.show_all()
            
