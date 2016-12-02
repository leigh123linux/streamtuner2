# encoding: UTF-8
# api: streamtuner2
# type: class
# title: global config object
# description: reads ~/.config/streamtuner/*.json files
# config:
#    { arg: -d,     type: str,      name: disable[], description: Omit plugin from initialization.  }
#    { arg: -e,     type: str,      name: enable[],  description: Add channel plugin.  }
#    { arg: --gtk3, type: boolean,  name: gtk3,      description: Start with Gtk3 interface. }
#    { arg: -D,     type: boolean,  name: debug,     description: Enable debug messages on console }
#    { arg: action, type: str *,    name: action[],  description: CLI interface commands. }
#    { arg: -x,     type: boolean,  name: exit,      hidden: 1 }
#    { arg: --nt,   type: boolean,  name: nothreads, description: Disable threading/gtk_idle UI. }
# version: 2.7
# priority: core
# depends: pluginconf >= 0.1, os, json, re, zlib, pkgutil
#
# Ties together the global conf.* object. It's typically used
# in the main application and modules with:
#
#   from config import *
#
# The underlying ConfigDict class is already instantiated and
# imported as `conf` then.
#
# With .save() or .load() it handles storage as JSON. Both
# utility functions are also used for other cache files.
# More specific config stores are available per .netrc(),
# and .init_args().
#
# Whereas plugin utility code is available per plugin_meta(),
# module_list(), and get_data(). There's a prepared function
# for add_plugin_config() on initialization.
#
# Also provides a simple logging interface with log.TYPE(...),
# which is also pre-instantiated.


from __future__ import print_function
import os, glob
import sys
import json
import gzip
import platform
import re
from compat2and3 import gzip_decode, find_executable, PY2, PY3
import zlib
import zipfile
import inspect
import pkgutil
import argparse
from pluginconf import plugin_meta, module_list, get_data
import pluginconf


# export symbols
__all__ = ["conf", "log", "plugin_meta", "module_list", "get_data", "find_executable"]


#-- create a stub instance of config object
conf = object()

# separate instance of netrc, if needed
netrc = None




# Global configuration store
#
# Autointializes itself on startup, makes conf.vars available.
# Also provides .load() and .save() for JSON data/cache files.
#
class ConfigDict(dict):

    args = {}

    # start
    def __init__(self):
    
        # object==dict means conf.var is conf["var"]
        self.__dict__ = self

        # prepare
        self.defaults()
        self.xdg()
        
        # runtime
        self.share = os.path.dirname(os.path.abspath(__file__))
        
        # settings from last session
        last = self.load("settings")
        if (last):
            if "share" in last:
                del last["share"]
            self.update(last)
            self.migrate()
        # store defaults in file
        else:
            self.save("settings")
            self.firstrun = 1

        # temporary files
        if not os.path.exists(self.tmp):
            os.mkdir(self.tmp)
        
        # add argv
        self.args = self.init_args(argparse.ArgumentParser())
        self.apply_args(self.args)


    # some defaults
    def defaults(self):
        self.windows = platform.system()=="Windows"
        self.play = {
           "audio/mpeg": self.find_player(),
           "audio/ogg": self.find_player(),
           "audio/*": self.find_player(),
           "video/youtube": self.find_player(typ="video") + " $(youtube-dl -g %srv)",
           "video/*": self.find_player(typ="video", default="vlc"),
           "url/http": self.find_player(typ="browser"),
        }
        self.record = {
           "audio/*": self.find_player(typ="xterm", append=' -e "streamripper %srv"'),   # -d /home/***USERNAME***/Musik
           "video/youtube": self.find_player(typ="video", append=' $("youtube-dl %srv")'),
        }
        self.specbuttons = {
           #"gtk-media-forward": "pavucontrol",
        }
        # Presets are redundant now. On first startup the `priority:` field of each plugin is checked.
        self.plugins = {
             # core plugins, cannot be disabled anyway
            "bookmarks": 1,
            "search": 1,
            "streamedit": 1,
            "configwin": 1,
        }
        self.tmp = os.environ.get("TEMP", "/tmp") + "/streamtuner2"
        self.nothreads = 0
        self.max_streams = "500"
        self.internetradio_max_pages = 5
        self.show_bookmarks = 1
        self.show_favicons = 1
        self.load_favicon = 1
        self.heuristic_bookmark_update = 0
        self.retain_deleted = 0
        self.auto_save_appstate = 1
        self.auto_save_stations = 0
        self.reuse_m3u = 1
        self.playlist_asis = 0
        self.window_title = 0
        self.google_homepage = 0
        self.open_mode = "r" if self.windows and PY2 else "rt"
        self.pyquery = 1
        self.debug = 0

    # update old setting names
    def migrate(self):
        # 2.1.7
        if self.tmp == "/tmp":
            self.tmp = "/tmp/streamtuner2"
        
    # Add plugin names and default config: options from each .meta
    def add_plugin_defaults(self, meta, name):
        pluginconf.add_plugin_defaults(self, self.plugins, meta, name)


    # look at system binaries for standard audio players
    def find_player(self, typ="audio", default="xdg-open", append=""):
        if self.windows:
            return self.find_player_win(typ, default)
        players = {  # linux
            "audio": ["audacious %m3u", "audacious2", "exaile %pls", "xmms2", "banshee", "amarok %pls", "clementine", "qmmp", "quodlibet", "aqualung", "mp3blaster %m3u", "vlc --one-instance", "totem"],
            "video": ["umplayer", "xnoise", "gxine", "totem", "vlc --one-instance", "parole", "smplayer", "gnome-media-player", "xine", "bangarang"],
            "browser": ["opera", "midori", "firefox", "sensible-browser"],
            "xterm": ["xfce4-terminal", "x-terminal-emulator", "gnome-terminal", "xterm", "rxvt"],
        }
        for bin in players[typ]:
            if find_executable(bin.split()[0]):
                return bin
        return default

    # Windows look for c:/program files/*/*.exe
    def find_player_win(self, typ="audio", default="wmplayer %asx", append=""):
        pf = os.environ["ProgramFiles"]
        base = [pf, "c:\\windows", "c:\\program files", "c:\\windows\\internet explorer\\"]
        players = {
            "audio": ["\\VideoLAN\\VLC*\\vlc.exe", "\\VLC*\\vlc.exe", "wmplayer.exe %asx"],
            "browser": ["\\Moz*\\firefox.exe", "iexplore.exe %url"],
            "xterm": ['/D "'+pf+'\\streamripper" streamripper.exe %srv']
        }
        typ = typ if typ in players else "audio"
        for bin in players[typ]:
            for b in base:
                fn = glob.glob(b + bin)
                if len(fn):
                    return re.sub("^(.+?)(\s%\w+)?$", '"\\g<1>"\\g<2>', fn[0], 1) + append
        return players[typ][-1]
    
        
    # http://standards.freedesktop.org/basedir-spec/basedir-spec-0.6.html
    def xdg(self, path="/streamtuner2"):
        home = os.environ.get("HOME", self.tmp)
        config = os.environ.get("XDG_CONFIG_HOME", os.environ.get("APPDATA", home+"/.config"))
        
        # storage dir
        self.dir = config + path
        
        # create if necessary
        if (not os.path.exists(self.dir)):
            os.makedirs(self.dir)
       

    # store some configuration list/dict into a file                
    def save(self, name="settings", data=None, gz=0, nice=0):
        name = name + ".json"
        if (data is None):
            data = vars(self)
            if "args" in data:
                data.pop("args")
            nice = 1
        # check for subdir
        if (name.find("/") > 0):
            subdir = name[0:name.find("/")]
            subdir = self.dir + "/" + subdir
            if (not os.path.exists(subdir)):
                os.mkdir(subdir)
                open(subdir+"/.nobackup", "w").close()
        # target filename
        file = self.dir + "/" + name
        # encode as JSON
        try:
            data = json.dumps(data, indent=(4 if nice else None), sort_keys=True)
        except Exception as e:
            log.ERR("JSON encoding failed", e)
            return
        # .gz or normal file
        if gz:
            f = gzip.open(file+".gz", "w")
            if os.path.exists(file):
                os.unlink(file)
        else:
            f = open(file, "w")
        # write
        try:
            f.write(data.encode("utf-8"))
        except TypeError as e:
            f.write(data)  # Python3 sometimes wants to write strings rather than bytes
        f.close()

    # retrieve data from config file            
    def load(self, name):
        name = name + ".json"
        file = self.dir + "/" + name
        try:
            # .gz or normal file
            if os.path.exists(file + ".gz"):
                f = gzip.open(file + ".gz", self.open_mode)
            elif os.path.exists(file):
                f = open(file, self.open_mode)
            else:
                return # file not found
            # decode
            r = json.load(f)
            f.close()
            return r
        except Exception as e:
            log.ERR("JSON parsing error (in "+name+")", e)
        
    # recursive dict update
    def update(self, with_new_data):
        for key,value in with_new_data.items():
            if type(value) == dict:
                self[key].update(value)
            else:
                self[key] = value
        # descends into sub-dicts instead of wiping them with subkeys

    # Shortcut to `state.json` loading (currently selected categories etc.)
    def state(self, module=None, d={}):
        if not d:
            d.update(conf.load("state") or {})
        if module:
            return d.get(module, {})
        return d

    # standard user account storage in ~/.netrc or less standard but contemporarily in ~/.config/netrc
    def netrc(self, varhosts=("shoutcast.com")):
        global netrc
        if not netrc:
            netrc = {}
            try:
                from netrc import netrc as parser
                try:
                     netrc = parser().hosts
                except:
                     netrc = parser(self.xdg() + "/netrc").hosts
            except:
                log.STAT("No .netrc")
        for server in varhosts:
            if server in netrc:
                return netrc[server]

    # Use config:-style definitions for argv extraction,
    # such as: { arg: -D, name: debug, type: bool }
    def init_args(self, ap):
        for opt in plugin_meta(frame=1).get("config"):
            kwargs = pluginconf.argparse_map(opt)
            if kwargs:
                #print(kwargs)
                ap.add_argument(*kwargs.pop("args"), **kwargs)
        return ap.parse_args()

    # Copy args fields into conf. dict
    def apply_args(self, args):
        self.debug = args.debug
        self.nothreads = args.nothreads
        if args.exit:
            sys.exit(1)
        for p_id in (args.disable or []):
            self.plugins[p_id] = 0
        for p_id in (args.enable or []):
            self.plugins[p_id] = 1


# Simplified print wrapper: `log.err(...)`
class log_printer(object):

    # Wrapper
    method = None
    def __getattr__(self, name):
        self.method = name
        return self.log_print
    
    # Printer
    def log_print(self, *args, **kwargs):
        # debug level
        method = self.method.upper()
        if method != "ERR":
            if "debug" in conf and not conf.debug:
                return
        # color/prefix
        method = r"[{}[{}][0m".format(self.colors.get(method.split("_")[0], "47m"), method)
        # output
        print(method + " " + " ".join([str(a) for a in args]), file=sys.stderr)

    # Colors
    colors = {
        "ERR":  "31m",          # red    ERROR
        "INIT": "38;5;196m",    # red    INIT ERROR
        "WARN": "38;5;208m",    # orange WARNING
        "EXEC": "38;5;66m",     # green  EXEC
        "PROC": "32m",          # green  PROCESS
        "FAVICON":"38;5;119m",  # green  FAVICON
        "CONF": "33m",          # brown  CONFIG DATA
        "DND":  "1;33;41m",     # yl/red DRAG'N'DROP
        "UI":   "34m",          # blue   USER INTERFACE BEHAVIOUR
        "UIKIT":"38;5;222;48;5;235m", # THREAD/UIKIT/IDLE TASKS
        "APPSTATE":"38;5;200m", # magenta APPSTATE RESTORE
        "HTTP": "35m",          # magenta HTTP REQUEST
        "DATA": "36m",          # cyan   DATA
        "INFO": "38;5;238m",    # lgray  INFO
        "STAT": "37m",          # gray   CONFIG STATE
    }

# instantiate right away
log = log_printer()


# populate global conf instance
conf = ConfigDict()
log.PROC("ConfigDict() initialized")

# tie in pluginconf.*
pluginconf.log_ERR = log.ERR
pluginconf.module_base = "config"
pluginconf.plugin_base = ["channels", "plugins"]#, conf.share+"/channels", conf.dir+"/plugins"]

