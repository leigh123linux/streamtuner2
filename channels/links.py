#
# api: streamtuner2
# title: links to directory services
# description: provides a simple list of homepages for directory services
# version: 0.1
# priority: rare
#
#
# Simply adds a "links" entry in bookmarks tab, where known channels
# and some others are listed with homepage links.
#
#


from channels import *
import copy



# hooks into main.bookmarks
class links (object):

    # plugin info
    module = "links"
    title = "Links"
    version = 0.1
    
    
    # configuration settings
    config = [    ]
    
    # list
    streams = [    ]
    default = {
        "radio.de": "http://www.radio.de/",
        "musicgoal": "http://www.musicgoal.com/",
        "streamfinder": "http://www.streamfinder.com/",
        "last.fm": "http://www.last.fm/",
        "rhapsody (US-only)": "http://www.rhapsody.com/",
        "pandora (US-only)": "http://www.pandora.com/",
        "radiotower": "http://www.radiotower.com/",
        "pirateradio": "http://www.pirateradionetwork.com/",
        "R-L": "http://www.radio-locator.com/",
        "radio station world": "http://radiostationworld.com/",
        "surfmusik.de": "http://www.surfmusic.de/",
    }
    
    
    # prepare gui
    def __init__(self, parent):
      if parent:

        # target channel
        bookmarks = parent.bookmarks
        if not bookmarks.streams.get(self.module):
            bookmarks.streams[self.module] = []
        bookmarks.add_category(self.module)


        # collect links from channel plugins
        for name,channel in parent.channels.items():
          try:
            self.streams.append({
                "favourite": 1,
                "title": channel.title,
                "homepage": channel.homepage,
            })
          except: pass
        for title,homepage in self.default.items():
            self.streams.append({
                "title": title,
                "homepage": homepage,
            })

        # add to bookmarks
        bookmarks.streams[self.module] = self.streams
        
        