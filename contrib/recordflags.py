# encoding: utf-8
# api: streamtuner2
# title: Recording options
# description: Allows to set streamripper/fIcy options before recording
# version: 0.8.5
# depends: streamtuner2 > 2.2.0
# conflicts: continuous_record
# priority: optional
# config:
#    { name: recordflags_auto, type: bool, value: 1, description: Apply options automatically once saved. }
#    { name: recordflags_row, type: select, value: record_flags, select: "record_flags|extras", description: Station field for saved options. }
#    { name: recordflags_dir, type: str, value: "", description: Default output directory. }
# type: handler
# category: ui
#
# Hijacks the ● record button, presents an option dialog to set various
# streamripper options. Allows to set an output directory or single-file
# recording for example.
#
# Reuses the known option scheme from the config window. Which is perhaps
# less pretty than a custom dialog, but allows to set options for different
# download/recording tools: streamripper, fPls, youtube-dl, wget.
#
# Note that predefining -flags in the Apps/Recording config table might
# conflict with per-stream options. In particular avoid a -d directory
# default for streamripper; and use this plugins´ option instead.
#
# ToDo:
#  → override main.record() instead of action.record
#  → eventually strip defaults such as `-d ../dir` from conf.record;
#    using action append= param now, thus no rewriting of assoc dict
#


import re
import os
import copy
from config import *
from channels import *
from uikit import *
import action
from compat2and3 import *


# hook record button / menu / action
class recordflags (FeaturePlugin):

    # settings
    cfg_widget_pfx = "recordoptions_config_"
    widgets = {}
    
    # available options per recording tool
    flag_meta = {
        "streamripper": {
            "title": "streamripper",
            "priority": "required",
            "type": "app",
            "category": "recording",
            "version": "1.64.6",
            "description": "Standard radio/stream recording tool",
            "doc": "streamripper is the standard tool for recording and extracting songs from internet radio stations. It does have a plethora of options, some of which are available here:",
            "config": [
                #{ "name": "A",	"arg": "-A",	"type": "bool",	"description": "<b>-A</b> Don't split individual tracks/MP3s", "value": False },
                { "name": "Aa",	"arg": "-A -a",	"type": "str",	"description": "<b>-a</b> Single MP3 output filename. (Instead of splitting by song.)", "value": "" },
                { "name": "dir", "arg": "-d",	"type": "str",	"description": "<b>-d</b> Destination directory", "value": "" },
                { "name": "D",	"arg": "-D",	"type": "str",	"description": "<b>-D</b> Filename pattern", "value": "" },
                { "name": "s",	"arg": "-s",	"type": "bool",	"description": "<b>-s</b> No subdirectories for each stream", "value": False },
                { "name": "o",	"arg": "-o",	"type": "select",	"description": "<b>-o</b> Incomplete track overwriting", "select": "|always|never|larger|version", "value": "" },
                { "name": "t",	"arg": "-t",	"type": "bool",	"description": "<b>-t</b> Never overwrite incomplete tracks", "value": False, "category": "extra" },
                { "name": "T",	"arg": "-T",	"type": "bool",	"description": "<b>-T</b> Truncate duplicated incompletes", "value": False, "category": "extra" },
                { "name": "l",	"arg": "-l",	"type": "int",	"description": "<b>-l</b> Seconds to record", "value": 0, "max": 7*24*3600 },
                { "name": "M",	"arg": "-M",	"type": "int",	"description": "<b>-M</b> Max megabytes to record", "value": 512 },
                { "name": "xs2", "arg": "--xs2", "type": "bool", "description": "<b>--xs2</b> New pause detection algorithm", "value": False },
                { "name": "xsnone", "arg": "--xs-none", "type": "bool", "description": "<b>--xs-none</b> No silence splitting", "value": False, "category": "extra" },
                { "name": "i",	"arg": "-i",	"type": "bool", "description": "<b>-i</b> Don't add any ID3 tags", "value": False, "category": "extra" },
                { "name": "id3v1", "arg": "--with-id3v1", "type": "bool", "description": "<b>--with-id3v1</b> Add ID3v1 tags", "value": False, "category": "extra" },
                { "name": "noid3v2", "arg": "--without-id3v2", "type": "bool", "description": "<b>--without-id3v2</b> Omit ID3v2 tags", "value": False, "category": "verbose" },
                { "name": "cs_fs", "arg": "--codeset-filesys", "type": "str", "description": "Charset filesystem", "value": "", "category": "extra" },
                { "name": "cs_id3", "arg": "--codeset-id3", "type": "str", "description": "Charset ID3 tags", "value": "", "category": "extra" },
                { "name": "u",	"arg": "-u",	"type": "str", "description": "<b>-u</b> User-agent (browser id)", "value": "", "category": "extra" },
                { "name": "p",	"arg": "-p",	"type": "str", "description": "<b>-p</b> Url for HTTP proxy to use", "value": "", "category": "extra" },
                { "name": "r",	"arg": "-r",	"type": "str", "description": "<b>-r</b> Relay server 'localhost:8000'", "value": "", "category": "extra" },
                { "name": "m",	"arg": "-m",	"type": "int", "description": "<b>-m</b>Timeout for stalled connection", "value": 15, "category": "verbose" },
                { "name": "debug", "arg": "--debug", "type": "bool", "description": "<b>--debug</b> Extra verbosity", "value": False, "category": "verbose"},
            ]
        },
        "fPls": {
            "title": "fPls/fIcy",
            "priority": "required",
            "type": "app",
            "category": "recording",
            "version": "1.0.19",
            "description": "Alternative station recording tool",
            "config": [
                { "name": "max", "arg": "-M", "type": "int", "description": "<b>-M</b> Maximum cumulative playing time", "value": 0 },
                { "name": "loop", "arg": "-L", "type": "int", "description": "<b>-L</b> Maximum playlist loops", "value": 0 },
                { "name": "retry", "arg": "-R", "type": "int", "description": "<b>-R</b> Maximum per-stream retries", "value": 0 },
                { "name": "redir", "arg": "-l", "type": "int", "description": "<b>-l</b> Redirect follow limit", "value": 0 },
                { "name": "fail", "arg": "-T", "type": "int", "description": "<b>-T</b> Wait time after failure", "value": 0 },
                { "name": "daemon", "arg": "-i", "type": "int", "description": "<b>-i</b> Max network idle seconds", "value": 0 },
                { "name": "authfn", "arg": "-a", "type": "str", "description": "<b>-a</b> HTTP auth file (user:pass)", "value": "", "category": "extra" },
                { "name": "verbose", "arg": "-v", "type": "bool", "description": "<b>-v</b> Verbose mode", "value": False, "category": "verbose" },
                { "name": "daemon", "arg": "-d", "type": "str", "description": "<b>-d</b> Daemon mode: log file", "value": "", "category": "verbose" },
                { "name": "ficy", "arg": "-P", "type": "str", "description": "<b>-P</b> Path to fIcy", "value": "", "category": "extra" },
            ]
        },
        "youtube-dl": {
            "title": "youtuble-dl",
            "priority": "required",
            "type": "app",
            "category": "download",
            "version": "2017.02.11.3",
            "description": "Youtube downloader",
            "config": [
                { "name": "freeformats", "arg": "--prefer-free-formats", "type": "bool", "description": "Prefer free audio formats", "value": False },
                { "name": "format", "arg": "-f", "type": "select", "select": "=any|b=best|249=webm audio only DASH|250=webm audio only DASH|140=m4a audio only DASH|171=webm audio only DASH|251=webm audio only DASH|278=webm 256x144 DASH|160=mp4 256x144 DASH|242=webm 426x240 DASH|133=mp4 426x240 DASH|243=webm 640x360 DASH|134=mp4 640x360 DASH|244=webm 854x480 DASH|135=mp4 854x480 DASH|247=webm 1280x720 DASH|136=mp4 1280x720 DASH|248=webm 1920x1080 DASH|137=mp4 1920x1080 DASH|17=3gp 176x144 small|36=3gp 320x180 small|43=webm 640x360 medium|18=mp4 640x360 medium|22=mp4 1280x720 hd720", "description": "<b>-f</b> Format", "value": "b" },
                { "name": "c", "arg": "-c", "type": "bool", "description": "<b>-c</b> Continue partial downloads ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ", "value": True },
                { "name": "netrc", "arg": "-n", "type": "bool", "description": "<b>-n</b> Use .netrc for auth/login", "value": False, "category": "extra" },
                { "name": "ignore", "arg": "-i", "type": "bool", "description": "<b>-i</b> Ignore errors", "value": False },
                { "name": "proxy", "arg": "--proxy", "type": "str", "description": "<b>-p</b> Proxy", "value": "", "category": "extra" },
                { "name": "verbose", "arg": "-v", "type": "bool", "description": "<b>-v</b> Verbose mode", "value": False, "category": "verbose" },
                { "name": "ipv4", "arg": "-4", "type": "bool", "description": "<b>-4</b> Use IPv4", "value": False, "category": "extra" },
                { "name": "ipv6", "arg": "-6", "type": "bool", "description": "<b>-6</b> Use IPv6", "value": False, "category": "extra" },
            ]
        },
        "wget": {
            "title": "wget",
            "priority": "required",
            "type": "app",
            "category": "download",
            "version": "1.15",
            "description": "HTTP download utility",
            "config": [
                { "name": "c", "arg": "-c", "type": "bool", "description": "<b>-c</b> Continue partial downloads.", "value": True },
                { "name":"nc", "arg":"-nc", "type": "bool", "description": "<b>-nc</b> No-clobber, keep existing files.", "value": False },
                { "name": "N", "arg": "-N", "type": "bool", "description": "<b>-N</b> Only fetch newer files", "value": False },
                { "name": "O", "arg": "-O", "type": "str",  "description": "<b>-O</b> Output to file", "value": "" },
                { "name": "v", "arg": "-v", "type": "bool", "description": "<b>-v</b> Verbose mode", "value": False, "category": "verbose" },
                { "name": "S", "arg": "-S", "type": "bool", "description": "<b>-S</b> Show response headers", "value": False, "category": "verbose" },
                { "name": "U", "arg": "-U", "type": "str",  "description": "<b>-U</b> Useragent to send", "value": "", "category": "extra" },
            ]
        },
    }

    # current selection (dialog only runs once anyway, so we can keep flags in same object)
    app = "streamripper"
    argmap = {}    # "--xs2" => "xs2"
    namemap = {}   # "xs2" => "--xs2"
    typemap = {}   # "xs2" => "bool"
    defmap = {}    # "opt" => "default"
    
    # parameters from current action.record() call
    k = []     # avoids having to pass them around
    kw = {}    # simplifies gtk callbacks
    row = {}   # only one active instance anyway


    # hooks for user interface/handlers
    def init2(self, parent, *k, **kw):
        # TEMPORARY WORKAROUND: swap action.record()
        action.record = self.action_hook
        # BETTER APPROACH: hook record button
        #parent.on_record_clicked = self.show_window

        # default widget actions
        parent.win_recordoptions.connect("delete-event", self.hide_dialog)
        parent.recordoptions_go.connect("clicked", self.do_record)
        parent.recordoptions_save.connect("clicked", self.save_only)
        parent.recordoptions_eventbox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("#442211"))

        # shortcuts
        self.add_plg = parent.configwin.add_plg           # create _cfg widgets
        self.load_config = parent.configwin.load_config   # populate _cfg widgets
        self.save_config = parent.configwin.save_config   # save from _cfg widgets
        self.cfg_vbox = { 
            "basic": self.parent.recordoptions_cfg,
            "extra": self.parent.recordoptions_cfg_extra,
            "verbose": self.parent.recordoptions_cfg_verbose,
        }

        # add menu entry (for simple triv#1 option)
        #uikit.add_menu([parent.extensions_context], "Set single MP3 record -A flag", self.set_cont)

        
    # prepares a few shortcuts
    def map_app_args(self, app):
        config = self.flag_meta[app]["config"]
        self.argmap = { row["arg"].split(" ")[0]: row["name"] for row in config if row.get("arg") }
        self.namemap = dict(zip(self.argmap.values(), self.argmap.keys()))
        self.typemap = { row["name"]: row["type"] for row in config if row.get("type") }
        self.defmap = { row["name"]: row["value"] for row in config if row.get("value") is not None }
        log.CONF(self.defmap)


    # triv #1 menu option → only saves `-A` flag to row["recordflags"]
    #def set_cont(self, row):
    #    row[conf.recordflags_row] = "-A"
        
    # override GtkWindow.destroy/delete-event
    def hide_dialog(self, *x):
        self.parent.win_recordoptions.hide()
        return True
        
    # hook for action.record
    def action_hook(self, row={}, *k, **kw):
        kw["assoc"] = conf.record
        # default
        if not self.can_handle(row):
            return action.run_fmt_url(row, *k, **kw)
        # use saved settings
        if conf.recordflags_auto and row.get(conf.recordflags_row):
            kw["append"] = row[conf.recordflags_row].strip()
            return action.run_fmt_url(row, *k, **kw)
        # else bring up win_recordoptions
        else:
            self.k = k    # stash away args: audioformat, source, assoc, append
            self.kw = kw
            self.row = row
            self.show_dialog(self.row)

    # only handle audio/* streamripper formats
    def can_handle(self, row):
        # search for configured (flag_meta) apps in conf.record["audio/*"] dict
        rx_apps = "\\b(?i)(" + ("|".join(self.flag_meta.keys())) + ")\\b"
        cmd = action.mime_app(row.get("format", "audio/*"), conf.record)
        match = re.findall(rx_apps, cmd or "")
        log.PROC(cmd)
        # if both mime matched, and cmd in supported apps:
        if cmd and match:
            log.STAT(match)
            self.app = match[0]
            self.map_app_args(self.app)
            return True
        return False

    # store current dialog settings into row[], invoked by [save] button
    def save_only(self, *x):
        self.row[conf.recordflags_row] = self.args_from_configwin()
        self.parent.channel().save()

    # overriden handler, chains to actual recording, invoked by [record] button
    def do_record(self, *x):
        self.kw["append"] = self.args_from_configwin().strip()
        action.run_fmt_url(self.row, *self.k, **self.kw)
        self.hide()

    # option window
    def show_dialog(self, row):
        p = self.parent
        # set labels, connect buttons
        p.recordoptions_title.set_text(row["title"][0:50])
        p.recordoptions_url.set_text(row["url"][0:50])
        # add option widgets
        self.load_config_widgets(row, self.app, p)
        # show window
        p.win_recordoptions.show()


    # populate config widgets, seth defaults/current settings
    def load_config_widgets(self, row, group="streamripper", p=None):
        # clean up previous
        [vbox.remove(w) for vbox in self.cfg_vbox.values() for w in vbox.get_children()]
        # add plugins
        self.add_plg(group, self.flag_meta[group], self.pack_option, self.cfg_widget_pfx)
        # set values
        self.load_config(self.configdict_from_args(row), self.cfg_widget_pfx, widgets=self.widgets)

    # Put config widgets into recordoptions_cfg_*** vbox
    def pack_option(self, id=None, w=None, label=None, color=None, image=None, align=5, opt={}):
        vbox = self.cfg_vbox.get(opt.get("category"), self.cfg_vbox["basic"])
        vbox.pack_start(uikit.wrap(self.widgets, id, w, label, color, image, align, label_markup=1, label_size=250))

        
    # return "--args str" for current config widget states
    def args_from_configwin(self):
        cfg = { name: None for name in self.namemap.keys() }
        self.save_config(cfg, self.cfg_widget_pfx, widgets=self.widgets)
        log.DATA(cfg)
        return self.args_from_configdict(cfg)

    #-- parse existing `record_flags` and conf.record defauls into name-config
    def configdict_from_args(self, row):
        r = copy.copy(self.defmap)
        # saved `record_flags`
        cmdstr = row.get(conf.recordflags_row, "")
        # add default options from configured recoding app
        if conf.record.get("audio/*"):
            add = re.findall('"(.+?)"', conf.record["audio/*"])
            if add:
                cmdstr = add[0] + " " + cmdstr
        # global/default plugin option, if set
        if conf.recordflags_dir:
            r["dir"] = conf.recordflags_dir
        # extract
        for arg,val in re.findall("""(-\w+|--[\w-]+)\s*("[^"]+"|'[^']+'|[^-]+)?""", cmdstr):
            if not arg in self.argmap:
                continue
            name = self.argmap[arg]
            r[name] = val.strip() if len(val) else 1
        return r
        # ToDo: differentiate `-A -a …` and `-A` only

    #-- convert { name=>value, .... } dict into "--arg str"
    def args_from_configdict(self, loaded_config):
        s = ""
        for name, val in loaded_config.items():
            default = str(self.defmap.get(name))
            if val in (False, None, "", 0, "0", default):
                continue
            arg = self.namemap[name]
            s = s + " " + arg
            if isinstance(val, (str, unicode)): # type == "bool" check here(...)
                s = s + " " + val
        return s
