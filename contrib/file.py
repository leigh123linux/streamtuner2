# api: streamtuner2
# title: File browser
# description: Displays mp3/oggs or m3u/pls files from local media file directories.
# type: channel
# category: local
# version: 0.2
# priority: optional
# status: unsupported
# depends: python:mutagen, python:id3
# config:  
#   { name: file_browser_dir, type: text, value: "$XDG_MUSIC_DIR, ~/MP3", description: "List of directories to scan for audio files." },
#   { name: file_browser_ext, type: text, value: "mp3,ogg, m3u,pls,xspf, avi,flv,mpg,mp4", description: "File type/extension filter." },
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABQAAAAPCAYAAADkmO9VAAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3wUFDQsK23vYngAAA6lJREFUOMtFz8tu1FYAxvH/sc+xxx7bM8lkElAgISoV4qIgpEaomwg2bMqiQmo3lfowPElVVbQr3gBVqGJRGi6VEERFDROS0Ewmc/N47Bkf+7gLevke4Kfv
#   L374/vufxm/ffjnudJQoisoVonLDcN+sr39z7uXLXzfOn6cRhmSTCf3TUwa9HoN+H601ynXxwhA7ivhdCH48PkZOut0vdh48cKtej9C2iSyLsF7/xLpx4/5eu/1LZzSiaQx1z8O5cIHapUvVmpRkaUqcJMRpSjydmnEcP/2zKH6WOs/7mdZBVVXIqsKuKk4nE4qdnTueUncCpZh5HoHj4AqBVRQIrUFrLGPwlaLhOLiWtX93OPxKIuX+0HHWJ5ZF03VxpaRfFLRmM1rTKUGrRX1piUYQEIUhfhRRC0OqOMZxHIIwJIgiHFj77OnT+7KEd0Wt
#   tl0Kgev7NHyf5apCTSaoLEMlCZdu3uT85ib1hQWi1VWcMCTb3cXxPJxmExlF2LWaMFpvS4TYcx2nmpalsKoKJQSNMCQ6cwZPCMxgwKTbpfPoETWlWDx3jtblyyghEFpjSYmwbYQx6DyPJUJ0bKUKU5Yqn83QSqGVolQKGQSEGxssrK3RffyY6Zs3zK9epb6wgBWGCCFQjkOlFFVRoIfDkTRwYIRIDTR0nqPnc7RSFP/AhW2jfJ/WlSvQ7zPe3SU9OECdPYuwbUrXxSiFsW2KOB7IaZYdp3keV9DQ8znacSj+RaWkqtVACExR0NrcZPriBflw
#   SJqmWO32R9BxMEAxnfatJE37cZb1jWVRaP3x4XxOkecIy0J6HibPmY1GqHqdpa0tbNdlvLNDfnJCOR5jJhPMYECZpj2JlPEwSbqBEFTG/Jd85fZtNm/dIjk6Itnbw19e5tN79yiHQ5JnzxgfHDBrNvGjCOM4lElCkWWn1ufb2/M4TQ9LIQAoiwJTlrQ3NrCVQjoOw04Hf2UF5ftI3wchsOt1Zu/eoTsd9KtX5E+eYCaTnux2u1VRVe8N/y/PMn57+JBka4v04IDs8JDD+RxGI8RoxPz1a6yyJJ/PGT9/rivXzZRSp3m9/kYAtFdWvm3PZt+1
#   kkQEtk1g2wRSEihV+badR7Va2vS8ceR5A9uYrimKv/LZ7MhU1VF7efnD2sWL3cb6+slzrT9IgKXFxT8W07S33GpZywsLHxzLep/Gcac3Gu0H9fp7Z3X1KLp27WT9+vXh8epq8vXdu7N+FPG61UIXBXZZAmCVJX8DADze5LjPkMQAAAAldEVYdGRhdGU6Y3JlYXRlADIwMTUtMDUtMDVUMTU6MTA6NTkrMDI6MDBD/PY6AAAAJXRFWHRkYXRlOm1vZGlmeQAyMDE1LTA1LTA1VDE1OjEwOjU5KzAyOjAwMqFOhgAAAABJRU5ErkJggg==
# png-orig:
#   https://openclipart.org/detail/168001/folder-icon-red-music
# extraction-method: os
#
# Local file browser. Presents files from configured directories.
# This is not what streamtuner2 is meant for. Therefore this is
# an optional plugin, and not overly well integrated.
#
# Bugs:
# Only loads directories on startup. Doesn't work when post-activated
# per pluginmanager2 for instance. And LANG=C breaks it on startup,
# if media directories contain anything but ASCII filenames.


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
        log.INFO("Just basic ID3 support")
        get_meta = lambda fn: dict([(k.lower(),v) for k,v in ID3(fn).iteritems()])
    except:
        log.INIT("You are out of luck in regards to mp3 browsing. No ID3 support.")
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

    # data
    listtype = "href"
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
        self.dir = [self.env_dir(s) for s in conf.file_browser_dir.split(",")]
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


    # Interpolate $VARS and XDG_SPECIAL_DIRS
    def env_dir(self, path):
        path = path.strip()
        env = self.fvars()
        # Replace $XDG_ ourselfes and normal $ENV vars per expandvars (because os.environ.update() doesn't do)
        path = re.sub("\$(XDG\w+)", lambda m: env.get(m.group(1), m.group(0)), path)
        path = os.path.expandvars(path)
        return os.path.expanduser(path)

    # Read user-dirs config
    def fvars(self, fn="$HOME/.config/user-dirs.dirs"):
        fn = os.path.expandvars(fn)
        src = open(fn, "r").read() if os.path.exists(fn) else ""
        env = re.findall('^(\w+)=[\"\']?(.+?)[\"\']?', src, re.M)  # pyxdg: Your move.
        return dict(env)

    
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
                sfx = ""
                while name+sfx in self.categories:
                    sfx = str(int(sfx)+1) if sfx else "2"
                name += sfx
        
                # files in subdir
                if files:
                    sub.append(name)
                    self.streams[name] = [self.file_entry(fn, dir) for fn in files if self.we_like_that_extension(fn)]
                
            # plant a maindir reference to shortname
            main_base = os.path.basename(main)
            if self.streams.get(main_base):
                self.streams[main] = self.streams[main_base]


    # extract meta data
    def file_entry(self, fn, dir):
        # basic data
        meta = {
            "title": fn,
            "filename": fn,
            "url": "file://" + dir + "/" + fn,
            "genre": "",
            "format": mime_fmt(fn[-3:]),
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
        return self.streams.get(os.path.basename(cat))


