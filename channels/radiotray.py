# api: dbus
# title: RadioTray hook
# description: Allows to bookmark stations to RadioTray
# version: 0.2
# type: feature
# category: bookmarks
# depends: deb:python-dbus, deb:streamtuner2, deb:python-xdg
# config: -
# url: http://radiotray.sourceforge.net/
# priority: extra
# id: streamtuner2-radiotray
# pack: radiotray.py=/usr/share/streamtuner2/channels/
#
# Adds a context menu "Keep in RadioTray.." to bookmark streams
# in RadioTray.  Until a newer version exposes addRadio(), this
# plugin will fall back to just playUrl().
#
# The patch for radiotray/DbusFacade.py would be:
#   +
#   +    @dbus.service.method('net.sourceforge.radiotray')
#   +    def addRadio(self, title, url, group="root"):
#   +        self.dataProvider.addRadio(title, url, group)
#
# Displays existing radiotray stations in ST2 bookmarks category
# as read from ~/.local/share/radiotray/bookmarks.xml. They're not
# refetched during runtime.
#
# This plugin may be packaged up separately.
#

from config import *
from channels import *
from mygtk import mygtk

import dbus
from xdg.BaseDirectory import xdg_data_home
from xml.etree import ElementTree


# not a channel plugin, just a category in bookmarks, and a context menu
class radiotray:

    # plugin info
    module = "radiotray"
    title = "RadioTray"
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

        # create category
        self.bm.add_category("radiotray", plugin=self);
        self.bm.streams["radiotray"] = self.update_streams(cat="radiotray")
        self.bm.reload_if_current(self.module)

        # add context menu
        if parent:
            mygtk.add_menu(parent.extensions, "Keep in RadioTray", self.share)
        

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
                self.radiotray().addRadio(row["title"], row["url"], row.get("genre", d="root"))
            except:
                self.radiotray().playUrl(row["url"])
        pass


