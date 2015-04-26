#
# api: streamtuner2
# title: Links to directory services
# description: Static list of various music directory websites.
# type: group
# category: web
# version: 0.2
# priority: standard
# config: -
#
# Simply adds a "links" entry in bookmarks tab, where known services
# are listed with homepage links.
#


from config import *
from channels import *
import copy



# hooks into main.bookmarks
class links (object):

    # plugin info
    module = "links"
    meta = plugin_meta()
    
    # list
    streams = [    ]
    default = [
        ("stream", "rad.io", "http://www.rad.io/"),
        ("stream", "RadioTower", "http://www.radiotower.com/"),
        ("stream", "8tracks", "http://8tracks.com/"),
        ("stream", "TuneIn", "http://tunein.com/"),
        ("stream", "Jango", "http://www.jango.com/"),
        ("stream", "last.fm", "http://www.last.fm/"),
        ("stream", "StreamFinder", "http://www.streamfinder.com/"),
        ("stream", "Rhapsody (US-only)", "http://www.rhapsody.com/"),
        ("stream", "Pirateradio Network", "http://www.pirateradionetwork.com/"),
        ("stream", "radio-locator", "http://www.radio-locator.com/"),
        ("stream", "Radio Station World", "http://radiostationworld.com/"),
        ("stream", "MusicGOAL", "http://www.musicgoal.com/"),
        ("download", "Live Music Archive(.org)", "https://archive.org/details/etree"),
        ("download", "FMA, free music archive", "http://freemusicarchive.org/"),
        ("download", "Audiofarm", "http://audiofarm.org/"),
        ("stream", "SoundCloud", "https://soundcloud.com/"),
        ("download", "ccMixter", "http://dig.ccmixter.org/"),
        ("download", "mySpoonful", "http://myspoonful.com/"),
        ("download", "NoiseTrade", "http://noisetrade.com/"),
        ("stream", "Hype Machine", "http://hypem.com/"),
        ("download", "Amazon Free MP3s", "http://www.amazon.com/b/ref=dm_hp_bb_atw?node=7933257011"),
        ("stream", "Shuffler.fm", "http://shuffler.fm/"),
        ("download", "ccTrax", "http://www.cctrax.com/"),
        ("list", "WP: Streaming music services", "http://en.wikipedia.org/wiki/Comparison_of_on-demand_streaming_music_services"),
        ("list", "WP: Music databases", "http://en.wikipedia.org/wiki/List_of_online_music_databases"),
        ("commercial", "Google Play Music", "https://play.google.com/about/music/"),
        ("commercial", "Deezer", "http://www.deezer.com/features/music.html"),
       #("stream", "SurfMusik.de", "http://www.surfmusic.de/"),
    ]
    
    
    
    # prepare gui
    def __init__(self, parent):

        if parent:

            # prepare target category
            bookmarks = parent.bookmarks
            if not bookmarks.streams.get(self.module):
                bookmarks.streams[self.module] = []
            bookmarks.add_category(self.module)
            
            # fill it up later
            parent.hooks["init"].append(self.populate)


    def populate(self, parent):
    
        # Collect links from channel plugins
        for name,channel in parent.channels.items():
            try:
                self.streams.append({
                    "favourite": 1,
                    "genre": "channel",
                    "title": channel.meta.get("title", channel.module),
                    "homepage": channel.meta.get("url", ""),
                    "type": "text/html",
                })
            except Exception as e:
                log.ERR("links: adding entry failed:", e)

        # Add built-in link list
        for row in self.default:
            (genre, title, homepage) = row
            self.streams.append({
                "genre": genre,
                "title": title,
                "homepage": homepage,
                "type": "text/html",
            })

        # add to bookmarks
        parent.bookmarks.streams[self.module] = self.streams

        # redraw category
        parent.bookmarks.reload_if_current(self.module)
