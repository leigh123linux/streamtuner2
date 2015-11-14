# encoding: utf-8
# api: streamtuner2
# title: New station
# description: Adds menu entry to add new station
# version: 0.1
# type: feature
# category: ui
# config: -
# priority: optional
# 
# Is a trivial wrapper around streamedit, which hooks into the
# main menu as "New station..."
#

from uikit import *

# 
class new_station (object):
    plugin = "new_station"
    meta = plugin_meta()
    parent = None

    # show stream data editing dialog
    def __init__(self, parent):
        self.parent = parent
        uikit.add_menu([parent.streammenu], "New station…", self.new, insert=3)
  
    # add a new list entry, update window
    def new(self, *w):
        self.parent.streamedit.new(None)
