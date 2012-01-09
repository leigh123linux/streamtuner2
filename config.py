#
# encoding: UTF-8
# api: streamtuner2
# type: class
# title: global config object
# description: reads ~/.config/streamtuner/*.json files
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
import pson
import gzip


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
            dirs = ["/usr/share/streamtuner2", "/usr/local/share/streamtuner2", sys.path[0], "."]
            self.share = [d for d in dirs if os.path.exists(d)][0]
            
            # settings from last session
            last = self.load("settings")
            if (last):
                self.update(last)
            # store defaults in file
            else:
                self.save("settings")
                self.firstrun = 1

        # some defaults
        def defaults(self):
            self.browser = "sensible-browser"
            self.play = {
               "audio/mp3": "audacious ",	# %u for url to .pls, %g for downloaded .m3u
               "audio/ogg": "audacious ",
               "audio/aac": "amarok -l ",
               "audio/x-pn-realaudio": "vlc ",
               "audio/*": "totem ",
               "*/*": "vlc %srv",
            }
            self.record = {
               "*/*": "x-terminal-emulator -e streamripper %srv",
                    #  x-terminal-emulator -e streamripper %srv -d /home/***USERNAME***/Musik
            }
            self.plugins = {
                "bookmarks": 1,  # built-in plugins, cannot be disabled
                "shoutcast": 1,
                "punkcast": 0,   # disable per default
            }
            self.tmp = os.environ.get("TEMP", "/tmp")
            self.max_streams = "120"
            self.show_bookmarks = 1
            self.show_favicons = 1
            self.load_favicon = 1
            self.heuristic_bookmark_update = 1
            self.retain_deleted = 1
            self.auto_save_appstate = 1
            self.theme = "" #"MountainDew"
            self.debug = False
            self.channel_order = "shoutcast, xiph, internet_radio_org_uk, jamendo, myoggradio, .."
            self.reuse_m3u = 1
            self.google_homepage = 1

            
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
            config = os.environ.get("XDG_CONFIG_HOME", home+"/.config")
            
            # storage dir
            self.dir = config + "/" + "streamtuner2"
            
            # create if necessary
            if (not os.path.exists(self.dir)):
                os.makedirs(self.dir)
           

        # store some configuration list/dict into a file                
        def save(self, name="settings", data=None, gz=0, nice=0):
            name = name + ".json"
            if (data == None):
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
            pson.dump(data, f, indent=(4 if nice else None))
            f.close()


        # retrieve data from config file            
        def load(self, name):
            name = name + ".json"
            file = self.dir + "/" + name
            try:
                # .gz or normal file
                if os.path.exists(file + ".gz"):
                    f = gzip.open(file + ".gz", "r")
                elif os.path.exists(file):
                    f = open(file, "r")
                else:
                    return # file not found
                # decode
                r = pson.load(f)
                f.close()
                return r
            except (Exception), e:
                print("PSON parsing error (in "+name+")", e)
            

        # recursive dict update
        def update(self, with_new_data):
            for key,value in with_new_data.iteritems():
                if type(value) == dict:
                    self[key].update(value)
                else:
                    self[key] = value
            # descends into sub-dicts instead of wiping them with subkeys
             

   
#-- actually fill global conf instance
conf = ConfigDict()


