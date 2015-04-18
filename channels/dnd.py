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


from config import *
from uikit import *


# Drag and Drop support
class dnd(object):

    module = "dnd"
    meta = plugin_meta()

    # Keeps selected row on starting DND event
    current_row = None

    # Supported type map
    drag_types = [
      ("audio/x-mpegurl", 0, 20),
      ("application/x-scpls", 0, 21),
      ("application/xspf+xml", 0, 22),
      ("text/uri-list", 0, 4),
#      ("TEXT", 0, 5),
#      ("STRING", 0, 5),
#      ("text/plain", 0, 5),
#      ("UTF8_STRING", 0, 5),
    ]


    # Hook to main, and extend channel tabs
    def __init__(self, parent):
        self.parent = parent
        parent.hooks["init"].append(self.add_dnd)

    # Attach drag and drop functionality to each TreeView
    def add_dnd(self, parent):

        # visit each module
        for cn,module in parent.channels.items():
            w = module.gtk_list
            # as source
            w.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, self.drag_types, gtk.gdk.ACTION_DEFAULT|gtk.gdk.ACTION_COPY|gtk.gdk.ACTION_MOVE)
            w.connect('drag-begin', self.begin)
            w.connect('drag-data-get', self.data_get)
            # as target
            w.enable_model_drag_dest(self.drag_types, gtk.gdk.ACTION_DEFAULT|gtk.gdk.ACTION_COPY)
            w.connect('drag-drop', self.drop)
            w.connect('drag-data-received', self.data_received)


    # --SOURCE--
    def begin(self, tv, context):
        print "begin-dragging"
        context.set_icon_stock("gtk-add", 2, 2)
        self.current_row = self.treelist_row(tv)
        return True
    # src testing
    def data_get(self, tv, context, selection, info, *time):
        print "data-get→send", context.targets, selection, info, time
        selection.set_uris([self.current_row["url"]])
        return True
    # Get selected row
    def treelist_row(self, tv):
        return self.parent.channel().row()

                
    # --DESTINATION--
    def drop(self, tv, context, x, y, time, *e):
        print "drop→probing", context.targets, x, y, time, context.drag_get_selection()
        tv.drag_get_data(context, context.targets[-1], time)
        return True
    # dest testing
    def data_received(self, tv, context, x, y, selection, info, time, *e):
        print "data-received", x,y,selection, info, time, selection.get_uris()
        context.finish(True, True, time)
        return True
