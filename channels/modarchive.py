
# api: streamtuner2
# title: MODarchive
# description: Collection of module / tracker audio files (MOD, S3M, XM, etc.)
# type: channel
# version: 0.3
# url: http://www.modarchive.org/
# priority: extra
# config: -
# category: collection
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAy1JREFUOI01k0trXGUAQM/33W/unblz55VJk0wekzSdaTtJ2oh0YRBEUCtUWoug4MKl4EoEQf+FoAvxDxhwo4uIoiBSH8GABElL0zQPnbyaRzMzSSadua/vc1FdnOXZHDii
#   dvsjg5BISzJWsJgaLYKwWLi/ye6pAAyFbJpnL5cRAta3D9nYOUIKAFChBuKAmUqWl65dolar0d9X5NXNXd7/5BuCKGbi/AApJ0EYxUxdGEJZFiv1PRKWhcrLJ8xMlrj1yvNMTF5BSEng+7R9gx+G9BUL9OQy+EGAlJIgihkf6qX+6IggjFCvz1R4+603yOYLRIFPfWuX
#   2W/voGUCN5UiiU8UdBDSJo5jHDvB0XGbMIqRUqL+WD/m6mod295jZWOTi6P9JIIWXu8QKUcxPWwzPuCxtNUmn3Fpnpxxd20HrQ1Sghh/7UNjy5gghvI5j/duXsNzHUQyzxezc3zwzg2Gh8t8Nvs9ey2f5Y0d/DBCWRZCgFSWhZ1MU8jn6fgRzdYxynG5dGGMmy88Q6k0
#   SMZzaZ52WFrdxk3a5DwXKQRxbFBXKkP09WRQlsRozc5Bk3J5hHTK4cb1F1HKJmkrJqujWMqmmM8QRTFBGLG+fYgaLRWJtUbrmISTZL/RwnOTfPXdr0xXB8nlciSUxI1aVIqSZvcMIxw816E2XkKFUYQRAokgDCO8dArfD/npz4fUd/c564acz2qmJqqkvDySmLnflwli
#   SRxrpDGgpAQhSNoWh6chc3cWKWRcrFSWMPCpjJX4+d4+n389D1JxtTqC0ZqTsw7ywT+PCMIIP4h4WN9j4f4Wvy0fkM+l6XZ9elKSSvUiipjmwQ7NZoNSfy+NVpvVzQNUfa/B49YZWms6fog2mr7eAo5t0zo5pVz06Osf4N03X+b6czVGR4aZv7vB/NI6aTeJVFLypBvQ
#   8UMSCQsQZFwHEAijGRk8h207fPrlj2wdthkq9dNotQkjjZISpY1BSoExoLXBmKcoSxBr8ENYvLfKDwsPWPt7k8nxAX5ZXMFOWERaIy7f/tj8L0n5tGzWSzJdHcZNOihpOGic8tfaI4TRZNM2j4+7yP9+/hd7YWLXivTEWgAAAABJRU5ErkJggg==
# extraction-method: regex
#
#
# A genre browser for tracker music files from the MOD Archive.
#
# MOD files dodn't work with all audio players. And with the default
# download method, it'll receive a .zip archive with embeded .mod file.
#
# Configuring VLC for `audio/mod+zip` or just a generic `*/*` works
# most reliably. See the help on how to define wget/curl to download
# them as well.


import re
import ahttp
from config import conf
from channels import *
from config import *


# The MOD Archive
#
# Modarchive actually provides an API
# http://modarchive.org/index.php?xml-api
# (If only it wasn't XML based..)
#
class modarchive (ChannelPlugin):

    # control attributes
    has_search = False
    base = "http://modarchive.org/"
    audioformat = "audio/mod+zip"
    listformat = "href"
    titles = dict(genre="Genre", title="Song", playing="File", listeners="Rating", bitrate=0)

    # keeps category titles->urls    
    catmap = {"Chiptune": "54", "Electronic - Ambient": "2", "Electronic - Other": "100", "Rock (general)": "13", "Trance - Hard": "64", "Swing": "75", "Rock - Soft": "15", "R &amp; B": "26", "Big Band": "74", "Ska": "24", "Electronic - Rave": "65", "Electronic - Progressive": "11", "Piano": "59", "Comedy": "45", "Christmas": "72", "Chillout": "106", "Reggae": "27", "Electronic - Industrial": "34", "Grunge": "103", "Medieval": "28", "Demo Style": "55", "Orchestral": "50", "Soundtrack": "43", "Electronic - Jungle": "60", "Fusion": "102", "Electronic - IDM": "99", "Ballad": "56", "Country": "18", "World": "42", "Jazz - Modern": "31", "Video Game": "8", "Funk": "32", "Electronic - Drum &amp; Bass": "6", "Alternative": "48", "Electronic - Minimal": "101", "Electronic - Gabber": "40", "Vocal Montage": "76", "Metal (general)": "36", "Electronic - Breakbeat": "9", "Soul": "25", "Electronic (general)": "1", "Punk": "35", "Pop - Synth": "61", "Electronic - Dance": "3", "Pop (general)": "12", "Trance - Progressive": "85", "Trance (general)": "71", "Disco": "58", "Electronic - House": "10", "Experimental": "46", "Trance - Goa": "66", "Rock - Hard": "14", "Trance - Dream": "67", "Spiritual": "47", "Metal - Extreme": "37", "Jazz (general)": "29", "Trance - Tribal": "70", "Classical": "20", "Hip-Hop": "22", "Bluegrass": "105", "Halloween": "82", "Jazz - Acid": "30", "Easy Listening": "107", "New Age": "44", "Fantasy": "52", "Blues": "19", "Other": "41", "Trance - Acid": "63", "Gothic": "38", "Electronic - Hardcore": "39", "One Hour Compo": "53", "Pop - Soft": "62", "Electronic - Techno": "7", "Religious": "49", "Folk": "21"}
    categories = []
    

    # refresh category list
    def update_categories(self):

        html = ahttp.get("http://modarchive.org/index.php?request=view_genres")

        rx_current = re.compile(r"""
            >\s+(\w[^<>]+)\s+</h1>  |
            <a\s[^>]+query=(\d+)&[^>]+>(\w[^<]+)</a>
        """, re.S|re.X)


        #-- archived shows
        sub = []
        self.categories = []
        for uu in rx_current.findall(html):
            (main, id, subname) = uu
            if main:
                self.categories.append(main)
                self.catmap[main] = 0
                sub = []
                self.categories.append(sub)
            else:
                sub.append(subname)
                self.catmap[subname] = id

        # .categories and .catmap are saved by reload_categories()
        pass



    # download links from dmoz listing
    def update_streams(self, cat):

        url = "http://modarchive.org/index.php"
        params = dict(query=self.catmap[cat], request="search", search_type="genre")
        html = ahttp.get(url, params)
        entries = []
        
        rx_mod = re.compile("""
            href="(https?://api\.modarchive\.org/downloads\.php[?]moduleid=(\d+)[#][^"]+)"
            .*?    ="format-icon">(\w+)<
            .*?    title="([^">]+)">([^<>]+)</a>
            .*?    >(?:Rated|Unrated)</a>\s*(\d*)
        """, re.X|re.S)
        
        for uu in rx_mod.findall(html):
            (url, id, fmt, title, file, rating) = uu
            #log.DATA( uu )
            entries.append({
                "genre": cat,
                "url": url,
                "id": id,
                "format": "audio/mod+zip",
                "title": title,
                "playing": file,
                "listeners": int(rating if rating else 0),
                "homepage": "http://modarchive.org/index.php?request=view_by_moduleid&query="+id,
            })
        
        # done    
        return entries
        

