# encoding: utf-8
# title: Channel toolbar link
# description: Shows current channel and a link to online service in toolbar.
# version: 1.1
# depends: streamtuner2 >= 2.1.9
# type: feature
# category: ui
#
# Reintroduces the channel/service link in the toolbar,
# just like in streamtuner1.
#
# Note this requires '[✔] Add current channel name to window title'
# in the general Options.


import re


# Channel Homepage in Toolbar
class ui_cht(object):
    module = 'ui_cht'

    # Hook toolbar label
    def __init__(self, parent):
        self.label = parent.toolbar_link
        parent.hooks["switch"].append(self.switchy)

    # Update link label
    def switchy(self, meta, *x, **y):
        title = meta.get("title", meta.get("id", ("")))
        url = meta.get("url", "")
        domain = re.sub("^.+?//|/.+$", "", url)
        self.label.set_markup("<big><b>{}</b></big>\n<a href='{}'>{}</a>".format(title, url, domain))

