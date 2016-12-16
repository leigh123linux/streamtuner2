# encoding: UTF-8
# api: streamtuner2
# title: GrLittleRadio
# description: Static list from Great Little Radio Player
# url: http://sourceforge.net/projects/glrp/
# version: 0.2
# type: channel
# category: playlist
# config: -
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QAAAAAAAD5Q7t/AAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3wUFEQge/7AFNAAAAgpJ
#   REFUOMuFk7trVFEQxn9zz9nc3Tw0CstGkCBoUHfhRgyIoF3wkRAUxEUrK7ESSWehFgpqI8TCTtQ/QCsLSSFisFFUSClBQzCJaPBBYkx2c+89Y3GyeW2iA6c4Z4Zvvvm+
#   OUJZ4bHwYUrtpae0B0JGQVk/RB3p6U4mLhyQSuGGIgCqmokGeA3sEsHwr1Bc7Ph2rIMjd0/KmKiqRAO8SpVDqmANtIQwPQ+xAyPr0ABU+Nh/mEh6H2j7+DTDiWMLgA1g
#   ayOUCtBg4MUnmK1CaFeDGKG6Ocd+GztCgUwtEQikDt5NgAmgby9kLQx/gckZ+DXvWTkIZxfIWGSRExCn8KgMzaG/5yyoQCWGc10wtwDXn3swI75ZsKSNQqkNOvKLGlTg
#   9ku4OgijP0AEchk4UYR0hUe2ThyFhRTOP/GFArwdhzt90LXd51dGsFbhQODNZ5iPl2k2WBgc8ZrU1dfb7EepJMtvczFEbeD0PwA1evkmuNYNrVnYlIXju6EcQeLqASzq
#   24rAyHffOTRwphN69oBz0Jrz3fONMDS6vFyqYEWIFZKaiEfvQ7Gw5Owqhb/O+F1oMBBAksuQyu+q2oP3eK9KpGtGWW+Ha2vjYPJUiWLQEkrSvZNehDEjpCIQBBsc74pT
#   mNrXxtlbPTIjTVeUPzeFy8+0eWiUHdUEg2z8GY3gom1MPizLTy4qfwFNC7cqp8RdxgAAAABJRU5ErkJggg==
# priority: extra
# extraction-method: csv
#
# Imports the playlist CSV from Great Little Radio Player.


import csv
from config import *
from channels import *
import ahttp
from compat2and3 import gzip_decode


# CSV list from GLRP
class glrp (ChannelPlugin):

    # control flags
    has_search = False
    listformat = "srv"
    audioformat = "audio/mpeg"
    titles = dict(listeners=False, bitrate=False, playing="Location")


    # Imports the CSV once and populates streams
    def update_categories(self):

        dat = ahttp.get("http://fossil.include-once.org/streamtuner2/cat/contrib/glrp.csv.gz", binary=1)
        dat = gzip_decode(dat).decode("utf-8")

        self.streams = {}
        if dat:
            ls = csv.reader(dat.split("\n"))
            for title, url, genre, location, fav in [x for x in ls if len(x)==5]:
                if not self.streams.get(genre):
                    self.streams[genre] = []
                self.streams[genre].append(dict(
                    title=title, url=url, genre=genre, playing=location, favorite=len(fav)
                ))
            self.save()
        self.categories = sorted(self.streams.keys())


    # Just returns existing entries
    def update_streams(self, cat, search=None):
        return self.streams.get(cat, [])
      
