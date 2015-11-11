# encoding: utf-8
# title: Stop button
# description: Kills streamripper recording
# version: 0.1
# depends: streamtuner2 >= 2.1.9
# type: feature
# category: ui
#
# Displays the [X] STOP toolbar button, and hooks it to
# a streamripper kill switch.

import action
from config import log

# Stop button
class record_stop(object):
    module = __name__

    # button + hook
    def __init__(self, parent):
        btn = parent.stop
        btn.show()
        btn.set_property("visible", True)
        btn.set_property("visible_horizontal", True)
        btn.connect("clicked", self.pkill_streamripper)

    # stop recording
    def pkill_streamripper(self, *x, **y):
        action.run("pkill streamripper || pkill fPls")

