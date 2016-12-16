# api: streamtuner2
# title: Global keyboard shortcut
# description: Allows switching between bookmarked radios via key press.
# type: feature
# category: ui
# version: 0.3
# config:
#    { name="switch_key", type="text", value="XF86Forward", description="Global key shortcut for switching radio." },
#    { name="switch_channel", type="text", value="bookmarks:favourite", description="Station list and channels to alternate in." },
#    { name="switch_random", type="boolean", value=0, description="Pick random channel, instead of next." },
# priority: extra
# depends: python:keybinder, uikit >= 1.5
#
#
# Binds a key to global desktop (F13 = left windows key).
# On keypress switches the currently playing radio station
# to another one from the bookmarks list.
#
# Valid key names are `F9`, `<Ctrl>G`, `<Alt>R` for example.


import keybinder
from config import *
import action
import random



# register a key
class global_key(object):

    # control attributes
    module = 'global_key'
    meta = plugin_meta()
    last = 0


    # register
    def __init__(self, parent):
        self.parent = parent
        conf.add_plugin_defaults(self.meta, self.module)
        try:
            for i,keyname in enumerate(conf.switch_key.split(",")):    # allow multiple keys
                keybinder.bind(keyname, self.switch, ((-1 if i else +1)))   # forward +1 or backward -1
        except:
            log.ERR("plugin global_key: Key `%s` could not be registered" % conf.switch_key)
    
        
    # key event
    def switch(self, num, *any):
        
        # bookmarks, favourite
        channel, cat = conf.switch_channel.split(":")

        # get list
        streams = self.parent.channels[channel].streams[cat]

        # pickrandom
        if conf.switch_random:
            self.last = random.randint(0, len(streams)-1)

        # or iterate over list
        else:
            self.last = self.last + num
            if self.last >= len(streams):
                self.last = 0
            elif self.last < 0:
                self.last = len(streams)-1
            
        # play
        i = self.last
        action.play(streams[i]["url"], streams[i]["format"])

        # set pointer in gtk.TreeView
        if self.parent.channels[channel].current == cat:
            self.parent.channels[channel].gtk_list.get_selection().select_path(i)


        