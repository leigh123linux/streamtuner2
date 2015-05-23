# api: streamtuner2
# title: Soundcloud player
# description: Just sets a new configuration option for `soundcli`
# version: -1
# url: http://elephly.net/soundcli.html
# priority: once
# type: config
# category: player
# 
# You only need to run this plugin once. It just adds an
# entry for "audio/soundcloud" in the player config list.

from config import *

# just once
class cfg_soundcloud(object):

    module = "cfg_soundcloud"
    fmt = "audio/soundcloud"
    cmd = "xterm -e \"soundcli stream %srv\""

    def __init__(self, *a, **kw):
        conf.play.setdefault(self.fmt, self.cmd)
        print self.module
        conf.plugins[self.module] = False


