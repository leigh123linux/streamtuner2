#
# encoding: UTF-8
# api: streamtuner2
#  .2
# type: class
# title: global config object
# description: reads ~/.config/streamtuner/*.json files
# config: {type:var, name:z, description:v}
#
# In the main application or module files which need access
# to a global conf object, just import this module as follows:
#
#   from config import conf
#
# Here conf is already an instantiation of the underlying
# Config class.
#


import os
import sys
import json
import gzip
import platform
import re
import zipfile
import inspect


# export symbols
__all__ = ["conf", "__print__", "dbg", "plugin_meta"]



#-- create a single instance of config object
conf = object()


#-- global configuration data               ---------------------------------------------
class ConfigDict(dict):


        # start
        def __init__(self):
        
            # object==dict means conf.var is conf["var"]
            self.__dict__ = self  # let's pray this won't leak memory due to recursion issues

            # prepare
            self.defaults()
            self.xdg()
            
            # runtime
            self.share = os.path.dirname(__file__)
            
            # settings from last session
            last = self.load("settings")
            if (last):
                self.update(last)
                self.migrate()
            # store defaults in file
            else:
                self.save("settings")
                self.firstrun = 1


        # some defaults
        def defaults(self):
            self.play = {
               "audio/mpeg": "audacious ",	# %u for url to .pls, %g for downloaded .m3u
               "audio/ogg": "audacious ",
               "audio/*": "audacious ",
               "video/youtube": "totem $(youtube-dl -g %srv)",
               "video/*": "vlc --one-instance %srv",
               "url/http": "sensible-browser",
            }
            self.record = {
               "audio/*": "xterm -e streamripper %srv",   # -d /home/***USERNAME***/Musik
               "video/youtube": "xterm -e \"youtube-dl %srv\"",
            }
            self.plugins = {
                "bookmarks": 1, # built-in plugin, cannot be disabled
                "shoutcast": 1,
                "xiph": 1,
                "modarchive": 0, # disable per default
                "file": 0,      # disable per default
                "punkcast": 0,  # disable per default
                "history": 0,
                "basicch": 0,   # ceased
                "tv": 0,        # ceased
            }
            self.tmp = os.environ.get("TEMP", "/tmp")
            self.max_streams = "500"
            self.show_bookmarks = 1
            self.show_favicons = 1
            self.load_favicon = 1
            self.heuristic_bookmark_update = 0
            self.retain_deleted = 0
            self.auto_save_appstate = 1
            self.theme = "" #"MountainDew"
            self.channel_order = "shoutcast, xiph, internet_radio, jamendo, myoggradio, .."
            self.reuse_m3u = 1
            self.google_homepage = 0
            self.windows = platform.system()=="Windows"
            self.pyquery = 1
            self.debug = 0

            
        # each plugin has a .config dict list, we add defaults here
        def add_plugin_defaults(self, config, module=""):
        
            # options
            for opt in config:
                if ("name" in opt) and ("value" in opt) and (opt["name"] not in vars(self)):
                    self.__dict__[opt["name"]] = opt["value"]

            # plugin state
            if module and module not in conf.plugins:
                 conf.plugins[module] = 1

        
            
        # http://standards.freedesktop.org/basedir-spec/basedir-spec-0.6.html
        def xdg(self):
            home = os.environ.get("HOME", self.tmp)
            config = os.environ.get("XDG_CONFIG_HOME", os.environ.get("APPDATA", home+"/.config"))
            
            # storage dir
            self.dir = config + "/streamtuner2"
            
            # create if necessary
            if (not os.path.exists(self.dir)):
                os.makedirs(self.dir)
           

        # store some configuration list/dict into a file                
        def save(self, name="settings", data=None, gz=0, nice=0):
            name = name + ".json"
            if (data is None):
                data = dict(self.__dict__)  # ANOTHER WORKAROUND: typecast to plain dict(), else json filter_data sees it as object and str()s it
                nice = 1
            # check for subdir
            if (name.find("/") > 0):
                subdir = name[0:name.find("/")]
                subdir = self.dir + "/" + subdir
                if (not os.path.exists(subdir)):
                    os.mkdir(subdir)
                    open(subdir+"/.nobackup", "w").close()
            # write                        
            file = self.dir + "/" + name
            # .gz or normal file
            if gz:
                f = gzip.open(file+".gz", "w")
                if os.path.exists(file):
                    os.unlink(file)
            else:
                f = open(file, "w")
            # encode
            data = json.dumps(data, indent=(4 if nice else None))
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
                print(dbg.ERR, "PSON parsing error (in "+name+")", e)
            

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

             
        # check for existing filename in directory list
        def find_in_dirs(self, dirs, file):
            for d in dirs:
                if os.path.exists(d+"/"+file):
                    return d+"/"+file



# Plugin meta data extraction
#
# Extremely crude version for Python and streamtuner2 plugin usage.
# Doesn't check top-level comment coherency.
# But supports plugins within python zip archives.
#
rx_zipfn  = re.compile(r"""^(.+\.(?:zip|pyz|pyzw|pyzip)(?:\.py)?)/(\w.*)$""")
rx_meta   = re.compile(r"""^ {0,4}# *([\w-]+): *(.+(\n *#  +(?![\w-]+:).+)*)$""", re.M)  # Python comments only
rx_lines  = re.compile(r"""\n *# """)        # strip multi-line prefixes
rx_config = re.compile(r"""[\{\<](.+?)[\}\>]""")     # extract only from JSOL/YAML scheme
rx_fields = re.compile(r"""["']?(\w+)["']?\s*[:=]\s*["']?([^,]+)(?<!["'])""")  # simple key: value entries
#
def plugin_meta(fn=None, frame=1, src=""):

    # filename of caller
    if not fn:
        fn = inspect.getfile(sys._getframe(frame))

    # within zip archive?
    zip = rx_zipfn.match(fn)
    if zip and zipfile.is_zipfile(zip.group(1)):
        src = zipfile.ZipFile(zip.group(1), "r").read(zip.group(2))
    else:
        src = open(fn).read(4096)

    # defaults
    meta = {
        "fn": fn,
        "id": os.path.basename(fn).replace(".py", "")
    }
    # extraction
    for field in rx_meta.findall(src):
        meta[field[0]] = rx_lines.sub("", field[1])

    # unpack config: structures
    meta["config"] = [
        dict([field for field in rx_fields.findall(entry)])
        for entry in rx_config.findall(meta.get("config", ""))
    ]
        
    return meta







# wrapper for all print statements
def __print__(*args):
    if conf.debug:
        print(" ".join([str(a) for a in args]))


# error colorization
dbg = type('obj', (object,), {
    "ERR":  r"[31m[ERR][0m",  # red    ERROR
    "INIT": r"[31m[INIT][0m", # red    INIT ERROR
    "PROC": r"[32m[PROC][0m", # green  PROCESS
    "CONF": r"[33m[CONF][0m", # brown  CONFIG DATA
    "UI":   r"[34m[UI][0m",   # blue   USER INTERFACE BEHAVIOUR
    "HTTP": r"[35m[HTTP][0m", # magenta HTTP REQUEST
    "DATA": r"[36m[DATA][0m", # cyan   DATA
    "INFO": r"[37m[INFO][0m", # gray   INFO
    "STAT": r"[37m[STATE][0m", # gray  CONFIG STATE
})


   
#-- actually fill global conf instance
conf = ConfigDict()
if conf:
    __print__(dbg.PROC, "ConfigDict() initialized")

