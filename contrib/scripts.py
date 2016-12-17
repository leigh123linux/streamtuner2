# encoding: UTF-8
# api: streamtuner2
# title: Script stations
# description: User scripts for individual stations
# type: feature
# category: bookmark
# version: 0.1
# priority: theoretical
#
# This plugin provides for a simpler alternative to channel plugins.
# It reads the ~./config/streamtuner2/script/ directory for script
# files, and shows them in the bookmarks channel. Each script may
# scan/uncover a station url at runtime.
# Which obviously isn't meant for easily parseable stations, but for
# the more difficult cases.
#
# There's support for python scripts obviously, but any executable
# file (scripting language) can be run and queried for urls.
#
# Each is supposed to contain a meta comment block (much like this
# plugin), except it's using more stream-oriented descriptors:
#
#   #!/bin/sh
#   # title: Station title
#   # description: Fetching a live stream
#   # genre: jazz
#   # homepage: http://example.org/
#   #
#   # Now normally, it would not just print something static.
#   
#   echo "http://example.org/.mp3"
#
# Obviously the purpose is more complicated extractions. Which is
# why a .py script had acces to all ST2s parsing tools already.
# 
# This is implemented using the action.handler hooks for urn:
# modules. But ensures the resolver script is run each time - by
# not caching the final stream url.
# Conversly this plugin prevents editing of script station entries.
#


import os, shutil, copy, subprocess, sys, StringIO
import csv, zipfile
import re, json, pq
import ahttp
import config
from config import *
import uikit
from compat2and3 import *
import action
from channels import *


# dynamic station extractors from ~/.config/streamtuner2/scripts/
class scripts (object):

    # plugin info
    module = "scripts"
    meta = plugin_meta()
    parent = None
    dir = conf.dir + "/scripts"

    # register hooks
    def __init__(self, parent):
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)
        self.parent = parent
        self.bm = parent.bookmarks
        action.handler["urn:script"] = self.urn_resolve
        self.bm.add_category("scripts")
        self.bm.category_plugins["scripts"] = self

    # find script files and compile station dicts
    def update_streams(self, cat):
        r = []
        for fn in os.listdir(self.dir):
            meta = config.plugin_meta(fn=self.dir+"/"+fn)
            r.append(dict(
                genre = meta.get("genre", meta.get("type", "script")),
                title = meta.get("title", fn),
                playing = meta.get("description", meta.get("playing", "")),
                homepage = meta.get("homepage", ""),
                listeners = to_int(meta.get("listeners", "1")),
                bitrate = to_int(meta.get("bitrate", "64")),
                format = meta.get("format", "audio/mp3"),
                listformat = "href",
                file = fn,
                url = "urn:script:" + fn
            ))
        return r

    # run'em
    def urn_resolve(self, row, *x):
        if not row.get("file"):
            return

        # prepare
        fn = "%s/%s" % (self.dir, row["file"])
        row = copy.copy(row)
        row["url"] = ""
        output = None

        # executable
        if os.path.isfile(fn) and os.access(fn, os.X_OK):
            f = subprocess.Popen([fn], stdout=subprocess.PIPE)
            output, err = f.communicate()
        # plain python script
        elif re.match("^[\w+-]\.py$"):
            real_stdout, sys.stdout = sys.stdout, StringIO.StringIO()
            execfile(fn)
            output, sys.stdout = sys.stdout.getvalue(), real_stdout
        # none
        else:
            return

        # extract urls
        if output:
            urls = re.findall("(\w+://\S+)", output)
            if urls:
                row["url"] = urls[0] # action module does not currently support multi-urls
        return row
        # Unlike other .resolve_urn() handlers this one returns a copy,
        # does not modify the passed dict. And this is only handled in
        # action.run_fmt_url(), but not by GenericChannel.play(). Why
        # OTOH this incudes a *double script invocation*.


