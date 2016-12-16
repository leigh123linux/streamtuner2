# encoding: utf-8
# title: Stop button
# description: Kills streamripper recording
# version: 0.2
# depends: streamtuner2 >= 2.1.9
# type: feature
# category: ui
#
# Displays the [X] STOP toolbar button, and hooks it to
# a streamripper kill switch.

import action
from config import log, conf

# Stop button
class record_stop(object):
    module = 'record_stop'

    # button + hook
    def __init__(self, parent):
        btn = parent.stop
        btn.show()
        btn.set_property("visible", True)
        btn.set_property("visible_horizontal", True)
        btn.connect("clicked", self.pkill_streamripper)

    # stop recording
    def pkill_streamripper(self, *x, **y):
        if conf.windows:
            action.run("taskkill -im streamripper.exe")
        else:
            action.run("pkill streamripper || pkill fPls")

