# api: dbus
# title: RadioTray interface
# description: Allows to bookmark stations to RadioTray
# version: 0.1
# type: feature
# category: bookmarks
# depends: deb:python-dbus, deb:streamtuner2, deb:python-xdg
# priority: extra
# id: streamtuner2-radiotray
# pack: radiotray.py=/usr/share/streamtuner2/channels/
#
# Adds a context menu "Share in RadioTray.." to bookmark a station
# in RadioTray.  Currently just starts playing.  RT doesn't expose
# its addRadio() method yet.
#
# Supposed to read RadioTrays bookmarks as well, and make them available
# in bookmarks>radiotray channel.
#
# Can be packaged up separately.
#

from config import conf, __print__, dbg
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
    # configuration settings
    config = [
    ]
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
            "net.sourceforge.radiotry"
        )


    # hook up to main tab
    def __init__(self, parent):

        # keep reference to main window    
        self.parent = parent
        self.bm = parent.channels["bookmarks"]

        # create category
        self.bm.add_category("radiotray");
        self.bm.streams["radiotray"] = self.update_streams(cat="radiotray")
        self.bm.reload_if_current(self.module)

        # add context menu
        if parent:
            mygtk.add_menu(parent.extensions, "Share in RadioTray", self.share)
        

    # load RadioTray bookmarks
    def update_streams(self, cat):
        r = []
        try:
            for group in ElementTree.parse(self.rt_xml).findall("//group"):
                for bookmark in group.findall("bookmark"):
                    r.append({
                        "genre": group.attrib["name"],
                        "title": bookmark.attrib["name"],
                        "url": bookmark.attrib["url"],
                        "playing": "",
                    })
        except:
            r
        return r


    # send to 
    def share(self, *w):
        row = self.parent.row()
        if row:
            # RadioTray doesn't have an addRadio method yet, so just fall back to play the stream URL
            try:
                self.radiotray().addRadio(row["title"], row["url"])
            except:
                self.radiotray().playUrl(row["url"])
        pass


