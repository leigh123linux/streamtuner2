# api: st2
# title: live365 channel
#
# 2.0.9 fixed by Abhisek Sanyal
#




# streamtuner2 modules
from config import conf
from mygtk import mygtk
import http
from channels import *
from config import __print__, dbg

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
            self.categories = []

            # fetch page
            html = http.get("http://www.live365.com/index.live", feedback=self.parent.status);
            rx_genre = re.compile("""
                href=['"]/genres/([\w\d%+]+)['"][^>]*>
                (   (?:<nobr>)?   )
                ( \w[-\w\ /'.&]+ )
                (   (?:</a>)?   )
            """, re.X|re.S)

            # collect
            last = []
            for uu in rx_genre.findall(html):
                (link, sub, title, main) = uu

                # main
                if main and not sub:
                    self.categories.append(title)
                    self.categories.append(last)
                    last = []
                # subcat
                else:
                    last.append(title)

            # don't forget last entries
            self.categories.append(last)



        # extract stream infos
        def update_streams(self, cat, search=""):
        
            # search / url
            if (not search):
                url = "http://www.live365.com/cgi-bin/directory.cgi?first=1&rows=200&mode=2&genre=" + self.cat2tag(cat)
            else:
                url = "http://www.live365.com/cgi-bin/directory.cgi?site=..&searchdesc=" + urllib.quote(search) + "&searchgenre=" + self.cat2tag(cat) + "&x=0&y=0"
            html = http.get(url, feedback=self.parent.status)
            # we only need to download one page, because live365 always only gives 200 results
	    
            # terse format            
            rx = re.compile(r"""
            ['"](OK|PM_ONLY|SUBSCRIPTION).*?
            href=['"](http://www.live365.com/stations/\w+)['"].*?
            page['"]>([^<>]*)</a>.*?
            CLASS=['"]genre-link['"][^>]*>(.+?)</a>.+?
            &station_id=(\d+).+?
            class=["']desc-link['"][^>]+>([^<>]*)<.*?
            =["']audioQuality.+?>(\d+)\w<.+?
            >DrawListenerStars\((\d+),.+?
            >DrawRatingStars\((\d+),\s+(\d+),.*?
                """, re.X|re.I|re.S|re.M)
#            src="(http://www.live365.com/.+?/stationlogo\w+.jpg)".+?

            # append entries to result list
            __print__( dbg.DATA, html )
            ls = []
            for row in rx.findall(html):
                __print__( dbg.DATA, row )
                points = int(row[8])
                count = int(row[9])
                ls.append({
                    "launch_id": row[0],
                    "sofo": row[0],  # subscribe-or-fuck-off status flags
                    "state":  (""  if  row[0]=="OK"  else  gtk.STOCK_STOP),
                    "homepage": entity_decode(row[1]),
                    "title": entity_decode(row[2]),
                    "genre": self.strip_tags(row[3]),
                    "bitrate": int(row[6]),
                    "listeners": int(row[7]),
                    "max": 0,
                    "rating": (points + count**0.4) / (count - 0.001*(count-0.1)),   # prevents division by null, and slightly weights (more votes are higher scored than single votes)
                    "rating_points": points,
                    "rating_count": count,
                    # id for URL:
                    "station_id": row[4],
                    "url": self.base_url + "play/" + row[4],
                    "description": entity_decode(row[5]),
                   #"playing": row[10],
                   # "deleted": row[0] != "OK",
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


