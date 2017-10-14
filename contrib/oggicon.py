# encoding: UTF-8
# api: streamtuner2
# title: OGG icon
# description: highlights OGG Vorbis and Opus stations with icons
# version: 0.2
# depends: uikit
# type: feature
# category: ui
# priority: extra
#
# Adds a Gtk icon for OGG Vorbis and Opus streams, which get displayed
# leftmost (to the genre) as state icon.
#
# Instantiates the icons right away as pixbufs in an IconFactory, assigns
# each to a short stock_id: `ogg` and `opus`.


import uikit
from config import *
from channels import *


# oggicon
class oggicon (FeaturePlugin):

    # icons
    png = {
        "ogg": """
            iVBORw0KGgoAAAANSUhEUgAAABgAAAAYBAMAAAASWSDLAAAAJFBMVEUAAAAVJCtCRRsdUnc5Vls2
            b5qLhjZTjrBqkpOqmhmWz9fu1CObwCzQAAAAAXRSTlMAQObYZgAAAAFiS0dEAIgFHUgAAAAJcEhZ
            cwAACxMAAAsTAQCanBgAAAAHdElNRQfhAg0VAAsUWVEpAAAA10lEQVQY02NgAAGuAgYEWB6OYHNV
            hSKklleFwqW4yqtC4VLLy11cnM0hbHaXwq5Vq4QhUktWCal0rVoCluKqaOnenbJqlaMISIfGKu+d
            27yWSHQ4MDA67WyavXPmRI9VqxwYOpbM3g0E2VmrVpgzFHp57k7SnLZt1xJHUwb2wGW7V2jvzpy1
            aoUDA4NI57YmoLpVq1YATRMR2r17m5Kix6olIItKBQVFVgkbCgqCnRMaGixobBwAcVxpaKixsSnU
            1ewgTgDMQ6WhcAmQFEICKGWKFDrsEAkAzOpE42DS7YsAAAAASUVORK5CYII=""",
        "opus": """
            iVBORw0KGgoAAAANSUhEUgAAABgAAAAYBAMAAAASWSDLAAAAGFBMVEVhcACTlZKYmpeeoJ2ipKGp
            q6isrquytLF6/PABAAAAAXRSTlMAQObYZgAAAAFiS0dEAIgFHUgAAAAJcEhZcwAACxMAAAsTAQCa
            nBgAAAAHdElNRQfhAg0UOTZDd/q1AAAAYUlEQVQY02NgoAYoBwJ2CJMdxC4AIiCbLQ0EEkCYgSEN
            DhIYWENBgBVMQTgMUMoFCBwYGFhANIwDoYyBwICBGUIZIwADgxICMDAwIbEZGAWhAOw0ICUAdzKj
            ILIHBEn1MQBjViBd1YYkTgAAAABJRU5ErkJggg=="""
    }

    # hook filter, set gtk icons
    def init2(self, parent):
        GenericChannel.postprocess_filters.append(self.row_icon)
        self.add_icons()
 
    # adds gtk.IconFactory and one IconSet/Pixbuf each
    def add_icons(self):
        fact = uikit.gtk.IconFactory()
        for stock_id, b64_png in self.png.items():
            img = uikit.gtk.IconSet(uikit.uikit.pixbuf(b64_png))
            fact.add(stock_id, img)
        fact.add_default()

    # postprocess_filter: add `state` icon name depending on audio format
    def row_icon(self, row, channel):
        fmt = str(row.get("format", channel.audioformat))[6:]
        if fmt in ("ogg", "opus"):
            row["state"] = fmt
        return True

