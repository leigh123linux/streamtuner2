# encoding: utf-8
# title: Continuous/JIT record
# description: Starts background recording on play, to allow saving current track
# version: 0.0
# depends: streamtuner2 >= 2.1.9
# type: hook
# config:
#   { name: jitrecord_ripper, type: select, value: streamtripper, select: streamripper|fpls, description: Background recording tool. }
#   { name: jitrecord_timeout, type: int, value: 15, description: Delete tracks after NN minutes. }
#   { name: jitrecord_target, type: str, value: "$HOME/Music", description: Where to save completed track. }
#   { name: jitrecord_tmp, type: str, value: "/tmp/streamtuner2/recording/", description: Temporary storeage. }
# category: ui
# status: incomplete
# support: none
#
# *Planned feature*
#    · Changes the record button into a record/save function.
#    · Starts streamripper in the background.
#      Target dir: /tmp/streamtuner2/recording/
#    · Deletes recorded tracks after 15 min.
#    · On [Save] just stored the last completed track
#      to $HOME/Music
#

import action
from config import *
from uikit import *
import os, os.path

# Stop button
class continuous_record(object):
    module = 'continuous_record'
    meta = plugin_meta()
    parent = None
    rec = None

    # exchange button and hook
    def __init__(self, parent):
        self.parent = parent
        self.rec = parent.record
    
        # register options
        conf.add_plugin_defaults(self.meta, self.module)
        
        # adapt icon
        self.rec.set_stock_id(gtk.STOCK_MEDIA_PAUSE)
        self.rec.set_label("jit")
        
        # apply hook
        parent.hooks["play"].append(self.play_start_recording)


    # Store last completed track away
    def save_current(self, *x, **y):
    
        # just opens stored folder
        action.run("xdg-open %s" % conf.jitrecord_tmp)
        
        # copy last file from /tmp to ~/Music
        pass


    # start recording background process
    def play_start_recording(self, row, *x, **y):

        # exchange toolbar button
        self.rec.set_stock_id(gtk.STOCK_FLOPPY)
        self.rec.set_label("track")
        self.rec.connect("clicked", self.save_current)
        #self.rec.disconnect("clicked", self.parent.on_record_clicked)
        
        # check for temp directory
        tmp = conf.jitrecord_tmp
        if not os.path.exists(tmp):
            os.mkdir(tmp)

        # start streamripper
        action.run("pkill streamripper")
        action.run("streamripper %r -d %s" % (row["url"], conf.jitrecord_tmp))

        # hook sched/kronos to look for outdated files
        pass
        
        # 


