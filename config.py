#
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
#
# In the main application or module files which need access
# to a global conf.* object, just import this module as follows:
#
#   from config import *
#
# Here conf is already an instantiation of the underlying
# ConfigDoct class.
#
# Also provides the logging function log.TYPE(...) and basic
# plugin handling code: plugin_meta() and module_list(),
# and the relative get_data() alias (files from pyzip/path).
#

from __future__ import print_function
import os
import sys
import json
import gzip
import platform
import re
from compat2and3 import gzip_decode, find_executable
import zlib
import zipfile
import inspect
import pkgutil
import argparse

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
        self.__dict__ = self  # let's pray this won't leak memory due to recursion issues

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
        self.play = {
           "audio/mpeg": self.find_player(),
           "audio/ogg": self.find_player(),
           "audio/*": self.find_player(),
           "video/youtube": self.find_player(typ="video") + " $(youtube-dl -g %srv)",
           "video/*": self.find_player(typ="video", default="vlc"),
           "url/http": self.find_player(typ="browser"),
        }
        self.record = {
           "audio/*": self.find_player(typ="xterm") + " -e streamripper %srv",   # -d /home/***USERNAME***/Musik
           "video/youtube": self.find_player(typ="xterm") + " -e \"youtube-dl %srv\"",
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
        self.show_bookmarks = 1
        self.show_favicons = 1
        self.load_favicon = 1
        self.heuristic_bookmark_update = 0
        self.retain_deleted = 0
        self.auto_save_appstate = 1
        self.reuse_m3u = 1
        self.playlist_asis = 0
        self.google_homepage = 0
        self.windows = platform.system()=="Windows"
        self.pyquery = 1
        self.debug = 0

        
    # each plugin has a .config dict list, we add defaults here
    def add_plugin_defaults(self, meta, module=""):
    
        # options
        config = meta.get("config", [])
        for opt in config:
            if ("name" in opt) and ("value" in opt) and (opt["name"] not in vars(self)):
                self.__dict__[opt["name"]] = opt["value"]

        # plugin state
        if module and module not in conf.plugins:
             conf.plugins[module] = meta.get("priority") in ("core", "builtin", "always", "default", "standard")


    # look at system binaries for standard audio players
    def find_player(self, typ="audio", default="xdg-open"):
        players = {
           "audio": ["audacious %m3u", "audacious2", "exaile %pls", "xmms2", "banshee", "amarok %pls", "clementine", "qmmp", "quodlibet", "aqualung", "mp3blaster %m3u", "vlc --one-instance", "totem"],
           "video": ["umplayer", "xnoise", "gxine", "totem", "vlc --one-instance", "parole", "smplayer", "gnome-media-player", "xine", "bangarang"],
           "browser": ["opera", "midori", "sensible-browser"],
           "xterm": ["xfce4-terminal", "x-termina-emulator", "gnome-terminal", "xterm", "rxvt"],
        }
        for bin in players[typ]:
            if find_executable(bin.split()[0]):
                return bin
        return default

        
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
            data = json.dumps(data, indent=(4 if nice else None))
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
                f = gzip.open(file + ".gz", "rt")
            elif os.path.exists(file):
                f = open(file, "rt")
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


    # update old setting names
    def migrate(self):
        # 2.1.1
        if "audio/mp3" in self.play:
            self.play["audio/mpeg"] = self.play["audio/mp3"]
            del self.play["audio/mp3"]
        if self.tmp == "/tmp":
            self.tmp = "/tmp/streamtuner2"

            
    # Shortcut to `state.json` loading (currently selected categories etc.)
    def state(self, module=None, d={}):
        if not d:
            d.update(conf.load("state") or {})
        if module:
            return d.get(module, {})
        return d

         
    # check for existing filename in directory list
    def find_in_dirs(self, dirs, file):
        for d in dirs:
            if os.path.exists(d+"/"+file):
                return d+"/"+file


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
        for opt in plugin_meta(frame=0).get("config"):
            kwargs = self.argparse_map(opt)
            if kwargs:
                #print kwargs
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


    # Transform config: description into quirky ArgumentParser args.
    #
    # · An option entry requires an arg: parameter - unlike regular plugin options:
    #     { arg: -i, name: input[], type: str, description: input files }
    # · Where list elements are indicated by appending `[]` to names, or `*`onto type
    #   specifiers (alternatively `?`, `+` or a numeric count).
    # · Types `str` or `int` and `bool` are recognized (bool with false/true optionals).
    # · Entries can also carry a `hidden: 1` or `required: 1` attribute.
    # · And `help:` is an alias to `description:`
    # · Same for `default:` instead of the normal `value:`
    # · And `type: select` utilizes the `select: a|b|c` format as uaual.
    # · ArgParsers const=, metavar= flag, or type=file are not aliased here.
    #
    def argparse_map(self, opt):
        if not ("arg" in opt and opt["name"] and opt["type"]):
            return {}

        # Extract --flag names
        args = opt["arg"].split() + re.findall("-+\w+", opt["name"])

        # Prepare mapping options
        typing = re.findall("bool|str|\[\]|const|false|true", opt["type"])
        naming = re.findall("\[\]", opt["name"])
        name   = re.findall("(?<!-)\\b\\w+", opt["name"])
        nargs  = re.findall("\\b\d+\\b|[\?\*\+]", opt["type"]) or [None]
        is_arr = "[]" in (naming + typing) and nargs == [None]
        is_bool= "bool" in typing
        false_b = "false" in typing or opt["value"] in ("0", "false")
        #print "\nname=", name, "is_arr=", is_arr, "is_bool=", is_bool, "bool_d=", false_b, "naming=", naming, "typing=", typing

        # Populate partially - ArgumentParser has aversions to many parameter combinations
        kwargs = dict(
            args     = args,
            dest     = name[0] if not name[0] in args else None,
            action   = is_arr and "append"  or  is_bool and false_b and "store_false"  or  is_bool and "store_true"  or  "store",
            nargs    = nargs[0],
            default  = opt.get("default") or opt["value"],
            type     = None if is_bool  else  ("int" in typing and int  or  "bool" in typing and bool  or  str),
            choices  = opt["select"].split("|") if "select" in opt else None,
            required = "required" in opt or None,
            help     = opt["description"] if not "hidden" in opt else argparse.SUPPRESS
        )
        return {k:w for k,w in kwargs.items() if w is not None}


# Retrieve content from install path or pyzip archive (alias for pkgutil.get_data)
#
def get_data(fn, decode=False, gz=False, file_base="config"):
    try:
        bin = pkgutil.get_data(file_base, fn)
        if gz:
            bin = gzip_decode(bin)
        if decode:
            return bin.decode("utf-8", errors='ignore')
        else:
            return str(bin)
    except:
        log.WARN("get_data() didn't find:", fn)


# Search through ./channels/ and get module basenames.
# (Reordering channel tabs is now done by uikit.apply_state.)
#
def module_list(plugin_base="channels"):

    # Should list plugins within zips as well as local paths
    ls = pkgutil.iter_modules([plugin_base, conf.share+"/"+plugin_base, conf.dir+"/plugins"])
    return [name for loader,name,ispkg in ls]



# Plugin meta data extraction
#
# Extremely crude version for Python and streamtuner2 plugin usage.
# But can fetch from different sources:
#  · fn= to read from literal files, out of a .pyzip package
#  · src= to extract from pre-read script code
#  · module= utilizes pkgutil to read 
#  · frame= automatically extract comment header from caller
#
plugin_base = ("channels", "plugins")
def plugin_meta(fn=None, src=None, module=None, frame=1):

    # try via pkgutil first
    if module:
       fn = module
       for base in plugin_base:
           try:
               src = pkgutil.get_data(base, fn+".py")
               if src: break
           except:
               continue  # plugin_meta_extract() will print a notice later

    # get source directly from caller
    elif not src and not fn:
        module = inspect.getmodule(sys._getframe(frame))
        fn = inspect.getsourcefile(module)
        src = inspect.getcomments(module)

    # real filename/path
    elif fn and os.path.exists(fn):
        src = open(fn).read(4096)

    # assume it's within a zip
    elif fn:
        intfn = ""
        while fn and len(fn) and not os.path.exists(fn):
            fn, add = os.path.split(fn)
            intfn = add + "/" + intfn
        if len(fn) >= 3 and intfn and zipfile.is_zipfile(fn):
            src = zipfile.ZipFile(fn, "r").read(intfn.strip("/"))
            
    if not src:
        src = ""
    if type(src) is not str:
        src = src.decode("utf-8", errors='replace')

    return plugin_meta_extract(src, fn)


# Actual comment extraction logic
def plugin_meta_extract(src="", fn=None, literal=False):

    # defaults
    meta = {
        "id": os.path.splitext(os.path.basename(fn or "")),
        "fn": fn,
        "title": fn, "description": "no description", "config": [],
        "type": "module", "api": "python", "doc": ""
    }

    # extract coherent comment block, split doc section
    if not literal:
        src = rx.comment.search(src)
        if not src:
            log.ERR("Couldn't read source meta information:", fn)
            return meta
        src = src.group(0)
        src = rx.hash.sub("", src).strip()
    
    # split comment block
    if src.find("\n\n") > 0:
        src, meta["doc"] = src.split("\n\n", 1)

    # key:value fields into dict
    for field in rx.keyval.findall(src):
        meta[field[0]] = field[1].strip()
    meta["config"] = plugin_meta_config(meta.get("config") or "")

    return meta

# Unpack config: structures
def plugin_meta_config(str):
    config = []
    for entry in rx.config.findall(str):
        opt = { "type": None, "name": None, "description": "", "value": None }
        for field in rx.options.findall(entry):
            opt[field[0]] = (field[1] or field[2] or field[3] or "").strip()
        config.append(opt)
    return config

# Comment extraction regexps
class rx:
    comment = re.compile(r"""(^ {0,4}#.*\n)+""", re.M)
    hash    = re.compile(r"""(^ {0,4}# *)""", re.M)
    keyval  = re.compile(r"""
        ^([\w-]+):(.*$(?:\n(?![\w-]+:).+$)*)      # plain key:value lines
    """, re.M|re.X)
    config  = re.compile(r"""
        [\{\<] (.+?) [\}\>]                    # JSOL/YAML scheme {...} dicts
    """, re.X)
    options = re.compile(r"""
        ["':$]?   (\w*)  ["']?                 # key or ":key" or '$key'
        \s* [:=] \s*                           # "=" or ":"
     (?:  "  ([^"]*)  " 
       |  '  ([^']*)  '                        #  "quoted" or 'singl' values
       |     ([^,]*)                           #  or unquoted literals
     )
    """, re.X)



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
        "FAVICON":"58;5;119m",  # green  FAVICON
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



   

#-- populate global conf instance
conf = ConfigDict()
log.PROC("ConfigDict() initialized")
