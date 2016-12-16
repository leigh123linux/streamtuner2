# encoding: UTF-8
# api: streamtuner2
# title: RadioSure
# description: Huge radio station collection
# version: 0.5
# type: channel
# category: radio
# url: http://radiosure.com/
# config: -
# priority: extra
# png: 
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQAgMAAABinRfyAAAADFBMVEULDgpKTEmQko/19/S0inLcAAAAUklEQVQI12P4DwQMDvuBBIs92zcGHh2G
#   BQw+FvUPGDwq/n9gaPoj/5DB6b/TQwaH/18uMrjs/yPI4FP2R4kh1vBHPUO8SsAnBn8P9ocMYFNABADRrSa61FmXoAAAAABJRU5ErkJggg==
# extraction-method: csv
#
# RadioSure is a Windows freeware/shareware for playing internet
# stations. It comes with a huge database of streams.
#
# Fetches and keeps the ZIP/CSV database at maximum once per day.
# (Not updated more frequently.)


from config import *
from channels import *
import re
import ahttp
import zipfile
import time
import os.path

# RadioSure "static" radio list
class radiosure (ChannelPlugin):

    # description
    has_search = False
    listformat = "pls"
    audioformat = "audio/mpeg"
    titles = dict(listeners=False, playing="Description")
    zip = "http://www.radiosure.com/rsdbms/stations2.zip"
    tmp = conf.dir + "/cache/radiosure-stations2.zip"

    categories = [
        '-', '50s/60s', '70s/80s', '90s', 'Adult Contemporary', 'Adult Standards / Nostalgia',
        'African', 'All News', 'Americana', 'Arabic', 'Asian', 'Big Band/Swing',
        'Bluegrass', 'Blues', 'Bollywood', 'Children',
        'Choral-Religious', 'Christian', ['Christian-Contemporary',
        'Christian-Gospel', 'Christian-Pop Adult'], 'Classical',
        'College/University', 'Community', 'Country', 'Country-Classic', 'Dance/DJ',
        'Easy Listening', 'Eclectic', 'Electronica', ['Electronica-Ambient',
        'Electronica-Breakbeat', 'Electronica-Chillout', 'Electronica-Dance/DJ',
        'Electronica-Drum & Bass', 'Electronica-Electro',
        'Electronica-Experimental', 'Electronica-Hard House', 'Electronica-House',
        'Electronica-Industrial', 'Electronica-Lounge', 'Electronica-Techno',
        'Electronica-Trance'], 'Fajta', 'Folk', 'Funk', 'Hit Radio - Rock/Top 40',
        'Hits', 'Hits: New and Old', 'Hot Adult Contemporary', 'Independent',
        'Irish/Celtic', 'Islamic', 'Island', 'Island-Caribbean', 'Island-Hawaii',
        'Island-Reggae', 'Island-Reggaeton', 'Jazz', ['Jazz-Classical', 'Jazz-Easy Listening',
        'Jazz-Latin', 'Jazz-Smooth', 'Jazz-Swing'], 'Latin', 'Medieval',
        'Mexican', 'Middle Eastern', 'Musical Comedy', 'Musicals', 'Mystery Shows',
        'New Age', 'Old Time Radio', 'Oldies', 'Opera', 'Pop', 'Public Radio',
        'Rap/Hip Hop', 'Religious-Jewish', 'Religious-Sikhism',
        'Religious-Spiritual', 'Rock', ['Rock-Alternative', 'Rock-Classic',
        'Rock-Goth', 'Rock-Hair Bands', 'Rock-Hard/Metal', 'Rock-Heavy Metal',
        'Rock-Indie', 'Rock-Pop', 'Rock-Progressive', 'Rock-Punk',
        'Rock-Rockabilly'], 'Seasonal', 'Seasonal-Christmas', 'Seasonal-Halloween',
        'Soft Adult Contemporary', 'Soul/R&B', 'Soundtracks', 'Spanish', 'Talk',
        ['Talk-Business', 'Talk-Comedy', 'Talk-Government', 'Talk-News',
        'Talk-Progressive', 'Talk-Public Radio', 'Talk-Religious', 'Talk-Sports',
        'Talk-Weather'], 'Tejano', 'Tropical', 'University', 'Urban Contemporary',
        'Variety', 'Western', 'World/Folk'
    ]

    # categories are derived from the station list
    def update_categories(self):
        #self.categories = sorted(self.streams.keys())
        pass

    # import station list
    def update_streams(self, cat, search=None):
        streams = []
        # refresh zip file
        if not os.path.isfile(self.tmp) or os.path.getmtime(self.tmp) < (time.time() - 24*3600):
            with open(self.tmp, "wb") as f:
                f.write(ahttp.get(self.zip, binary=1))
        # get first file
        zip = zipfile.ZipFile(self.tmp)
        csv = zip.read(zip.namelist()[0])
        self.status("Updating streams from RadioSure CSV database")
        # fields = ["title", "playing", "genre", "country", "language", "url"]
        for e in re.findall(r"^([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+)\t([^\t]+(?:\t[^\t\n]{3,})*)", csv, re.M):
            if cat == e[2]:
                streams.append(dict(
                    title = e[0],
                    playing = e[1],
                    genre = e[2],
                    country = e[3],
                    language = e[4],
                    url = e[5].replace("\t", " ")#...
                ))
        return streams


