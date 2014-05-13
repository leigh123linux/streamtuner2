#
# api: streamtuner2
# title: Global keyboard shortcut
# description: Allows switching between bookmarked radios via key press.
# type: feature
# category: ui
# version: 0.2
# priority: extra
# depends: python-keybinder
#
#
# Binds a key to global desktop (F13 = left windows key). On keypress
# it switches the currently playing radio station to another one in
# bookmarks list.
#
# Valid key names are for example F9, <Ctrl>G, <Alt>R, <Super>N
#


import keybinder
from config import conf
import action
import random



# register a key
class global_key(object):

    module = "global_key"
    title = "keyboard shortcut"
    
    config = [
        dict(name="switch_key", type="text", value="XF86Forward", description="global key for switching radio"),
        dict(name="switch_channel", type="text", value="bookmarks:favourite", description="station list to alternate in"),
        dict(name="switch_random", type="boolean", value=0, description="pick random channel, instead of next"),
    ]
    last = 0


    # register
    def __init__(self, parent):
        self.parent = parent
        try:
            for i,keyname in enumerate(conf.switch_key.split(",")):    # allow multiple keys
                keybinder.bind(keyname, self.switch, ((-1 if i else +1)))   # forward +1 or backward -1
        except:
            print("Key could not be registered")
    
        
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
        action.action.play(streams[i]["url"], streams[i]["format"])

        # set pointer in gtk.TreeView
        if self.parent.channels[channel].current == cat:
            self.parent.channels[channel].gtk_list.get_selection().select_path(i)


        