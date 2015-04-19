# encoding: UTF-8
# api: streamtuner2
# title: Drag and Drop
# description: Move streams/stations from and to other applications.
# depends: uikit
# version: 0.1
# type: interface
# category: ui
#
# Implements Gtk/X11 drag and drop support for station lists.
# Should allow to export either just stream URLs, or complete
# PLS, XSPF collections.
#
# Also used by the bookmarks tab to move favourites around.


import copy
from config import *
from uikit import *
import action


# Drag and Drop support
class dnd(object):

    module = "dnd"
    meta = plugin_meta()

    # Keeps selected row on starting DND event
    row = None
    # Buffer converted types
    buf = {}

    # Supported type map
    drag_types = [
      ("json/vnd.streamtuner2.station", 0, 51),
      ("audio/x-mpegurl", 0, 20),
      ("application/x-scpls", 0, 21),
      ("application/xspf+xml", 0, 22),
      ("FILE_NAME", 0, 3),
      ("text/uri-list", 0, 4),
      ("STRING", 0, 5),
      ("text/plain", 0, 5),
    ]
    cnv_types = {
       20: "m3u",
       21: "pls",
       22: "xspf",
        4: "temp",
        5: "srv",
       51: "json",
    }


    # Hook to main, and extend channel tabs
    def __init__(self, parent):
        self.parent = parent
        parent.hooks["init"].append(self.add_dnd)


    # Attach drag and drop handlers to each channels´ station TreeView
    def add_dnd(self, parent):

        # visit each module
        for cn,module in parent.channels.items():
            w = module.gtk_list
            # bind SOURCE events
            w.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, self.drag_types, gtk.gdk.ACTION_DEFAULT|gtk.gdk.ACTION_COPY|gtk.gdk.ACTION_MOVE)
            w.connect('drag-begin', self.begin)
            w.connect('drag-data-get', self.data_get)
            # bind DESTINATION events
            w.enable_model_drag_dest(self.drag_types, gtk.gdk.ACTION_DEFAULT|gtk.gdk.ACTION_COPY)
            w.connect('drag-drop', self.drop)#self.drag_types
            w.connect('drag-data-received', self.data_received)



    # -- SOURCE, drag'n'drop from ST2 to elsewhere --

    # Starting to drag a row
    def begin(self, widget, context):
        __print__(dbg.UI, "dnd←source: begin-drag, store current row")
        self.row = self.treelist_row()
        self.buf = {}
        #context.set_icon_stock("gtk-add", 2, 2)
        return "url" in self.row


    # Keep currently selected row when source dragging starts
    def treelist_row(self):
        cn = self.parent.channel()
        row = copy.copy(cn.row())
        row.setdefault("format", cn.audioformat)
        row.setdefault("listformat", cn.listformat)
        return row

        
    # Target window/app requests data for offered drop
    def data_get(self, widget, context, selection, info, time):
        __print__(dbg.UI, "dnd←source: data-get, send and convert to requested target type", info)

        # Start new converter if not buffered (because `data_get` gets called mercilessly along the dragging path)
        if not info in self.buf:
            r = self.row
            cnv = action.save_playlist(source=r["listformat"], multiply=False)

            # Pass M3U/PLS/XSPF as direct content, or internal JSON even
            if info >= 20:
                buf = 'set_text', cnv.export(urls=[r["url"]], row=r, dest=self.cnv_types[info])
            # Create temporary PLS file, because "text/uri-list" is widely misunderstood and just implemented for file:// IRLs
            elif info <= 4:
                fn = "{}/{}.pls".format(conf.tmp, re.sub("[^\w-]+", " ", r["title"]))
                cnv.file(rows=[r], dest="pls", fn=fn)
                if info == 4:
                    fn = ["file://localhost{}".format(fn)]
                buf = 'set_uris', fn
            # Text sources are assumed to understand the literal URL, or expect a description
            else:
                buf = 'set_text', "{url}\n# Title: {title}\n# Homepage: {homepage}".format(**r)

            # Buffer
            self.buf[info] = buf
            
        # Return prepared data
        func, data = self.buf[info]
        if func in ('set_text'):
            selection.set_text(data)
        else:
            selection.set_uris(data)
        return True

                
    # -- DESTINATION, when playlist/url gets dragged in from other app --

    # Just a notification for incoming drop
    def drop(self, widget, context, x, y, time):
        __print__(dbg.UI, "dnd→dest: drop-probing", context.targets, x, y, time, context.drag_get_selection())
        widget.drag_get_data(context, context.targets[0], time)
        return True

    # Actual data is being passed,
    # now has to be converted and patched into stream rows and channel liststore
    def data_received(self, widget, context, x, y, selection, info, time):
        __print__(dbg.UI, "dnd→dest: data-receival", x,y,selection, info, time, selection.get_uris(), selection.get_text())
        context.finish(True, False, time)
        return True


