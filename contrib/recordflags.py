# encoding: utf-8
# api: streamtuner2
# title: Recording options
# description: Allows to set streamripper/fIcy options before recording
# version: 0.9
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
                # basic
                { "name": "Aa",	"arg": "-A -a",	"type": "str",	"description": "<b>-a</b> Single MP3 output filename. (Instead of splitting by song.)", "value": "" },
                { "name": "dir", "arg": "-d",	"type": "str",	"description": "<b>-d</b> Destination directory", "value": "" },
                { "name": "s",	"arg": "-s",	"type": "bool",	"description": "<b>-s</b> No subdirectories for each stream", "value": False },
                { "name": "D",	"arg": "-D",	"type": "str",	"description": "<b>-D</b> Filename pattern", "value": "" },
                { "name": "o",	"arg": "-o",	"type": "select",	"description": "<b>-o</b> Incomplete track overwriting", "select": "|always|never|larger|version", "value": "" },
                { "name": "l",	"arg": "-l",	"type": "int",	"description": "<b>-l</b> Seconds to record", "value": 0, "max": 7*24*3600 },
                { "name": "M",	"arg": "-M",	"type": "int",	"description": "<b>-M</b> Max megabytes to record", "value": 512 },
                { "name": "xs2", "arg": "--xs2", "type": "bool", "description": "<b>--xs2</b> New pause detection algorithm", "value": False },
                { "name": "xsnone", "arg": "--xs-none", "type": "bool", "description": "<b>--xs-none</b> No silence splitting", "value": False },
                # meta
                { "name": "A",	"arg": "-A",	"type": "bool",	"description": "<b>-A</b> Don't split individual tracks/MP3s", "value": False, "category": "meta" },
                { "name": "i",	"arg": "-i",	"type": "bool", "description": "<b>-i</b> Don't add any ID3 tags", "value": False, "category": "meta" },
                { "name": "noid3v2", "arg": "--without-id3v2", "type": "bool", "description": "<b>--without-id3v2</b> Omit ID3v2 tags", "value": False, "category": "meta" },
                { "name": "id3v1", "arg": "--with-id3v1", "type": "bool", "description": "<b>--with-id3v1</b> Add ID3v1 tags", "value": False, "category": "meta" },
                { "name": "cs_fs", "arg": "--codeset-filesys", "type": "str", "description": "Charset filesystem", "value": "", "category": "meta" },
                { "name": "cs_id3", "arg": "--codeset-id3", "type": "str", "description": "Charset ID3 tags", "value": "", "category": "meta" },
                { "name": "t",	"arg": "-t",	"type": "bool",	"description": "<b>-t</b> Never overwrite incomplete tracks", "value": False, "category": "meta" },
                { "name": "T",	"arg": "-T",	"type": "bool",	"description": "<b>-T</b> Truncate duplicated incompletes", "value": False, "category": "meta" },
                # net
                { "name": "p",	"arg": "-p",	"type": "str", "description": "<b>-p</b> Url for HTTP proxy to use", "value": "", "category": "net" },
                { "name": "r",	"arg": "-r",	"type": "str", "description": "<b>-r</b> Relay server 'localhost:8000'", "value": "", "category": "net" },
                { "name": "u",	"arg": "-u",	"type": "str", "description": "<b>-u</b> User-agent (browser id)", "value": "", "category": "net" },
                { "name": "m",	"arg": "-m",	"type": "int", "description": "<b>-m</b> Timeout for stalled connection", "value": 15, "category": "net" },
                { "name": "debug", "arg": "--debug", "type": "bool", "description": "<b>--debug</b> Extra verbosity", "value": False, "category": "net"},
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
                # basic
                { "name": "max", "arg": "-M", "type": "int", "description": "<b>-M</b> Maximum cumulative playing time", "value": 0 },
                { "name": "loop", "arg": "-L", "type": "int", "description": "<b>-L</b> Maximum playlist loops", "value": 0 },
                { "name": "retry", "arg": "-R", "type": "int", "description": "<b>-R</b> Maximum per-stream retries", "value": 0 },
                { "name": "redir", "arg": "-l", "type": "int", "description": "<b>-l</b> Redirect follow limit", "value": 0 },
                { "name": "fail", "arg": "-T", "type": "int", "description": "<b>-T</b> Wait time after failure", "value": 0 },
                # meta
                { "name": "ficy", "arg": "-P", "type": "str", "description": "<b>-P</b> Path to fIcy", "value": "", "category": "meta" },
                # net
                { "name": "daemon", "arg": "-i", "type": "int", "description": "<b>-i</b> Max network idle seconds", "value": 0, "category": "net" },
                { "name": "authfn", "arg": "-a", "type": "str", "description": "<b>-a</b> HTTP auth file (user:pass)", "value": "", "category": "net" },
                { "name": "verbose", "arg": "-v", "type": "bool", "description": "<b>-v</b> Verbose mode", "value": False, "category": "net" },
                { "name": "daemon", "arg": "-d", "type": "str", "description": "<b>-d</b> Daemon mode: log file", "value": "", "category": "net" },
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
                # basic
                { "name": "freeformats", "arg": "--prefer-free-formats", "type": "bool", "description": "Prefer free audio formats", "value": False },
                { "name": "format", "arg": "-f", "type": "select", "select": "=any|b=best|249=webm audio only DASH|250=webm audio only DASH|140=m4a audio only DASH|171=webm audio only DASH|251=webm audio only DASH|278=webm 256x144 DASH|160=mp4 256x144 DASH|242=webm 426x240 DASH|133=mp4 426x240 DASH|243=webm 640x360 DASH|134=mp4 640x360 DASH|244=webm 854x480 DASH|135=mp4 854x480 DASH|247=webm 1280x720 DASH|136=mp4 1280x720 DASH|248=webm 1920x1080 DASH|137=mp4 1920x1080 DASH|17=3gp 176x144 small|36=3gp 320x180 small|43=webm 640x360 medium|18=mp4 640x360 medium|22=mp4 1280x720 hd720", "description": "<b>-f</b> Format", "value": "b" },
                { "name": "c", "arg": "-c", "type": "bool", "description": "<b>-c</b> Continue partial downloads", "value": True },
                { "name": "o", "arg": "-o", "type": "str", "description": "<b>-o</b> Output TEMPLATE", "value": "" },
                { "name": "ascii", "arg": "--restrict-filenames", "type": "bool", "description": "<b>--restrict-filenames</b> to ASCII", "value": False },
                { "name": "id", "arg": "--id", "type": "bool", "description": "Use only <b>--id</b> in filename", "value": False },
                { "name": "xa", "arg": "-x", "type": "bool", "description": "<b>-x</b> Extract audio only", "value": False },
                { "name": "recode", "arg": "--recode-format", "type": "select", "select": "|mp4|flv|ogg|webm|mkv|avi", "description": "<b>--recode-format</b>", "value": "" },
                # meta
                { "name": "w_desc", "arg": "--write-description", "type": "bool", "description": "<b>--write-description</b> file", "value": False, "category": "meta" },
                { "name": "w_json", "arg": "--write-info-json", "type": "bool", "description": "<b>--write-info-json</b> file", "value": False, "category": "meta" },
                { "name": "w_anno", "arg": "--write-annotations", "type": "bool", "description": "<b>--write-annotations</b> xml", "value": False, "category": "meta" },
                { "name": "e_subs", "arg": "--embed-subs", "type": "bool", "description": "<b>--embed-subs</b> in video files", "value": False, "category": "meta" },
                { "name": "e_thumb", "arg": "--embed-thumbnail", "type": "bool", "description": "<b>--embed-thumbnail</b> as cover", "value": False, "category": "meta" },
                { "name": "add_meta", "arg": "--add-metadata", "type": "bool", "description": "<b>--add-metadata</b> in output file", "value": False, "category": "meta" },
                { "name": "xattrs", "arg": "--xattrs", "type": "bool", "description": "<b>--xattrs</b> for meta data", "value": False, "category": "meta" },
                ##{ "name": "", "arg": "", "type": "bool", "description": "<b></b>", "value": False, "category": "meta" },
                { "name": "verbose", "arg": "-v", "type": "bool", "description": "<b>-v</b> Verbose mode", "value": False, "category": "meta" },
                { "name": "igncfg", "arg": "--ignore-config", "type": "bool", "description": "<b>--ignore-config</b>", "value": False, "category": "meta" },
                { "name": "downads", "arg": "--download-ads", "type": "bool", "description": "<b>--download-ads</b>", "value": False, "category": "meta" },
                # net
                { "name": "ua", "arg": "--user-agent", "type": "str", "description": "<b>--user-agent</b>", "value": "", "category": "net" },
                { "name": "netrc", "arg": "-n", "type": "bool", "description": "<b>-n</b> Use .netrc for auth/login", "value": False, "category": "net" },
                { "name": "proxy", "arg": "--proxy", "type": "str", "description": "<b>-p</b> Proxy", "value": "", "category": "net" },
                { "name": "geoproxy", "arg": "--geo-verification-proxy", "type": "str", "description": "Geo-verification Proxy", "value": "", "category": "net" },
                { "name": "ignore", "arg": "-i", "type": "bool", "description": "<b>-i</b> Ignore errors", "value": False },
                { "name": "bin", "arg": "--external-downloader", "type": "str", "description": "<b>--external-downloader</b> tool", "value": "", "category": "net" },
                { "name": "ipv4", "arg": "-4", "type": "bool", "description": "<b>-4</b> Use IPv4", "value": False, "category": "net" },
                { "name": "ipv6", "arg": "-6", "type": "bool", "description": "<b>-6</b> Use IPv6", "value": False, "category": "net" },
                { "name": "update", "arg": "-U", "type": "bool", "description": "<b>-U</b> Update", "value": False, "category": "net" },
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
                # basic
                { "name": "c", "arg": "-c", "type": "bool", "description": "<b>-c</b> Continue partial downloads.", "value": True },
                { "name":"nc", "arg":"-nc", "type": "bool", "description": "<b>-nc</b> No-clobber, keep existing files.", "value": False },
                { "name": "N", "arg": "-N", "type": "bool", "description": "<b>-N</b> Only fetch newer files", "value": False },
                { "name": "O", "arg": "-O", "type": "str",  "description": "<b>-O</b> Output to file", "value": "" },
                { "name": "dir", "arg": "-P", "type": "str",  "description": "<b>-P</b> Directory prefix", "value": "" },
                # meta
                { "name": "v", "arg": "-v", "type": "bool", "description": "<b>-v</b> Verbose mode", "value": False, "category": "meta" },
                { "name": "d", "arg": "-d", "type": "bool", "description": "<b>-d</b> Debug mode", "value": False, "category": "meta" },
                { "name": "enc", "arg": "--local-encoding", "type": "select", "select": "UTF-8|ISO-8859-1|ISO-8859-15", "description": "<b>--local-encoding</b>", "value": False, "category": "meta" },
                { "name": "e", "arg": "-e", "type": "str",  "description": "<b>-e</b> wgetrc-command", "value": "", "category": "meta" },
                # net
                { "name": "noch", "arg": "--no-cache", "type": "bool", "description": "<b>-S</b> No cached files", "value": False, "category": "net" },
                { "name": "limit", "arg": "--limit-rate", "type": "int", "description": "<b>--limit-rate</b> Max download speed", "value": 0, "category": "net" },
                { "name": "S", "arg": "-S", "type": "bool", "description": "<b>-S</b> Show response headers", "value": False, "category": "net" },
                { "name": "U", "arg": "-U", "type": "str",  "description": "<b>-U</b> Useragent to send", "value": "", "category": "net" },
                { "name": "ref", "arg": "--referer", "type": "str",  "description": "<b>--referer</b> to send", "value": "", "category": "net" },
                { "name": "4", "arg": "-4", "type": "bool", "description": "<b>-4</b> Use IPv4 only", "value": "", "category": "net" },
            ]
        },
    }

    # current selection (dialog only runs once anyway, so we can keep flags in same object)
    app = "streamripper"
    argmap = {}    # "--xs2" => "xs2"
    namemap = {}   # "xs2" => "--xs2"
    typemap = {}   # "xs2" => "bool"
    defmap = {}    # "opt" => "default"
    catalias = {"verbose": "net", "extra": "meta", None: "basic"}  # alias option category:
    
    # parameters from current action.record() call
    k = []     # avoids having to pass them around
    kw = {}    # simplifies gtk callbacks
    row = {}   # only one active instance anyway


    # hooks for user interface/handlers
    def init2(self, parent, *k, **kw):

        # default widget actions
        parent.win_recordoptions.connect("delete-event", self.hide_dialog)
        parent.recordoptions_go.connect("clicked", self.do_record)
        parent.recordoptions_save.connect("clicked", self.save_only)
        parent.recordoptions_eventbox.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(0x44, 0x22, 0x11))

        # shortcuts
        self.add_plg = parent.configwin.add_plg           # create _cfg widgets
        self.load_config = parent.configwin.load_config   # populate _cfg widgets
        self.save_config = parent.configwin.save_config   # save from _cfg widgets
        self.cfg_vbox = { 
            "basic": self.parent.recordoptions_cfg,
            "meta": self.parent.recordoptions_cfg_extra,
            "net": self.parent.recordoptions_cfg_verbose,
        }

        # swap out action.record()
        action.record = self.action_hook
           # The better option would be overriding main.on_record_clicked.
           # Though that would require to also adapt GenericChannel.record.
           # And would make injecting the append= arguments a bit harder.
        
    # prepares a few shortcuts
    def map_app_args(self, app):
        config = self.flag_meta[app]["config"]
        self.argmap = { row["arg"].split(" ")[0]: row["name"] for row in config if row.get("arg") }
        self.namemap = dict(zip(self.argmap.values(), self.argmap.keys()))
        self.typemap = { row["name"]: row["type"] for row in config if row.get("type") }
        self.defmap = { row["name"]: row["value"] for row in config if row.get("value") is not None }
        #log.CONF(self.defmap)


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

    # check row for matching audio/* MIME,
    # and if tool options are configured for it
    def can_handle(self, row):
        # search for configured (flag_meta) apps in conf.record["audio/*"] dict
        rx_apps = "\\b(?i)(" + ("|".join(self.flag_meta.keys())) + ")\\b"
        cmd = action.mime_app(row.get("format", "audio/*"), conf.record)
        match = re.findall(rx_apps, cmd or "")
        #log.PROC(cmd)
        # if both mime matched, and cmd in supported apps:
        if cmd and match:
            #log.STAT(match)
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
        self.hide_dialog()
        action.run_fmt_url(self.row, *self.k, **self.kw)


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
        category = opt.get("category")
        vbox = self.cfg_vbox.get(self.catalias.get(category) or category) or self.cfg_vbox["basic"]
        vbox.pack_start(uikit.wrap(self.widgets, id, w, label, color, image, align, label_markup=1, label_size=250), expand=False, fill=False)

        
    # return "--args str" for current config widget states
    def args_from_configwin(self):
        cfg = { name: None for name in self.namemap.keys() }
        self.save_config(cfg, self.cfg_widget_pfx, widgets=self.widgets)
        #log.DATA(cfg)
        return self.args_from_configdict(cfg)

    #-- extract saved row[record_flags] and conf.record[] defaults into name-config{}
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
