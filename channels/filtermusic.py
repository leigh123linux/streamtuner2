# encoding: UTF-8
# api: streamtuner2
# title: filtermusic
# description: Daily refreshed list of electronic+dance music streams.
# version: 0.1
# type: channel
# url: http://filtermusic.net/
# category: radio
# config:
#   { name: filtermusic_src, type: select, value: web, select: "web=Website|xml=XML Data|buf=Buffered", description: "Which data source to read from. (Both HTML and XML extraction are speedy.)" }
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAB3RJTUUH3wQeBA4mIX2CmQAAABl0RVh0Q29tbWVudABDcmVhdGVkIHdpdGggR0lNUFeBDhcAAAGISURBVCjPnVI9SyNRFD333slMMhrNjBJU0FSLIlovy6IWbmelhRJ/gI2lkMXfIOwv2K38qizstFCs3B+wLFhoIfiR1cggkXzMvHnPIiG6
#   GkE8zYXLPfe8c94F2oAkk7CHHLIIb4AAEIlkcuJmARr8OTxW+pKe9l6PSqN0jOe9hd3014J09tdP96SHSLh8GKirsM1+TvnZ5RN/buO5ItvcUH4BCwC7vex0Vf5stroGMKFu+3omKymdfUTMrs9uDyczAHzfz+VyIpwgu1u8NGccSjbFUyOz/vyOUVVoDZbq3+1gd6lQWMnn85PTEzPR4mdnKjLhrS6uBasArNrZ3t36N29u6/7ge/1038QRECul
#   arWaNrqLvV/lHx2U/pQYbXowUTUuXwJGV0rxQ/H/sKkU/yuqC4dSfdZA0wMAELd+4wUhNFUABro52Spvg54l9y7Cq1g/RiBwAvTkQURs2waBwQARiGE93RKJzW5v/fxIl68bXdd1gyA4Pv6tlLqLbyJEoamX4iI+gEdAknsz9gP1pgAAAABJRU5ErkJggg==
# x-doc:
#   http://code.google.com/p/filtermusic-dot-net/source/browse/
# priority: extra
#
#
# Filtermusic.net is a radio collection with primarily electronic
# and dance music stations.
#
#  · All entries come with direct server stream URLs.
#  · No homepage listings, or further genre details etc.


from config import *
from channels import *
import ahttp
import re
import xml.etree.ElementTree as ET


# filtermusic.net
class filtermusic (ChannelPlugin):

    # control attributes
    has_search = False
    listformat = "srv"
    audioformat = "audio/mpeg"
    titles = dict(listeners=False, bitrate=False, playing=False)
    categories = ["House / Dance", "Lounge Grooves", "Rock / Metal", "Breaks / Drum'n'Bass", "Various / Independent", "Downtempo / Ambient", "60's / 70's / 80's / 90's", "Hits / Mainstream", "Electronica / Industrial", "Techno / Trance", "HipHop / RnB", "Classical", "Eclectic", "Funk / Soul / Disco", "Reggae / Dub / Dancehall", "International / Ethnic", "Jazz", "Latin / Salsa / Tango"]


    # static
    def update_categories(self):
        pass


    # Refresh station list
    def update_streams(self, cat, search=None):
        if conf.filtermusic_src == "web":
            return self.from_web(cat)
        else:
            return self.from_xml(cat)


    # Extract directly from filtermusic.net html
    def from_web(self, cat):
        ucat = re.sub("\W+", "-", cat.lower().replace("'", ""))
        html = ahttp.get("http://filtermusic.net/{}".format(ucat))

        ls = re.findall("""<h4>(.*?)</h4><p>(.*?)</p>.*?href='(.*?)'""", html)
        r = [
            dict(genre=cat, title=title, playing=descr, url=url)
            for title,descr,url in ls
        ]
        return r


    # Parse and cache XML,
    # Stucture is: <z> <g> id="Genre"> <t id="Title"> <u>URL</u> </t> ... </g> ... </z>
    def from_xml(self, cat):
        buf = {}
        z = ET.fromstring(ahttp.get("http://www.filtermusic.net/xml/list.2.0.xml"))
        for g in z:
            try:
                genre = g.attrib["id"]
                buf[genre] = []
            except:
                # no group "id" for trailing <r>..</r> tag
                continue
            for t in g:
                buf[genre].append(dict(genre=genre, title=t.attrib.get("id"), url="http://"+t[0].text))
        if conf.filtermusic_src == "buf":
            self.streams = buf
        return buf[cat]


