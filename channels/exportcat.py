# encoding: UTF-8
# api: streamtuner2
# title: Export Category
# description: Exports a complete channel category (all stations into one file).
# version: 0.3
# type: feature
# category: file
# priority: optional
# -disabled-config:
#   { name: export_format, value: xspf, type: select, select: "pls|xspf|m3u|jspf|smil|asx|json", description: Default export format. }
# hooks: config_save
#
# Adds a context menu "Extensions > Export all", which can be used
# in any channel and category to save all stations into one playlist.
# Defaults to exporting as .PLS file, but meanwhile can be used for
# XSPF or old M3U files as well.
# Note that a .desktop link can only hold the very first entry.
#
# It won't convert the internal stream URLs though. Such that the
# combined playlist file may reference further playlists from servers
# of a directory provider.
#
# This is a workaround until the main GUI supports selecting multiple
# rows at once. You can already save as


from config import *
from channels import *
import ahttp
from uikit import uikit
import action
import re


# provides another export window, and custom file generation - does not use action.save()
class exportcat():

    meta = plugin_meta()
    module = 'exportcat'

    # Register callback
    def __init__(self, parent):
        conf.add_plugin_defaults(self.meta, self.module)
        if parent:
            self.parent = parent
            uikit.add_menu([parent.extensions, parent.extensions_context], "Export all stations", self.savewindow)

    # Fetch streams from category, show "Save as" dialog, then convert URLs and export as playlist file
    def savewindow(self, *w):
        cn = self.parent.channel()
        source = cn.listformat
        streams = cn.streams[cn.current]
        category = re.sub(r"[^\w&-+]+", "_", cn.current)
        fn = uikit.save_file("Export category", None, "%s.%s.%s" % (cn.module, category, "pls"))
        log.PROC("Exporting category to", fn)
        if fn:
            dest = re.findall("\.(m3u|pls|xspf|jspf|json|smil|asx|desktop|url)8?$", fn.lower())
            if dest:
                dest = dest[0]
            else:
                self.parent.status("Unsupported export playlist type (file extension).")
                return
            action.save_playlist(source="asis", multiply=False).file(rows=streams, fn=fn, dest=dest)
        pass            
