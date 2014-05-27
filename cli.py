#
# api: streamtuner2
# title: CLI interface
# description: allows to call streamtuner2 from the commandline
# status: experimental
# version: 0.3
#
#  Returns JSON data when queried. Usually returns cache data, but the
#  "category" module always loads fresh info from the directory servers.
#
#  Not all channel plugins are gtk-free yet. And some workarounds are
#  used here to not upset channel plugins about a missing parent window.
#
#
#


import sys
#from channels import *
import ahttp
import action
from config import conf
import json




# CLI
class StreamTunerCLI (object):


    # plugin info
    title = "CLI interface"
    version = 0.3

    
    # channel plugins
    channel_modules = ["shoutcast", "xiph", "internet_radio", "jamendo", "myoggradio", "live365"]
    current_channel = "cli"
    plugins = {} # only populated sparsely by .stream()
    
    
    # start
    def __init__(self):

        # fake init    
        action.action.main = empty_parent()
        action.action.main.current_channel = self.current_channel

        # check if enough arguments, else  help
        if len(sys.argv)<3:
            a = self.help
        # first cmdline arg == action
        else:
            command = sys.argv[1]
            a = self.__getattribute__(command)

        # run
        result = a(*sys.argv[2:])
        if result:
            self.json(result)
        
        
    # show help
    def help(self, *args): 
        print("""
syntax:  streamtuner2 action [channel] "stream title"

    from cache:
          streamtuner2 stream shoutcast frequence
          streamtuner2 dump xiph
          streamtuner2 play "..."
          streamtuner2 url "..."
    load fresh:
          streamtuner2 category shoutcast "Top 40"
          streamtuner2 categories xiph
        """)
        
    # prints stream data from cache
    def stream(self, *args):
 
        # optional channel name, title
        if len(args) > 1:
            (channel_list, title) = args
            channel_list = channel_list.split(",")
        else:
            title = list(args).pop()
            channel_list = self.channel_modules
        
        # walk through channel plugins, categories, rows
        title = title.lower()
        for channel in channel_list:
            self.current_channel = channel
            c = self.channel(channel)
            self.plugins[channel] = c
            c.cache()
            for cat in c.streams:
                for row in c.streams[cat]:
                    if row and row.get("title","").lower().find(title)>=0:
                        return(row)
    
    # just get url
    def url(self, *args):
        row = self.stream(*args)
        if row.get("url"):
            print(row["url"])
            
    # run player
    def play(self, *args):
        row = self.stream(*args)
        if row.get("url"):
            #action.action.play(row["url"], audioformat=row.get("format","audio/mpeg"))
            self.plugins[self.current_channel].play(row)
            
    # return cache data 1:1
    def dump(self, channel):
        c = self.channel(channel)
        c.cache()
        return c.streams
        
        
    # load from server
    def category(self, module, cat):
        c = self.channel(module)
        r = c.update_streams(cat)
        [c.postprocess(row) for row in r]
        return r

    # load from server
    def categories(self, module):
        c = self.channel(module)
        c.cache()
        r = c.update_categories()
        if not r:
            r = c.categories
        if c.__dict__.get("empty"):
            del r[0]
        return r
        
        
    # load module
    def channel(self, module):
        plugin = __import__("channels."+module, None, None, [""])
        plugin_class = plugin.__dict__[module]
        p = plugin_class(None)
        p.parent = empty_parent()
        return p
    
    # load all channel modules    
    def channels(self, channels=None):
        if channels:
            channels = channels.split(",")
        else:
            channels = self.channel_modules
        return (self.channel(module) for module in channels)
    
    # pretty print json
    def json(self, dat):    
        print(json.dumps(dat, sort_keys=True, indent=2))
    
    
    
    
    
# trap for some main window calls
class empty_parent (object):    
    channel = {}
    null = lambda *a: None
    status = null
    thread = null


    