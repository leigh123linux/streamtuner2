# encoding: UTF-8
# api: streamtuner2
# title: Gtk2 theme installer
# description: Shows themes in the bookmarks pane for installation
# type: feature
# category: ui
# version: 0.4.2
# priority: experimental
#
# Downloads a list of Gtk themes and presents it in the bookmarks
# tab under... »themes«. Double clicking will download and install
# a theme right away.
#
# Note that this is primarily meant for Windows, as it unpacks
# *.dll engines if found. Should work on BSD/Linux still, but would
# require setting up .gtkrc, and writeable module_path for engines.
# It only handles Gtk2 themes currently.
#
# Reuses the `conf.theme` setting from the `gtk_theme` plugin, and
# should work in conjunction to it.
#
# The theme repository is a CSV file of:
#   themepkg.zip, theme.png, Title, Author, http://homepage/
# with the packages residing next to it.
#
# Using a repo.json works better however, and would allow to
# integrate it with the regular plugin manager somewhen.
# The bookmark/themes channel provides the nicer UI however.
#
# A theme.zip should contain a structure like:
#    ---------  ---------- -----   ----
#        62937  2016-12-12 16:39   librezlooks.dll
#            0  2016-12-12 16:40   Rezlooks-dark/
#            0  2016-12-03 20:58   Rezlooks-dark/gtk-2.0/
#         5332  2006-06-30 05:28   Rezlooks-dark/gtk-2.0/gtkrc
#    ---------  ---------- -----   ----
# With the dll in the root, and theme files in a named subdir.
# Zips are extracted into the config dir ../streamtuner2/themes/
# and copies left there even.


import os, shutil
import csv
import zipfile
import re
import json
import ahttp
from config import *
import uikit
from compat2and3 import *
import action
import channels.favicon as fi


# register a key
class theme_installer(object):

    # plugin info
    module = "theme_installer"
    meta = plugin_meta()
    category = "themes"
    theme_dir = conf.dir + "/themes/"
    themes_url = "http://milki.include-once.org/streamtuner2/themes/"
    themes_csv = "themes.json"
    mime = "zip/gtk-theme"
    parent = None
    bm = None

    # register
    def __init__(self, parent):
        if not parent:
            return
        if not uikit.ver == 2:
            return
        if not "theme" in conf:
            conf.theme = "default"
        if not os.path.exists(self.theme_dir):
            os.mkdir(self.theme_dir)
        self.parent = parent
        self.bm = parent.bookmarks

        # register hooks
        action.handler[self.mime] = self.install_handler    # zip/gtk-theme downloader
        self.bm.add_category(self.category)                 # add subcategory
        self.bm.category_plugins[self.category] = self      # reloading theme list
        parent.hooks["init"].append(self.apply_theme)       # load gtk theme on start

    # gtk.rc_parse() called on configwin.save and ST2 startup
    def apply_theme(self, now=True):
        if conf.theme == "default":
            return
        # look if theme exists
        fn = "%s%s/%s" % (self.theme_dir, conf.theme, "gtk-2.0/gtkrc")
        if not os.path.exists(fn):
            return
        log.GTK_THEME_FILE(fn)
        # .GTKRC/Gtk2
        uikit.gtk.rc_parse_string("module_path \"%s:%s\"\n" % (uikit.gtk.rc_get_module_dir(), self.theme_dir))
        uikit.gtk.rc_parse(fn)
        uikit.gtk.rc_reset_styles(uikit.gtk.settings_get_for_screen(uikit.gtk.gdk.screen_get_default()))

    # download list of themes
    def update_streams(self, cat):
        r = []
        data = ahttp.get(self.themes_url + self.themes_csv)
        
        #-- repo.JSON
        if re.match("^\s*\[\s*\{", data):
            r = json.loads(data)
            # can contain a literal rows-list + repo meta data

        #-- themes.CSV
        else:
            for row in re.findall("^(?!#)\s*(.+?),\s*(.+?),\s*(.+?),\s*(.+?),\s*(.+)", data, re.M):
                # prepare row
                d = dict(
                    genre = "gtk2",
                    url = row[0],
                    img = row[1],
                    title = row[2],
                    playing = row[3],
                    homepage = row[4],
                    state = "gtk-zoom-fit",
                    format = self.mime,
                    listformat = "href"
                )
                # add
                r.append(d)

        # filter on properties
        d_platform = "win32" if conf.windows else "linux"
        d_gtk = "gtk2" if uikit.ver == 2 else "gtk3"
        for i,d in enumerate(r):
            if not d.get("depends"):
                continue
            for dep in re.split("\s*,\s*", d["depends"]):
                if dep in ("gtk", "streamtuner2", "theme_installer", "gtk2|gtk3", "win32|linux"):
                    continue
                if not dep in (d_platform, d_gtk):
                    del r[i]

        # convert relative references
        for d in r:
            for field in ("url", "img", '$file'):
                v = str(d.get(field))
                if v  and v.find("://") < 0:
                    d[field] = self.themes_url + v
            d["title"] = "\n%s\n" % d.get("title", "-")

        # predownload favicons
        for d in r:
            d["favicon"] = fi.row_to_fn(d)
            if not os.path.exists(d["favicon"]):
                fi.banner_localcopy(d["img"], d["favicon"], 64)
                log.COPY( d["img"], d["favicon"] )
        
        return r


    # invoked by action. module when encounterin a zip/gtk-theme links
    def install_handler(self, row, audioformat, source, assoc):
        if not "url" in row:
            return

        # download
        log.THEME_INSTALL(row["url"])
        zip = self.theme_dir + os.path.basename(row["url"])
        #if not os.path.exists(zip):
        with open(zip, "wb") as f:
            f.write(ahttp.get(row["url"], binary=True))
        # extract
        z = zipfile.ZipFile(zip)
        z.extractall(self.theme_dir)
        z.close()
        os.remove(zip)
        ls = z.namelist()
        dll = [fn for fn in ls if re.search("\w+\.(dll|so)$", fn)]
        base = [m.group(1) for fn in ls for m in [re.match("^([\w\s\-\.]+)/gtk-2.0/.+", fn)] if m]

        # move *.dll / *.so
        for gtk_dir in uikit.gtk.rc_get_module_dir().split(";" if conf.windows else ":"):
            if os.path.exists(gtk_dir) and os.access(gtk_dir, os.W_OK):
                for fn in dll:
                    if fn.find("/") > 0:  # create lib/engines/.../ if given
                        try: os.makedirs(self.theme_dir + os.path.basename(fn))
                        except: pass      # copy file
                    try:            
                        if shutil.copy(self.theme_dir + fn, gtk_dir):
                            break
                    except Exception as e: #access denied - either 'file in use'
                        if not os.path.exists(gtk_dir + "/" + fn): # or missing file system rights
                            log.THEME_INSTALL("Copy Gtk theme engine error ", e)
                            self.parent.status('<span background="orange">⛔ Set theme unsuccessful. - Check access rights!</span>', timeout=22, markup=1)
                            self.clear_theme(ls, dll)
                            return
            else:
                if conf.windows:
                    log.THEME_INSTALL("Copy Gtk theme engine error, gtk_dir= " + gtk_dir)
                    self.parent.status('<span background="orange">⛔ Set theme unsuccessful. - Check ' + gtk_dir + '</span>', timeout=22, markup=1)
                    self.clear_theme(ls, dll)
                    return

        # enable
        if dll: 
            self.clear_dll(dll)
            
        conf.theme = base[0]
        self.apply_theme(True)
        conf.save()

    # delete theme files if application failed
    def clear_theme(self, ls, dll):
        for fn in ls:
            try:
                shutil.rmtree(self.theme_dir + fn)
            except: pass # probably not found
        if dll:
            self.clear_dll(dll)

    # delete theme engine dll
    def clear_dll(self, dll):
        for fn in dll:
            os.remove(self.theme_dir + fn)
