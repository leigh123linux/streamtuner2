# encoding: utf-8
# title: Channel toolbar link
# description: Shows current channel and a link to online service in toolbar.
# version: 1.0
# depends: streamtuner2 >= 2.1.9
# type: feature
# category: ui
#
# Reintroduces the channel/service link in the toolbar,
# just like in streamtuner1.


import re


# Channel Homepage in Toolbar
class ui_cht(object):
    module = __name__

    # Hook toolbar label
    def __init__(self, parent):
        self.label = parent.toolbar_link
        parent.hooks["switch"].append(self.switchy)

    # Update link label
    def switchy(self, meta, *x, **y):
        title = meta.get("title")
        url = meta.get("url")
        domain = re.sub("^.+?//|/.+$", "", url)
        self.label.set_markup("<big><b>{}</b></big>\n<a href='{}'>{}</a>".format(title, url, domain))

