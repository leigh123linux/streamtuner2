# api: streamtuner2
# title: RCast
# description: Streaming server provider and station directory
# type: channel
# category: radio
# version: 0.2
# url: http://www.rcast.net/dir
# png: 
#    iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAABH0lEQVR42mPgZWXkNxdhsScH87Iw8DOAGHcDBf6Tg02FmW1RDPj97cvf/0BwJ4D/HyHNGAbc9uUBawaBf0BASDOGASBNIM1fHt34BaKRFd4CGg4C
#    eA0Agd9fPv255c39F90AXC6DG3ArSOwP1O9wDTc92cA23gqR/g3i3yvz/IFuMNgAeyBANx0Enk7M+Qlig5wO0wgCt1yZwepuBQj8sQUCsAG/3r74g+7k318//oWxYYaDwM/3r//A2GADsKUDGICxH7XG/wK75s8f
#    cEB/vnwU7C2MdADDn2+d+4VsADCKIc72ZPsHM/zvn99/cRpw050Z7O+nvVkYUfpmx4KfMDGcBiB7A90AZIzXgJ9vX4D9eceP9x9ZBhCDwQZQmp0BVv4354bQNGwAAAAASUVORK5CYII=
# priority: extra
# extraction-method: regex
#
# RCast.net is a provider for streaming servers, that also features
# a tidy and detailed station directory. It currently hosts/lists
# around 7700 individual stations.
#
# It lists direct streaming server addresses, homepages, currently
# playing songs, bitrate etc. It's also pretty quick, but only
# returns 10 results per page. Categories have to be collected
# manually though.


import re
import ahttp
from config import *
from channels import *


# rcast.net
class rcast (ChannelPlugin):

    # settings/data
    catmap = {}
    categories = ["top", "pop", "dance", "holiday", "jazz", "rock", "variety", "regional", "romanian", "disco", "chillout", "and", "urban", "mixed", "various", "hip", "hop", "trance", "rap", "techno", "house", "60s", "70s", "80s", "90s", "alternative", "blues", "comedy", "folk", "funk", "indie", "jungle", "amp", "oldies", "sports", "news", "fusion", "top40", "charts", "nederlandstalig", "soft", "radio", "station", "ostuni", "edm", "freestyle", "hard", "country", "metal", "all", "musicworld", "music", "zouk", "salsa", "world", "italy", "electronic", "happy", "international", "contemporary", "misc", "reggae", "talk", "latin", "turkish", "turkce", "slow", "italian", "talkshow", "electro", "dubstep", "40pop", "adult", "soul", "rnb", "1960", "1970", "1980", "1990", "2000", "2010", "more", "lounge", "eas", "decades", "hits", "new", "first", "club", "eurodance", "dancehall", "compas", "classic", "energy", "tribal", "brasil", "clubbing", "rave", "punk", "psytrance", "punkrock", "progressive", "ambient", "drum", "bass", "chill", "handsup", "hardstyle", "manele", "petrecere", "minimal", "electronica", "garage", "speak", "futbol", "europe", "themed", "seasonal", "holidays", "smooth", "christmas", "xmas", "genres", "navidad", "festive", "weihnachten", "christian", "swing", "trip", "acoustic", "underground", "deep", "downtempo", "soulful", "real", "hiphop", "rare", "groove", "other", "afro", "central", "northern", "motown", "classique", "prog", "remixes", "spanish", "age", "soundtracks", "soca", "ska", "disckofox", "schlager", "rockabilly", "roll", "electr", "nica", "classical", "easy", "listening", "bachata", "banda", "cumbia", "mariachi", "merengue", "ranchera", "reggaeton", "mexican", "none", "party", "discofox", "volksmusik", "piraten", "80er", "90er", "european", "deutsch", "fox", "dream", "religious", "discourse", "prayers", "portuguese", "celtic", "surf", "klavier", "piano", "improvisation", "brown", "noise", "psychill", "african", "tamil", "soundtrack", "japanese", "meditation", "40s", "big", "band", "old", "time", "neo", "love", "romance", "gangsta", "naija", "school", "urbano", "wave", "eclectic", "italia", "community", "video", "greece", "athens", "greek", "hardcore", "neurofunk", "public", "gospel", "inspiration", "turntablism", "acid", "dnb", "dutch", "future", "breakbeat", "trap", "freak", "classics", "funky", "west", "coast", "texas", "east", "experimental", "mixtapes", "dub", "tech", "entertainment", "tekno", "hardtekno", "break", "kizomba", "kuduro", "tejano", "oldskool", "metalcore", "south", "africa", "modern", "goth", "mento", "calypso", "post", "art", "kraut", "grunge", "hair", "heavy", "power", "best", "gothic", "darkwave", "ebm", "industrial", "college", "choral", "impressionist", "opera", "symphony", "orchestral", "inspirational", "cool", "xtreme", "extreme", "electric", "indigenous", "rhythm", "doo", "wop", "jump", "ballads", "50s", "cover", "listen", "bits", "laugh", "thm", "zeybekler", "worldbeat", "elettronica", "turbo", "mix", "western", "americana", "hindi", "irish", "varied", "goud", "van", "oud", "neder", "tangos", "folklore", "latinos", "recuerdos", "nacionales", "internacionales", "cuartetos", "cumbias", "tropical", "etc", "spiritual", "tehno", "comercial", "romania", "info", "artists", "british", "style", "hit", "latino", "etno", "pre", "populara", "espa", "raggaeton", "mixtape", "variadades", "portugues", "italiana", "educational", "compa", "sega", "kompa", "retro", "rumba", "ndombolo", "ngwasuma", "congolais", "soukouss", "coupe", "cale", "black", "rhythmc", "sport", "our", "passion", "romantic", "everything", "between", "the", "one", "channel", "bootlegs", "128k", "ghana", "acidjazz", "caribbean", "jewish", "indian", "brandnew2016"]
    titles = dict(listeners=False)
    has_search = True
    listformat = "srv"
    base = "http://www.rcast.net/dir"
    

    # use a static list for now
    def update_categories(self):
        self.categories = self.categories

    # get streems
    def update_streams(self, cat, search=None, max_pages=10):
        r = []

        # fetch
        html = ""
        if search: # pretty much identical (except first page should be /dir/?action=search and POST field)
            cat = search
            max_pages = 1
        for i in range(1, max_pages + 1):
            html += ahttp.get("%s/%s/page%s" % (self.base, cat, i))
            if not re.search('href="/dir/%s/page%s">Next' % (cat, i + 1), html):
                break

        # extract
        ls = re.findall("""
           <tr> .*?
           <audio\s+id="jp_audio_(\d+)" .*? src="([^"]+?);?"> .*?
           <h4.*?>([^<>]+)</a></h4> .*?
           <b>([^<>]*)</b> .*?
           <b\s+class[^>]+>([^<>]*)</b> .*?
           Genre:(.+?)</td> .*?
           </i>\s*(\d+)\s*Kbps<br>\s*(audio/[\w.-]+)
        """, html, re.X|re.S)
        #log.DATA(re.findall("(<audio.*?>)", html))
        
        # blocks
        for row in ls:
            try:
                log.UI(row)
                r.append(dict(
                    id = row[0],
                    url = row[1],
                    title = unhtml(row[2]),
                    playing = unhtml(row[3]),
                    homepage = unhtml(row[4]),
                    genre = unhtml(row[5]),
                    bitrate = to_int(row[6]),
                    format = row[7],
                    #listeners = to_int(listeners[5])
                ))
            except:
                pass #some field missing

        # done
        return r
        
        # (disabled): collect genres
        for row in r:
            for c in re.findall("(\w+)", row["genre"]):
                if c not in self.categories:
                    self.categories.append(c)


