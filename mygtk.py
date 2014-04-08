#
# encoding: UTF-8
# api: python
# type: functions
# title: mygtk helper functions
# description: simplify usage of some gtk widgets
# version: 1.7
# author: mario
# license: public domain
#
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
#
#




# debug
from config import __print__, dbg

# filesystem
import os.path
import copy
import sys

from compat2and3 import unicode, xrange, PY3


# gtk version (2=gtk2, 3=gtk3)
ver = 2
# if running on Python3 or with commandline flag
if PY3 or "--gtk3" in sys.argv:
    ver = 3
# load gtk modules
if ver==3:
    from gi import pygtkcompat as pygtk
    pygtk.enable() 
    pygtk.enable_gtk(version='3.0')
    from gi.repository import Gtk as gtk
    from gi.repository import GObject as gobject
    from gi.repository import GdkPixbuf
    ui_file = "gtk3.xml"
    empty_pixbuf = GdkPixbuf.Pixbuf.new_from_data(b"\0\0\0\0", GdkPixbuf.Colorspace.RGB, True, 8, 1, 1, 4, None, None)
    __print__(dbg.PROC, gtk)
    __print__(dbg.PROC, gobject)
else:
    import pygtk
    import gtk
    import gobject
    ui_file = "gtk2.xml"
    empty_pixbuf = gtk.gdk.pixbuf_new_from_data(b"\0\0\0\0",gtk.gdk.COLORSPACE_RGB,True,8,1,1,4)




# simplified gtk constructors               ---------------------------------------------
class mygtk:


             
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
        def columns(widget, datamap=[], entries=[], pix_entry=False, typecast=0):

            # create treeviewcolumns?
            if (not widget.get_column(0)):
                # loop through titles
                datapos = 0
                for n_col,desc in enumerate(datamap):
                                    
                    # check for title
                    if (type(desc[0]) != str):
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
                    for var in xrange(2, len(desc)):
                        cell = desc[var]
                        # cell renderer
                        if (cell[2] == "pixbuf"):
                            rend = gtk.CellRendererPixbuf()  # img cell
                            if (cell[1] == str):
                                cell[3]["stock_id"] = datapos  # for stock icons
                                expand = False
                            else:
                                pix_entry = datapos
                                cell[3]["pixbuf"] = datapos
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

                        __print__(cell)
                    # add column to treeview
                    widget.append_column(col)
                # finalize widget
                widget.set_search_column(5)   #??
                widget.set_search_column(4)   #??
                widget.set_search_column(3)   #??
                widget.set_search_column(2)   #??
                widget.set_search_column(1)   #??
                #widget.set_reorderable(True)
               
            # add data?
            if (entries):
                #- expand datamap            
                vartypes = []  #(str, str, bool, str, int, int, gtk.gdk.Pixbuf, str, int)
                rowmap = []    #["title", "desc", "bookmarked", "name", "count", "max", "img", ...]
                if (not rowmap):
                    for desc in datamap:
                        for var in xrange(2, len(desc)):
                            vartypes.append(desc[var][1])  # content types
                            rowmap.append(desc[var][0])    # dict{} column keys in entries[] list
                # create gtk array storage
                ls = gtk.ListStore(*vartypes)   # could be a TreeStore, too
                __print__(vartypes)
                __print__(rowmap)

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
#                    row["search_col"] = "white"

                    # generate ordered list from dictionary, using rowmap association
                    row = [   row.get( skey , defaults[vartypes[i]] )   for i,skey   in enumerate(rowmap)   ]

                    # autotransform string -> gtk image object
                    if (pix_entry and type(row[pix_entry]) == str):
                        row[pix_entry] = (  gtk.gdk.pixbuf_new_from_file(row[pix_entry])  if  os.path.exists(row[pix_entry])  else  defaults[gtk.gdk.Pixbuf]  )

                    try:
                        # add
                        ls.append(row)   # had to be adapted for real TreeStore (would require additional input for grouping/level/parents)

                    except:
                        # brute-force typecast
                        ls.append( [va  if ty==gtk.gdk.Pixbuf  else ty(va)   for va,ty in zip(row,vartypes)]  )
                __print__(row)
                
                # apply array to widget
                widget.set_model(ls)
                return ls
                
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

            # add entries
            for entry in entries:
                if (type(entry) == str):
                    main = ls.append(None, [entry, icon])
                else:
                    for sub_title in entry:
                        ls.append(main, [sub_title, icon])

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

            # finalize
            widget.set_model(ls)
            tvcolumn.set_sort_column_id(0)
            widget.set_search_column(0)
            #tvcolumn.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            #tvcolumn.set_fixed_width(125])
            #widget.expand_all()
            #widget.expand_row("3", False)
            #print(widget.row_expanded("3"))

            return ls




        #-- save window size and widget properties
        #
        # needs a list of widgetnames
        # e.g. pickle.dump(mygtk.app_state(...), open(os.environ["HOME"]+"/.config/app_winstate", "w"))
        #
        @staticmethod
        def app_state(wTree, widgetnames=["window1", "treeview2", "vbox17"]):
            r = {} # restore array
            for wn in widgetnames:
                r[wn] = {}
                w = wTree.get_widget(wn)
                t = type(w)
#                print(wn, w, t)
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
                        if w.row_expanded(str(i)):
                            r[wn]["rows:expanded"].append(i)
                    # - selected
                    (model, paths) = w.get_selection().get_selected_rows()
                    if paths:
                        r[wn]["row:selected"] = paths[0]
                # gtk.Toolbar
                if t == gtk.Toolbar:
                    r[wn]["icon_size"] = int(w.get_icon_size())
                    r[wn]["style"] = int(w.get_style())
                # gtk.Notebook
                if t == gtk.Notebook:
                    r[wn]["page"] = w.get_current_page()
            #print(r)
            return r


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
                for method,args in r[wn].iteritems():
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
                            w.expand_row(str(i), False)                        
                    #  - selected
                    if method == "row:selected":
                        w.get_selection().select_path(tuple(args))
                    # gtk.Toolbar
                    if method == "icon_size":
                        w.set_icon_size(args)
                    if method == "style":
                        w.set_style(args)
                    # gtk.Notebook
                    if method == "page":
                        w.set_current_page(args)

            pass



        #-- Save-As dialog
        #
        @staticmethod
        def save_file(title="Save As", parent=None, fn="", formats=[("*","*")]):
            c = gtk.FileChooserDialog(title, parent, action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=(gtk.STOCK_CANCEL, 0, gtk.STOCK_SAVE, 1))
            # params
            if fn:
                c.set_current_name(fn)
                fn = ""
            for fname,ftype in formats:
                f = gtk.FileFilter()
                f.set_name(fname)
                f.add_pattern(ftype)
                c.add_filter(f)
            # display
            if c.run():
                fn = c.get_filename()  # return filaname
            c.destroy()
            return fn
        
        
        
        # pass updates from another thread, ensures that it is called just once
        @staticmethod
        def do(lambda_func):
            gobject.idle_add(lambda: lambda_func() and False)


        # adds background color to widget,
        # eventually wraps it into a gtk.Window, if it needs a container
        @staticmethod
        def bg(w, color="", where=["bg"]):
            """ this method should be called after widget creation, and before .add()ing it to container """
            if color:
                # wrap unstylable widgets into EventBox
                if not isinstance(w, gtk.Window):
                    wrap = gtk.EventBox()
                    wrap.add(w)
                    wrap.set_property("visible", True)
                    w = wrap
                # copy style object, modify settings
                s = w.get_style().copy()
                c = w.get_colormap().alloc_color(color)
                for state in (gtk.STATE_NORMAL, gtk.STATE_SELECTED):
                    s.bg[state] = c
                w.set_style(s)
                # probably redundant, but better safe than sorry:
                w.modify_bg(gtk.STATE_NORMAL, c)
            # return modified or wrapped widget
            return w


        @staticmethod
        def add_menu(menuwidget, label, action):
            m = gtk.MenuItem(label)
            m.connect("activate", action)
            m.show()
            menuwidget.add(m)
            

        # gtk.messagebox
        @staticmethod
        def msg(text, style=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_CLOSE):
            m = gtk.MessageDialog(None, 0, style, buttons, message_format=text)
            m.show()
            m.connect("response", lambda *w: m.destroy())
            


