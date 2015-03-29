#
# api: streamtuner2
# title: File browser
# description: Displays mp3/oggs or m3u/pls files from local media file directories.
# type: channel
# category: media
# version: 0.1
# priority: optional
# depends: mutagen
# config:  
#   { name: file_browser_dir, type: text, value: "~/Music, /media/music", description: "List of directories to scan for audio files." },
#   { name: file_browser_ext, type: text, value: "mp3,ogg, m3u,pls,xspf, avi,flv,mpg,mp4", description: "File type/extension filter." },
#
# Local file browser.
#



# modules
import os
import re

from channels import *
from config import *

# ID3 libraries
try:
    from mutagen import File as get_meta
except:
    try:
        from ID3 import ID3
        __print__(dbg.INFO, "Just basic ID3 support")
        get_meta = lambda fn: dict([(k.lower(),v) for k,v in ID3(fn).iteritems()])
    except:
        __print__(dbg.INIT, "You are out of luck in regards to mp3 browsing. No ID3 support.")
        get_meta = lambda *x: {}


# work around mutagens difficult interface
def mutagen_postprocess(d):
    if d.get("TIT2"):
        return {
            "encoder": d["TENC"][0],
            "title": d["TIT2"][0],
            "artist": d["TPE1"][0],
#            "tyer?????????????": d["TYER"][0],
#            "track": d["TRCK"][0],
            "album": d["TALB"][0],
        }
    else:
        return d




# file browser / mp3 directory listings
class file (ChannelPlugin):

    # info
    module = "file"
    title = "file browser"
    listtype = "url/file"
    
    # data
    streams = {}
    categories = []
    dir = []
    ext = []
    
    # display
    datamap = [ # coltitle   width	[ datasrc key, type, renderer, attrs ]	[cellrenderer2], ...
           ["",		20,	["state",	str,  "pixbuf",	{}],	],
           ["Genre",	65,	['genre',	str,	"t",	{"editable":8}],	],
           ["File",	160,	["filename",	str,	"t",	{"strikethrough":10, "cell-background":11, "cell-background-set":12}],	],
           ["Title",	205,	["title",	str,    "t",	{"editable":8}], ],
           ["Artist",	125,	["artist",	str,	"t",	{"editable":8}],	],
           ["Album", 	125,	["album",	str,	"t",	{"editable":8}],	],
           ["Bitrate",	35,	["bitrate",	int,	"t",	{}],	],
           ["Format",	50,	["format",	str,	None,	{}],	],
           [False,	0,	["editable",	bool,	None,	{}],	],
           [False,	0,	["favourite",	bool,	None,	{}],	],
           [False,	0,	["deleted",	bool,	None,	{}],	],
           [False,	0,	["search_col",	str,	None,	{}],	],
           [False,	0,	["search_set",	bool,	None,	{}],	],
    ]        
    rowmap = []

    

    # prepare    
    def __init__(self, parent):
    
        # data dirs
        self.dir = [s.strip() for s in conf.file_browser_dir.split(",")]
        self.ext = [s.strip() for s in conf.file_browser_ext.split(",")]
        # first run
        if not self.categories or not self.streams:
            self.scan_dirs()
            
        # draw gtk lists
        ChannelPlugin.__init__(self, parent)
        
        # make editable
        #{editable:8}
        
        # add custom context menu
        #self.gtk_list.connect('button-press-event', self.context_menu)

        
        
    # save list?
    #save = lambda *x: None
    # yeah, give it a try
    
    # don't load cache file
    cache = lambda *x: None

        

    # read dirs
    def scan_dirs(self):
        self.categories = []
    
        # add main directory
        for main in self.dir:
          if os.path.exists(main):
            self.categories.append(main)
            
            # prepare subdirectories list
            sub = []
            self.categories.append(sub)

            # look through            
            for dir, subdirs, files in os.walk(main):
                name = os.path.basename(dir)
                while name in self.categories:
                    name = name + "2"
        
                # files in subdir
                if files:
                    sub.append(name)
                    self.streams[name] = [self.file_entry(fn, dir) for fn in files if self.we_like_that_extension(fn)]
                
            # plant a maindir reference to shortname
            self.streams[main] = self.streams[os.path.basename(main)]


    # extract meta data
    def file_entry(self, fn, dir):
        # basic data
        meta = {
            "title": fn,
            "filename": fn,
            "url": dir + "/" + fn,
            "genre": "",
            "format": self.mime_fmt(fn[-3:]),
            "editable": True,
        }
        # add ID3
        meta.update(mutagen_postprocess(get_meta(dir + "/" + fn) or {}))
        return meta
        
    # check fn for .ext
    def we_like_that_extension(self, fn):
        return fn[-3:] in self.ext
    


    # same as init
    def update_categories(self):
        self.scan_dirs()

        
    # same as init
    def update_streams(self, cat, x=0):
        self.scan_dirs()
        print(self.streams)
        print(self.categories)
        return self.streams.get(os.path.basename(cat))


