# encoding: UTF-8
# api: streamtuner2
# title: Drag and Drop
# description: Move streams/stations from and to other applications.
# depends: uikit
# version: 0.1
# type: interface
# config:
#   { name: dnd_format, type: select, value: pls, select: "pls|m3u|xspf|jspf|asx|smil", description: "Default temporary file format for copying a station entry." }
# category: ui
# priority: experimental
#
# Implements Gtk/X11 drag and drop support for station lists.
# Should allow to export either just stream URLs, or complete
# PLS, XSPF collections.
#
# Also used by the bookmarks tab to move favourites around.


# mousepad == ['GTK_TEXT_BUFFER_CONTENTS', 'application/x-gtk-text-buffer-rich-text',
#   'UTF8_STRING', 'COMPOUND_TEXT', 'TEXT', 'STRING',
#   'text/plain;charset=utf-8', 'text/plain']
# libreoffice ==# ['text/plain;charset=utf-8', 'UTF8_STRING', 'application/x-openoffice-embed-source-xml;windows_formatname="Star Embed# Source (XML)"', 'text/richtext', 'text/html',
#    'application/x-openoffice-objectdescriptor-xml;windows_formatname="Star Object Descriptor (XML)";classname="8BC6B165-B1B2-4EDD-aa47-dae2ee689dd6";typename="LibreOffice 4.4 Textdokument";viewaspect="1";width="16999";height="2995";posx="5347";posy="5347"']


import copy
from config import conf, __print__, dbg, json
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
      # internal
      ("json/vnd.streamtuner2.station", gtk.TARGET_SAME_APP, 51),
      # literal exports
      ("audio/x-mpegurl", 0, 20),
      ("application/x-scpls", 0, 21),
      ("application/xspf+xml", 0, 22),
      ("application/smil", 0, 23),
      ("text/html", 0, 23),
      ("text/richtext", 0, 23),
      ("application/jspf+json", 0, 25),
      # direct srv urls
      ("text/url", 0, 15),  #@TODO: support in action.save_/convert_
      ("message/external-body", 0, 15),
      ("url/direct", 0, 15),
      # url+comments
      ("TEXT", 0, 5),
      ("STRING", 0, 5),
      ("UTF8_STRING", 0, 5),
      ("text/plain", 0, 5),
      # filename, file:// IRL
      ("FILE_NAME", 0, 3),
      ("text/uri-list", 0, 4),
    ]
    cnv_types = {
       20: "m3u",
       21: "pls",
       22: "xspf",
       23: "smil",
       25: "jspf",
       15: "srv",
        4: "temp",
        5: "srv",
       51: "json",
    }


    # Hook to main, and extend channel tabs
    def __init__(self, parent):
        self.parent = parent
        parent.hooks["init"].append(self.add_dnd)
        conf.add_plugin_defaults(self.meta, self.module)


    # Attach drag and drop handlers to each channels´ station TreeView
    def add_dnd(self, parent):

        # visit each module
        for cn,module in parent.channels.items():
            w = module.gtk_list
            # bind SOURCE events
            w.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, self.drag_types, gtk.gdk.ACTION_DEFAULT|gtk.gdk.ACTION_COPY)
            w.connect('drag-begin', self.begin)
            w.connect('drag-data-get', self.data_get)
            # bind DESTINATION events
            w.enable_model_drag_dest(self.drag_types, gtk.gdk.ACTION_DEFAULT|gtk.gdk.ACTION_COPY)
            w.connect('drag-drop', self.drop)
            w.connect('drag-data-received', self.data_received)



    # -- SOURCE, drag'n'drop from ST2 to elsewhere --

    # Starting to drag a row
    def begin(self, widget, context):
        __print__(dbg.UI, "dnd←source: begin-drag, store current row")
        self.row = self.treelist_row()
        self.buf = {}
#        uikit.do(context.set_icon_default)
        uikit.do(context.set_icon_stock, gtk.STOCK_ADD, 16, 16)
        return "url" in self.row

    # Keep currently selected row when source dragging starts
    def treelist_row(self):
        cn = self.parent.channel()
        row = copy.copy(cn.row())
        row.setdefault("format", cn.audioformat)
        row.setdefault("listformat", cn.listformat)
        row.setdefault("url", row.get("homepage"))
        return row
        
    # Target window/app requests data for offered drop
    def data_get(self, widget, context, selection, info, time):
        __print__(dbg.UI, "dnd←source: data-get, send and convert to requested target type:", info, selection.get_target())

        # Start new converter if not buffered (because `data_get` gets called mercilessly along the dragging path)
        if not info in self.buf:
            r = self.row
            cnv = action.save_playlist(source=r["listformat"], multiply=False)

            # internal JSON row
            if info >= 51:
                buf = 'text', json.dumps(r)
                print buf
            # Pass M3U/PLS/XSPF as literal payload
            elif info >= 20:
                buf = 'text', cnv.export(urls=[r["url"]], row=r, dest=self.cnv_types[info])
            # Direct server URL
            elif info >= 10:
                urls = action.convert_playlist(r["url"], r["listformat"], "srv", False, r)
                #buf = 'uris', urls
                buf = 'text', urls[0]
            # Text sources are assumed to understand the literal URL or expect a description block
            elif info >= 5:
                buf = 'text', "{url}\n# Title: {title}\n# Homepage: {homepage}\n\n".format(**r)
            # Create temporary PLS file, because "text/uri-list" is widely misunderstood and just implemented for file:// IRLs
            else:
                tmpfn = "{}/{}.{}".format(conf.tmp, re.sub("[^\w-]+", " ", r["title"]), conf.dnd_format)
                cnv.file(rows=[r], dest=conf.dnd_format, fn=tmpfn)
                buf = 'uris', ["file://{}".format(tmpfn)] if (info==4) else tmpfn

            # Keep in type request buffer
            self.buf[info] = buf
        
        # Return prepared data
        func, data = self.buf[info]
        if func.find("text") >= 0:
            # Yay for trial and error. Nay for docs. PyGtks selection.set_text() doesn't actually work unless the requested target type is an Atom.
            selection.set("STRING", 8, data)
        if func.find("uris") >= 0:
            selection.set_uris(data)
        return True

                
    # -- DESTINATION, when playlist/url gets dragged in from other app --

    # Just a notification for incoming drop
    def drop(self, widget, context, x, y, time):
        __print__(dbg.UI, "dnd→dest: drop-probing, possible targets:", context.targets)
#        context.drop_reply(True, time) #"STRING"
        return widget.drag_get_data(context, context.targets[0], time) or True

    # Actual data is being passed,
    # now has to be converted and patched into stream rows and channel liststore
    def data_received(self, widget, context, x, y, selection, info, time):
        __print__(dbg.UI, "dnd→dest: data-receival", info, selection.get_text(), selection.get_uris())
#        print selection.get_length()
#        print selection.get_format()
#        print selection.get_targets()
#        print selection.get_target()
        
        # incoming data
        data = selection.get_text()
        urls = selection.get_uris()
        if not data and not urls:
            context.drop_finish(False, time)
            context.drag_abort(time)
            print "ABORT DROP"
            return

        # internal target dicts
        cn = self.parent.channel()
        
        # direct/internal row import
        if info >= 51:
            print "ADD ROW"
            cn.streams[cn.current].append(json.loads(data))
        # convertible formats
        elif info >= 10:
            pass
        elif info >= 5:
            pass
        else:
            pass
            #self.parent.streamedit()
            
        # finish drop
        context.drop_finish(True, time)
        context.finish(True, False, time)
        return True


