# encoding: UTF-8
# api: streamtuner2
# title: Drag and Drop
# description: Copy streams/stations from and to other applications.
# depends: uikit >= 1.8, action >= 1.0
# version: 0.7
# type: feature
# config:
#   { name: dnd_format, type: select, value: xspf, select: "pls|m3u|xspf|jspf|asx|smil|desktop|srv", description: "Default temporary file format for copying a station." }
# category: io
# priority: default
# support: experimental
#
# Implements Gtk/X11 drag and drop support for station lists.
# Should allow to export either just stream URLs, or complete
# PLS, XSPF collections.
#
# Also used by the bookmarks channel to copy favourites around.
# Which perhaps should even be constrained to just the bookmarks
# tab.


import copy
from config import conf, json, log
from uikit import *
import action
import compat2and3


# Welcome to my new blog.
#
# Now it's perhaps not even Gtks fault, but all the gory implementation
# details of XDND are pretty gory. And not much documentatiion lives up
# to reality anymore.
#
# Almost only the ridiculous `TEXT/URI-LIST` is used in practice. Without
# host names, of course, despite the spec saying otherwise. (It perhaps
# leaked into the Gnome UI, and they decreed it banished). And needless
# to say, there's no actual IRI (or "URI" if you've been living under a
# rock for two decades) support in any file manager or pairing clients
# beyond local paths.
#
# Supporting PLS, XSPF, M3U as direct payload was a pointless exercise.
# It's not gonna get requested by anyone. Instead there's another config
# option now, which predefines the exchange format for temporary file:///
# dumps. Because, you know, there was never any point in type negotiation
# due to all the API overhead. There's no way to indicate any actually
# supported content types per text/uri-list.
#
# What works, and what's widely used in practice instead, is declaring
# yet another custom type per application. Our row format is transferred
# unfiltered over the selection buffer as JSON. However, it's decidedly
# never exposed to other apps as x-special/x-custom whatever. (It's also
# not using the MIME 1.0 application/* trash bin for that very reason.)


# Drag and Drop support
class dnd(object):

    module = 'dnd'
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
      ("application/xspf+xml", 0, 22),
      ("application/jspf+json", 0, 25),
      ("application/x-scpls", 0, 21),
      ("audio/x-mpegurl", 0, 20),
      ("application/smil", 0, 23),
      ("text/html", 0, 23),
      ("text/richtext", 0, 23),
      ("application/x-desktop", 0, 26),
      ("text/url", 0, 27),
      ("message/external-body", 0, 27),
      # direct srv urls
      ("url/direct", 0, 15),
      ("text/iri-list", 0, 15),
      # filename, file:// IRL
      ("FILE_NAME", 0, 3),
#     ("text/uri-list;x-format=xspf,pls,m3u,jspf,smil,http", 0, 4),
      ("text/uri-list", 0, 4),
      # url+comments
      ("TEXT", 0, 5),
      ("STRING", 0, 5),
      ("UTF8_STRING", 0, 5),
      ("text/plain", 0, 5),
    ]
    
    # Map target/`info` integers to action. module identifiers
    cnv_types = {
       20: "m3u",
       21: "pls",
       22: "xspf",
       23: "smil",
       25: "jspf",
       26: "desktop",
       27: "url",
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
            
        # register bookmarks category as destination too
        w = parent.bookmarks.gtk_cat
        w.enable_model_drag_dest([self.drag_types[0]], gtk.gdk.ACTION_DEFAULT|gtk.gdk.ACTION_MOVE)
        w.connect('drag-data-received', self.data_received)
        



    # -- SOURCE, drag'n'drop from ST2 to elsewhere --

    # Starting to drag a row
    def begin(self, widget, context):
        log.DND("source→out: begin-drag, store current row")
        self.row = self.treelist_row()
        self.buf = {}
        if "set_icon_stock" in dir(context):
            uikit.do(context.set_icon_stock, gtk.STOCK_ADD, 16, 16)
        return "url" in self.row

    # Keep currently selected row when source dragging starts
    def treelist_row(self):
        cn = self.parent.channel()
        row = copy.copy(cn.row())
        row.setdefault("format", cn.audioformat)
        row.setdefault("listformat", cn.listformat)
        row.setdefault("url", row.get("homepage"))
        row.update({"_origin": [cn.module, cn.current, cn.rowno()]}) # internal: origin channel+genre+rowid
        return row
    
    # Target window/app requests data for offered drop
    def data_get(self, widget, context, selection, info, time):
        log.DND("source→out: data-get, send and convert to requested target type:", info, selection.get_target())
        # Return prepared data
        func, data = self.export_row(info, self.row)
        log.DND("data==", func, data)
        if func.find("text") >= 0:
            try:
                # Yay for trial and error. Nay for docs. PyGtks selection.set_text() doesn't
                # actually work unless the requested target type is an Atom. Therefore "STRING".
                selection.set("STRING", 8, data)
            except:
                # Except of course Gtk3, where an Atom is required, but neither
                # gtk.gdk.TARGET_STRING nor selection.get_target() actually do
                selection.set_text(data, len(data))
        if func.find("uris") >= 0:
            selection.set_uris(data)
        return True

    # Handles the conversion from the stored .row to the desired selection data
    def export_row(self, info, r):

        # Needs buffering because `data_get` gets called mercilessly along the dragging path
        if info in self.buf:
            return self.buf[info]
        
        # Prepare new converter
        cnv = action.save_playlist(source=r["listformat"], multiply=False)

        # internal JSON row
        if info >= 51:
            buf = 'text', json.dumps(r)

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

        # Direct URL as text/uri-list
        elif conf.dnd_format == "srv":
            buf = 'uris', [self.row.get("url")]

        # Create temporary PLS file, because "text/uri-list" is widely misunderstood
        # and just used for file:// IRLs in drag and drops
        else:
            title = re.sub("[^\w-]+", "_", r["title"]).strip()
            tmpfn = "{}/{}.{}".format(conf.tmp, title, conf.dnd_format)
            log.DND("tmpfn", tmpfn)
            cnv.file(rows=[r], dest=conf.dnd_format, fn=tmpfn)
            if info == 4:
                buf = 'uris', ["file://{}".format(tmpfn)]
            else:
                buf = 'text', tmpfn

        # Keep in type request buffer
        self.buf[info] = buf
        return buf



    # -- DESTINATION, when playlist/file gets dragged into ST2 from other app --

    # Just a notification for incoming drop
    def drop(self, widget, context, x, y, time):
        log.DND("dest←in: drop-probing, possible targets:", context.targets)
        # find a matching target
        targets = [t.split(";")[0] for t in context.targets]
        accept = [type[0] for type in self.drag_types if type[0] in targets]
        context.drop_reply(len(accept) > 0, time)
        if accept:
                widget.drag_get_data(context, accept[0], time) or True
        return True

    # Actual data is being passed,
    def data_received(self, widget, context, x, y, selection, info, time):
        log.DND("dest←in: data-receival", info, selection.get_target(), selection.get_text(), selection.get_uris())

        # incoming data
        data = selection.get_text()
        urls = selection.get_uris()
        any = (data or urls) and True

        # Convert/Add
        if any: self.import_row(info, urls, data, y)
        else: log.DND("Abort, no urls/text.")
        
        # Respond
        context.drop_finish(any, time)
        context.finish(any, False, time)
        return True

    # Received files or payload has to be converted, copied into streams
    def import_row(self, info, urls, data, y=5000):
        # Internal target dicts
        cn = self.parent.channel()
        rows = []
                
        # Direct/internal row import
        if data and info >= 51:
            log.DND("Received row in internal format, append+reload")
            rows += [ json.loads(data) ]

        # Convertible formats as direct payload
        elif data and info >= 5:
            log.DND("Converting direct payload playlist")
            cnv = action.extract_playlist(data)
            
            # known DND info format
            if info >= 20:
                fmt = self.cnv_types[info]

            # else probe content (which also works for URLs in plain text)
            else:
                fmt = cnv.probe_fmt()
                if fmt == "href": fmt = "raw"

            add = cnv.rows(fmt)
            rows += [ cnv.mkrow(row) for row in add ]

        # Extract from playlist files, either passed as text/uri-list or single FILE_NAME
        elif urls:
            log.DND("Importing from playlist file")
            for fn in urls or [data]:

                # Plain file urls
                if re.match("^(scp|file)://(localhost)?/|/", fn):

                    # read and convert playlist files
                    fn = compat2and3.urldecode(re.sub("^\w+://[^/]*", "", fn))
                    cnv = action.extract_playlist(fn=fn)
                    if cnv.src:
                        rows += [ cnv.mkrow(row) for row in cnv.rows() ]

                # Real resource links, http://server:8090/.mp3 etc
                else:
                    # Action module can't query streaming servers yet,
                    # so append a stub entry of just the target url,
                    # which will bring up the streamedit dialog
                    rows += [ dict(url=fn, title="", playing="", genre="url") ]
                    
        
        # Insert and update view
        if rows:
            cn.insert_rows(rows, y)
            if conf.auto_save_stations or cn.module == "bookmarks":
                cn.save()
            # Show streamedit window if title is empty
            if not len(rows[0].get("title", "")):
                self.parent.configwin.load_config(rows[0], "streamedit_")
                self.parent.win_streamedit.show()
        else:
            self.parent.status("Unsupported station format. Not imported.")


        