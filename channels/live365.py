#
# api: streamtuner2
# title: live365
# state: deprecated
#
# Live365 probably won't be made working anymore. Too many Javascript+XML blobs.
# Pretty cumbersome/sluggish to use the actual website nowadays.
#





# streamtuner2 modules
from config import conf
from mygtk import mygtk
import http
from channels import *
from channels import __print__

# python modules
import re
import xml.dom.minidom
from xml.sax.saxutils import unescape as entity_decode, escape as xmlentities
import gtk
import copy
import urllib


# channel live365
class live365(ChannelPlugin):


        # desc
        api = "streamtuner2"
        module = "live365"
        title = "Live365"
        version = 0.1
        homepage = "http://www.live365.com/"
        base_url = "http://www.live365.com/"
        listformat = "url/http"
        mediatype = "audio/mpeg"

        # content
        categories = ['Alternative', ['Britpop', 'Classic Alternative', 'College', 'Dancepunk', 'Dream Pop', 'Emo', 'Goth', 'Grunge', 'Indie Pop', 'Indie Rock', 'Industrial', 'Lo-Fi', 'Modern Rock', 'New Wave', 'Noise Pop', 'Post-Punk', 'Power Pop', 'Punk'], 'Blues', ['Acoustic Blues', 'Chicago Blues', 'Contemporary Blues', 'Country Blues', 'Delta Blues', 'Electric Blues', 'Cajun/Zydeco'], 'Classical', ['Baroque', 'Chamber', 'Choral', 'Classical Period', 'Early Classical', 'Impressionist', 'Modern', 'Opera', 'Piano', 'Romantic', 'Symphony'], 'Country', ['Alt-Country', 'Americana', 'Bluegrass', 'Classic Country', 'Contemporary Bluegrass', 'Contemporary Country', 'Honky Tonk', 'Hot Country Hits', 'Western'], 'Easy Listening', ['Exotica', 'Lounge', 'Orchestral Pop', 'Polka', 'Space Age Pop'], 'Electronic/Dance', ['Acid House', 'Ambient', 'Big Beat', 'Breakbeat', 'Disco', 'Downtempo', "Drum 'n' Bass", 'Electro', 'Garage', 'Hard House', 'House', 'IDM', 'Jungle', 'Progressive', 'Techno', 'Trance', 'Tribal', 'Trip Hop'], 'Folk', ['Alternative Folk', 'Contemporary Folk', 'Folk Rock', 'New Acoustic', 'Traditional Folk', 'World Folk'], 'Freeform', ['Chill', 'Experimental', 'Heartache', 'Love/Romance', 'Music To ... To', 'Party Mix', 'Patriotic', 'Rainy Day Mix', 'Reality', 'Shuffle/Random', 'Travel Mix', 'Trippy', 'Various', 'Women', 'Work Mix'], 'Hip-Hop/Rap', ['Alternative Rap', 'Dirty South', 'East Coast Rap', 'Freestyle', 'Gangsta Rap', 'Old School', 'Turntablism', 'Underground Hip-Hop', 'West Coast Rap'], 'Inspirational', ['Christian', 'Christian Metal', 'Christian Rap', 'Christian Rock', 'Classic Christian', 'Contemporary Gospel', 'Gospel', 'Praise/Worship', 'Sermons/Services', 'Southern Gospel', 'Traditional Gospel'], 'International', ['African', 'Arabic', 'Asian', 'Brazilian', 'Caribbean', 'Celtic', 'European', 'Filipino', 'Greek', 'Hawaiian/Pacific', 'Hindi', 'Indian', 'Japanese', 'Jewish', 'Mediterranean', 'Middle Eastern', 'North American', 'Soca', 'South American', 'Tamil', 'Worldbeat', 'Zouk'], 'Jazz', ['Acid Jazz', 'Avant Garde', 'Big Band', 'Bop', 'Classic Jazz', 'Cool Jazz', 'Fusion', 'Hard Bop', 'Latin Jazz', 'Smooth Jazz', 'Swing', 'Vocal Jazz', 'World Fusion'], 'Latin', ['Bachata', 'Banda', 'Bossa Nova', 'Cumbia', 'Latin Dance', 'Latin Pop', 'Latin Rap/Hip-Hop', 'Latin Rock', 'Mariachi', 'Merengue', 'Ranchera', 'Salsa', 'Tango', 'Tejano', 'Tropicalia'], 'Metal', ['Extreme Metal', 'Heavy Metal', 'Industrial Metal', 'Pop Metal/Hair', 'Rap Metal'], 'New Age', ['Environmental', 'Ethnic Fusion', 'Healing', 'Meditation', 'Spiritual'], 'Oldies', ['30s', '40s', '50s', '60s', '70s', '80s', '90s'], 'Pop', ['Adult Contemporary', 'Barbershop', 'Bubblegum Pop', 'Dance Pop', 'JPOP', 'Soft Rock', 'Teen Pop', 'Top 40', 'World Pop'], 'R&B/Urban', ['Classic R&B', 'Contemporary R&B', 'Doo Wop', 'Funk', 'Motown', 'Neo-Soul', 'Quiet Storm', 'Soul', 'Urban Contemporary'], 'Reggae', ['Contemporary Reggae', 'Dancehall', 'Dub', 'Pop-Reggae', 'Ragga', 'Reggaeton', 'Rock Steady', 'Roots Reggae', 'Ska'], 'Rock', ['Adult Album Alternative', 'British Invasion', 'Classic Rock', 'Garage Rock', 'Glam', 'Hard Rock', 'Jam Bands', 'Prog/Art Rock', 'Psychedelic', 'Rock & Roll', 'Rockabilly', 'Singer/Songwriter', 'Surf'], 'Seasonal/Holiday', ['Anniversary', 'Birthday', 'Christmas', 'Halloween', 'Hanukkah', 'Honeymoon', 'Valentine', 'Wedding'], 'Soundtracks', ['Anime', "Children's/Family", 'Original Score', 'Showtunes'], 'Talk', ['Comedy', 'Community', 'Educational', 'Government', 'News', 'Old Time Radio', 'Other Talk', 'Political', 'Scanner', 'Spoken Word', 'Sports']]
        current = ""
        default = "Pop"
        empty = None
        
        # redefine
        streams = {}
        

        def __init__(self, parent=None):
        
            # override datamap fields  //@todo: might need a cleaner method, also: do we really want the stream data in channels to be different/incompatible?
            self.datamap = copy.deepcopy(self.datamap)
            self.datamap[5][0] = "Rating"
            self.datamap[5][2][0] = "rating"
            self.datamap[3][0] = "Description"
            self.datamap[3][2][0] = "description"
            
            # superclass
            ChannelPlugin.__init__(self, parent)


        # read category thread from /listen/browse.live
        def update_categories(self):
            return



        # extract stream infos
        def update_streams(self, cat, search=""):
        
            # search / url
            if (not search):
                url = "http://www.live365.com/genres/" + self.cat2tag(cat)
            else:
                url = "http://www.live365.com/cgi-bin/directory.cgi?mode=2&site=web&searchdesc=" + urllib.quote(search)
            html = http.get(url, feedback=self.parent.status)
            # we only need to download one page, because live365 always only gives 200 results

            # extract JS calls
            rx = re.compile(r"""
                    new\s+top\.Station;
                \s+ stn.set\("stationName",    \s+   "(\w+)"\);
                \s+ stn.set\("title",          \s+   "([^"]+)"\);
                \s+ stn.set\("id",             \s+   "(\d+)"\);
                \s+ stn.set\("listenerAccess", \s+   "(\w+)"\);
                \s+ stn.set\("status",         \s+   "(\w+)"\);
                \s+ stn.set\("serverMode",     \s+   "(\w+)"\);
                \s+ stn.set\("rating",         \s+   "(\d+)"\);
                \s+ stn.set\("ratingCount",    \s+   "(\d+)"\);
                \s+ stn.set\("tlh",            \s+   "(\d+)"\);
                \s+ stn.set\("imgUrl",         \s+   "([^"]+)"\);
                \s+ stn.set\("location",       \s+   "([^"]+)"\);
                """, re.X|re.I|re.S|re.M)

#('jtava', 'ANRLIVE.NET', '293643', 'PUBLIC', 'OK', 'OR', '298', '31',
#'98027', 'http://www.live365.com/userdata/37/15/1371537/stationlogo80x45.jpg', 'n/a')


            # append entries to result list
            __print__( html )
            ls = []
            for row in rx.findall(html):
                __print__( row )

                ls.append({
                    "launch_id": row[0],
                    "title": entity_decode(row[1]),
                    "station_id": row[2],
                    "sofo": row[3],
                    "state":  (""  if  row[4]=="OK"  else  gtk.STOCK_STOP),
                    "rating": int(row[6]),
                    "listeners": int(row[8]),
                    "img_": row[9],
                    "description": entity_decode(row[10]),
                    "max": 0,
                    "genre": cat,
                    "bitrate": 128,
                    "playing": "",
                    "url": "http://www.live365.com/cgi-bin/mini.cgi?version=3&templateid=xml&from=web&site=web&caller=&tag=web&station_name="+row[0]+"&_=1388870321828",
                    "format": "application/xml",
                })
            return ls
            
        # faster if we do it in _update() prematurely
        #def prepare(self, ls):
        #    GenericChannel.prepare(ls)
        #    for row in ls:
        #        if (not row["state"]):
        #            row["state"] = (gtk.STOCK_STOP, "") [row["sofo"]=="OK"]
        #    return ls

        
        # html helpers
        def cat2tag(self, cat):
            return urllib.quote(cat.lower()) #re.sub("[^a-z]", "", 
        def strip_tags(self, s):
            return re.sub("<.+?>", "", s)


