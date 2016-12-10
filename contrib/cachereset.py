# encoding: UTF-8
# api: streamtuner2
# title: Cache Reset
# description: Allows to empty cached stations and favicons
# version: 0.2
# type: feature
# category: config
# priority: optional
# hooks: config_load
#
# Inserts a [Cache Reset] button into the Options tab. Allows
# to either clear channel caches and/or stored favicons.


from config import *
from channels import *
import ahttp
from uikit import *
import action
import re
import os


# provides another export window, and custom file generation - does not use action.save()
class cachereset():

    meta = plugin_meta()
    module = __name__

    # Register in configwin
    def __init__(self, parent):
        # hook
        if not parent:
            return
        parent.hooks["config_load"].append(self.dialog_update)
        
        # add vbox
        hbox = gtk.HBox(False)
        btn = gtk.Button("Cache reset")
        btn.connect("clicked", self.execute)
        self.t1 = gtk.CheckButton("Channels __KB")
        self.t2 = gtk.CheckButton("Icons __KB")
        self.t3 = gtk.CheckButton("Temp __KB")
        hbox.pack_start(btn, True, True, 5)
        hbox.pack_start(self.t1, False, False, 10)
        hbox.pack_start(self.t2, False, False, 10)
        hbox.pack_start(self.t3, False, False, 10)
        parent.vbox1options.pack_start(hbox)
        self.l1 = self.t1.get_children()[0]
        self.l2 = self.t2.get_children()[0]
        self.l3 = self.t3.get_children()[0]
        

    # Update size labels
    def dialog_update(self, *w):
        s1 = self.foldersize(conf.dir + "/cache") / 1024
        s2 = self.foldersize(conf.dir + "/icons") / 1024
        s3 = self.foldersize(conf.tmp) / 1024
        self.l1.set_text("Channels (%s KB)" % s1)
        self.l2.set_text("Icons (%s KB)" % s2)
        self.l3.set_text("Temp (%s KB)" % s3)

    # Calculate folder size (flat dir)
    def foldersize(self, p):
        return sum([os.path.getsize(p+"/"+fn) for fn in os.listdir(p)])

    # Actually delete stuff
    def execute(self, *w):
        for dir, btn in [(conf.dir+"/cache/", self.t1), (conf.dir+"/icons/", self.t2), (conf.tmp+"/", self.t3)]:
            # check if checked
            if not btn.get_state():
                continue
            # list dir + delete files
            for fn in os.listdir(dir):
                os.unlink(dir + fn)
            open(dir + ".nobackup", "a").close()
            self.dialog_update()
