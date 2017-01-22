# encoding: utf-8
# api: streamtuner2
# title: Recording options
# description: Allows to set streamripper/fIcy options before recording
# version: 0.7
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
# less pretty than a custom dialog, but allows to show options for different
# download/recording tools.
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
            "config": [
                { "name": "A",	"arg": "-A",	"type": "bool",	"description": "➖𝘼 Don't split individual tracks/MP3s", "value": False },
                { "name": "a",	"arg": "-a",	"type": "str",	"description": "➖𝙖 Single MP3 output file", "value": "" },
                { "name": "dir", "arg": "-d",	"type": "str",	"description": "➖𝙙 Destination directory", "value": "" },
                { "name": "D",	"arg": "-D",	"type": "str",	"description": "➖𝘿 Filename pattern", "value": "" },
                { "name": "s",	"arg": "-s",	"type": "bool",	"description": "➖𝙨 No subdirectories for each stream", "value": False },
                { "name": "t",	"arg": "-t",	"type": "bool",	"description": "➖𝙩 Never overwrite incomplete tracks", "value": False },
                { "name": "T",	"arg": "-T",	"type": "bool",	"description": "➖𝙏 Truncate duplicated incompletes", "value": False },
                { "name": "o",	"arg": "-o",	"type": "select",	"description": "➖𝙤 Incomplete track overwriting", "select": "|always|never|larger|version", "value": "" },
                { "name": "l",	"arg": "-l",	"type": "int",	"description": "➖𝙡 Seconds to record", "value": 3600 },
                { "name": "M",	"arg": "-M",	"type": "int",	"description": "➖𝙈 Max megabytes to record", "value": 16 },
                { "name": "xs2", "arg": "--xs2", "type": "bool", "description": "➖➖𝙭𝙨𝟮 New pause detection algorithm", "value": False },
                { "name": "xsnone", "arg": "--xs-none", "type": "bool", "description": "➖➖𝙭𝙨➖𝙣𝙤𝙣𝙚 No silence splitting", "value": False },
                { "name": "i",	"arg": "-i",	"type": "bool", "description": "➖𝙞 Don't add any ID3 tags", "value": False },
                { "name": "id3v1", "arg": "--with-id3v1", "type": "bool", "description": "➖➖𝙬𝙞𝙩𝙝➖𝙞𝙙𝟯𝙫𝟭 Add ID3v1 tags", "value": False },
                { "name": "noid3v2", "arg": "--without-id3v2", "type": "bool", "description": "➖➖𝙬𝙞𝙩𝙝𝙤𝙪𝙩➖𝙞𝙙𝟯𝙫𝟮 Omit ID3v2 tags", "value": False },
                { "name": "cs_fs", "arg": "--codeset-filesys", "type": "str", "description": "Charset filesystem", "value": "" },
                { "name": "cs_id3", "arg": "--codeset-id3", "type": "str", "description": "Charset ID3 tags", "value": "" },
                { "name": "u",	"arg": "-u",	"type": "str", "description": "➖𝙪 User-agent (browser id)", "value": "" },
                { "name": "p",	"arg": "-p",	"type": "str", "description": "➖𝙥 Url for HTTP proxy to use", "value": "" },
                { "name": "r",	"arg": "-r",	"type": "str", "description": "➖𝙧 Relay server 'localhost:8000'", "value": "" },
                { "name": "m",	"arg": "-m",	"type": "int", "description": "➖𝙢 Timeout for stalled connection", "value": 15 },
                { "name": "debug", "arg": "--debug", "type": "bool", "description": "➖➖𝙙𝙚𝙗𝙪𝙜 Extra verbosity", "value": False },
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
                { "name": "max", "arg": "-M", "type": "int", "description": "➖𝙈 Maximum cumulative playing time", "value": 0 },
                { "name": "loop", "arg": "-L", "type": "int", "description": "➖𝙇 Maximum playlist loops", "value": 0 },
                { "name": "retry", "arg": "-R", "type": "int", "description": "➖𝙍 Maximum per-stream retries", "value": 0 },
                { "name": "redir", "arg": "-l", "type": "int", "description": "➖𝙡 Redirect follow limit", "value": 0 },
                { "name": "fail", "arg": "-T", "type": "int", "description": "➖𝙏 Wait time after failure", "value": 0 },
                { "name": "daemon", "arg": "-i", "type": "int", "description": "➖𝙞 Max network idle seconds", "value": 0 },
                { "name": "authfn", "arg": "-a", "type": "str", "description": "➖𝙛 HTTP auth file (user:pass)", "value": "" },
                { "name": "verbose", "arg": "-v", "type": "bool", "description": "➖𝙫 Verbose mode", "value": False },
                { "name": "daemon", "arg": "-d", "type": "str", "description": "➖𝙙 Daemon mode: log file", "value": "" },
                { "name": "ficy", "arg": "-P", "type": "str", "description": "➖𝙋 Path to fIcy", "value": "" },
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
                { "name": "format", "arg": "-f", "type": "select", "select": "=any|b=best|249=webm audio only DASH|250=webm audio only DASH|140=m4a audio only DASH|171=webm audio only DASH|251=webm audio only DASH|278=webm 256x144 DASH|160=mp4 256x144 DASH|242=webm 426x240 DASH|133=mp4 426x240 DASH|243=webm 640x360 DASH|134=mp4 640x360 DASH|244=webm 854x480 DASH|135=mp4 854x480 DASH|247=webm 1280x720 DASH|136=mp4 1280x720 DASH|248=webm 1920x1080 DASH|137=mp4 1920x1080 DASH|17=3gp 176x144 small|36=3gp 320x180 small|43=webm 640x360 medium|18=mp4 640x360 medium|22=mp4 1280x720 hd720", "description": "➖𝙛 Format", "value": "b" },
                { "name": "c", "arg": "-c", "type": "bool", "description": "➖𝙘 Continue partial downloads ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ... ", "value": True },
                { "name": "netrc", "arg": "-n", "type": "bool", "description": "➖𝙣 Use .netrc for auth/login", "value": False },
                { "name": "ignore", "arg": "-i", "type": "bool", "description": "➖𝙞 Ignore errors", "value": False },
                { "name": "proxy", "arg": "--proxy", "type": "str", "description": "➖𝙥 Proxy", "value": "" },
                { "name": "verbose", "arg": "-v", "type": "bool", "description": "➖𝙫 Verbose mode", "value": False },
                { "name": "ipv4", "arg": "-4", "type": "bool", "description": "➖𝟰 Use IPv4", "value": False },
                { "name": "ipv6", "arg": "-6", "type": "bool", "description": "➖𝟲 Use IPv6", "value": False },
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
                { "name": "c", "arg": "-c", "type": "bool", "description": "➖𝙘 Continue partial downloads.", "value": True },
                { "name":"nc", "arg":"-nc", "type": "bool", "description": "➖𝙣𝙘 No-clobber, keep existing files.", "value": False },
                { "name": "N", "arg": "-N", "type": "bool", "description": "➖𝙉 Only fetch newer files", "value": False },
                { "name": "O", "arg": "-O", "type": "str",  "description": "➖𝙊 Output to file", "value": "" },
                { "name": "v", "arg": "-v", "type": "bool", "description": "➖𝙫 Verbose mode", "value": False },
                { "name": "S", "arg": "-S", "type": "bool", "description": "➖𝙎 Show response headers", "value": False },
                { "name": "U", "arg": "-U", "type": "str",  "description": "➖𝙐 Useragent to send", "value": "" },
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
        action.record = self.action_record
        # BETTER APPROACH: hook record button
        #parent.on_record_clicked = self.show_window

        # add menu entry (for simple triv#1 option)
        uikit.add_menu([parent.streammenu], "Set single MP3 record -A flag", self.set_cont)

        # default widget actions
        parent.win_recordoptions.connect("delete-event", self.hide)
        parent.recordoptions_go.connect("clicked", self.do_record)
        parent.recordoptions_save.connect("clicked", self.save_only)
        parent.recordoptions_eventbox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("#442211"))

        # shortcuts
        self.add_plg = parent.configwin.add_plg           # create _cfg widgets
        self.load_config = parent.configwin.load_config   # populate _cfg widgets
        self.save_config = parent.configwin.save_config   # save from _cfg widgets
        self.recordoptions_cfg = parent.recordoptions_cfg # our vbox widget

    # prepares a few shortcuts
    def map_app_args(self, app):
        config = self.flag_meta[app]["config"]
        self.argmap = { row["arg"]: row["name"] for row in config if row.get("arg") }
        self.namemap = dict(zip(self.argmap.values(), self.argmap.keys()))
        self.typemap = { row["name"]: row["type"] for row in config if row.get("type") }
        self.defmap = { row["name"]: row["value"] for row in config if row.get("value") is not None }
        log.CONF(self.defmap)


    # triv #1 menu option → only saves `-A` flag to row["recordflags"]
    def set_cont(self, row):
        row[conf.recordflags_row] = "-A"
        
    # override GtkWindow.destroy/delete-event
    def hide(self, *x):
        self.parent.win_recordoptions.hide()
        return True
        
    # hook for action.record
    def action_record(self, row={}, *k, **kw):
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

    # Put config widgets into recordoptions_cfg vbox
    def add_flag(self, id=None, w=None, label=None, color=None, image=None, align=5):
        self.parent.recordoptions_cfg.pack_start(uikit.wrap(self.widgets, id, w, label, color, image, align, label_markup=1, label_size=250))


    # populate config widgets, seth defaults/current settings
    def load_config_widgets(self, row, group="streamripper", p=None):
        # clean up previous
        [self.recordoptions_cfg.remove(w) for w in self.recordoptions_cfg.get_children()]
        # add plugins
        self.add_plg(group, self.flag_meta[group], self.add_flag, self.cfg_widget_pfx)
        # set values
        self.load_config(self.configdict_from_args(row), self.cfg_widget_pfx, widgets=self.widgets)
        
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
