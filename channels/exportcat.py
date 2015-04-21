# encoding: UTF-8
# api: streamtuner2
# title: Export All
# description: Exports a complete channel category (all stations into one file).
# version: -0.1
# type: feature
# category: file
# priority: optional
# config:
#   { name: export_format, value: pls, type: select, select: "pls|xspf|m3u|jspf|smil|asx|json", description: Export format. }
# hooks: config_save
#
# Use "Extensions > Export all" in the desired channel and category,
# to export all station entries at once. Currently just export PLS,
# which in turn references other .pls file).  Luckily most players
# can cover up for this horrid misdesign.
#
# This is a workaround until the main GUI supports selecting multiple
# rows at once, and the action.* module has been overhauled to export
# a bit more deterministically.


from config import *
from channels import *
import ahttp
from uikit import uikit
import action
import re


# provides another export window, and custom file generation - does not use action.save()
class exportcat():

    meta = plugin_meta()
    module = "exportcat"

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
        fn = uikit.save_file("Export category", None, "%s.%s.%s" % (cn.module, cn.current, conf.export_format))
        log.PROC("Exporting category to", fn)
        if fn:
            dest = re.findall("\.(m3u8?|pls|xspf|jspf|json|smil|asx)8?$", fn.lower())
            if dest:
                dest = dest[0]
            else:
                self.parent.status("Unsupported export playlist type (file extension).")
                return
            action.save_playlist(source="asis", multiply=False).file(rows=streams, fn=fn, dest=dest)
        pass            
