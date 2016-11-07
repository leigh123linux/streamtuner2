# api: streamtuner2
# title: Stream entry editor
# description: Allows to inspect and modify station/stream entries.
# version: 0.6
# type: feature
# category: ui
# config: -
# priority: core
# 
# Editing dialog for stream entries. Available in
# the context and main menu. Most useful for
# changing bookmarks, or even creating new ones.
#

from uikit import *
import channels
from config import *
from copy import copy


# aux win: stream data editing dialog
class streamedit (AuxiliaryWindow):

    fields = [
        "favicon", "format", "genre", "homepage", "playing", "title", "url", "extra"
    ]

    # show stream data editing dialog
    def open(self, mw):
        self.main.configwin.load_config(self.main.row(), "streamedit_")
        self.win_streamedit.show_all()

    # copy widget contents to stream
    def save(self, w):
        row = self.main.row()
        for k in self.fields:
            if not k in row:
                row[k] = ""
        self.main.configwin.save_config(row, "streamedit_")
        self.main.channel().save()
        self.cancel(w)

    # add a new list entry, update window
    def new(self, w):
        s = self.main.channel().stations()
        s.append({"title":"new", "url":"", "format":"audio/mpeg", "genre":"", "listeners":1});
        self.main.channel().switch() # update display
        self.main.channel().gtk_list.get_selection().select_path(str(len(s)-1)); # set cursor to last row
        self.open(w)

    # hide window
    def cancel(self, *w):
        self.win_streamedit.hide()
        return True

