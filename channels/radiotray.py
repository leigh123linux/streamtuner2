# api: dbus
# title: RadioTray hook
# description: Allows to bookmark stations to RadioTray
# version: 0.3
# type: feature
# category: bookmarks
# depends: deb:python-dbus, deb:streamtuner2, deb:python-xdg
# config:
#   { name: radiotray_map, type: select, value: "group", select: 'root|group|asis|play', description: 'Map genres to default RadioTray groups, or just "root".' }
# url: http://radiotray.sourceforge.net/
# priority: extra
# id: streamtuner2-radiotray
# pack: radiotray.py
# fpm-prefix: /usr/share/streamtuner2/channels/
#
# Adds a context menu "Keep in RadioTray.." for bookmarking.
# Until a newer version exposes addRadio(), this plugin
# will fall back to just playUrl().
#
# The patch for radiotray/DbusFacade.py would be:
#   +
#   +    @dbus.service.method('net.sourceforge.radiotray')
#   +    def addRadio(self, title, url, group="root"):
#   +        self.dataProvider.addRadio(title, url, group)
#
# Displays existing radiotray stations in ST2 bookmarks
# category as read from ~/.local/share/radiotray/bookmarks.xml.
#
# This plugin may be packaged up separately.
#

from config import *
from channels import *
from uikit import uikit
import re
import dbus
from xdg.BaseDirectory import xdg_data_home
from xml.etree import ElementTree


# not a channel plugin, just a category in bookmarks, and a context menu
class radiotray:

    # plugin info
    module = "radiotray"
    meta = plugin_meta()
    # bookmarks cat
    parent = None
    bm = None
    # radiotray config file / bookmarks
    rt_xml = "%s/%s/%s" % (xdg_data_home, "radiotray", "bookmarks.xml")


    # DBUS connector
    def radiotray(self):
        return dbus.Interface(
            dbus.SessionBus().get_object(
                "net.sourceforge.radiotray",
                "/net/sourceforge/radiotray"
            ),
            "net.sourceforge.radiotray"
        )


    # hook up to main tab
    def __init__(self, parent):

        # keep reference to main window    
        self.parent = parent
        self.bm = parent.channels["bookmarks"]
        conf.add_plugin_defaults(self.meta, self.module)

        # create category
        self.bm.add_category("radiotray", plugin=self);
        self.bm.streams["radiotray"] = self.update_streams(cat="radiotray")
        self.bm.reload_if_current(self.module)

        # add context menu
        uikit.add_menu([parent.streammenu, parent.streamactions], "Keep in RadioTray", self.share, insert=4)
        

    # load RadioTray bookmarks
    def update_streams(self, cat):
        r = []
        try:
            for group in ElementTree.parse(self.rt_xml).findall(".//group"):
                for bookmark in group.findall("bookmark"):
                    r.append({
                        "genre": group.attrib["name"],
                        "title": bookmark.attrib["name"],
                        "url": bookmark.attrib["url"],
                        "playing": "",
                    })
        except:
            pass
        return r


    # send to 
    def share(self, *w):
        row = self.parent.row()
        if row:
            # RadioTray doesn't have an addRadio method yet, so just fall back to play the stream URL
            try:
                group = self.map_group(row.get("genre"))
                log.PROC("mapping genre '%s' to RT group '%s'" % (row["genre"], group))
                self.radiotray().addRadio(row["title"], row["url"], group)
            except:
                self.radiotray().playUrl(row["url"])
        pass

    # match genre to RT groups
    def map_group(self, genre):
        if not genre or not len(genre) or conf.radiotray_map == "root":
            return "root"
        if conf.radiotray_map == "asis":
            return genre  # if RadioTray itself can map arbitrary genres to its folders
        if conf.radiotray_map == "play":
            raise NotImplementedError("just call .playUrl()")
        map = {
            "Jazz": "jazz|fusion|swing",
            "Pop / Rock": "top|pop|rock|metal",
            "Latin": "latin|flamenco|tango|salsa|samba",
            "Classical": "classic|baroque|opera|symphony|piano|violin",
            "Oldies": "20s|50s|60s|70s|oldie",
            "Chill": "chill|easy|listening",
            "Techno / Electronic": "techno|electro|dance|house|beat|dubstep|progressive|trance",
            "Country": "country|bluegrass|western",
            "Community": "community|talk|sports|spoken|educational",
        }
        #for str in (genre,title):
        for cat,rx in map.items():
            if re.search(rx, genre, re.I):
                return cat
        return "root"

