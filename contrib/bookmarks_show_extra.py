# encoding: utf-8
# api: streamtuner2
# title: UI: bookmarks: show `extra` field
# description: Extra field in bookmarks list
# version: 0.0
# type: feature
# category: ui
# config: -
# priority: rare
# 
# Just injects the `extra` column for display
#
##
# Now some of the workarounds (clean treeview) wouldn't be necessary if this
# was loaded prior to bookmarks plugin. But alas we don't have #order: loading
# support in ST2 init/pluginconf.
#

from config import *
import copy

# Inject into .bookmarks.datamap[]
class bookmarks_show_extra (object):
    plugin = "bookmarks_show_extra"
    meta = plugin_meta()

    def __init__(self, parent):
        bm = parent.bookmarks
        # clean treeview
        for c in bm.gtk_list.get_columns():
            bm.gtk_list.remove_column(c)
            c.destroy()
        # inject new column
        bm.datamap = copy.deepcopy(bm.datamap)
        bm.datamap.append(
            ["Extra", 40, ["extra", str, "text", {}] ]
        )
        # redraw treeview
        bm.columns([])
           # @bug: does not update existing {text:IDX} attribute for columns,
           # just happens to work for .append()
  

