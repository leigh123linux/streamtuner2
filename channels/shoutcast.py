#
# api: streamtuner2
# title: shoutcast
# description: Channel/tab for Shoutcast.com directory
# depends: pq, re, http
# version: 1.2
# author: Mario
# original: Jean-Yves Lefort
#
# Shoutcast is a server software for audio streaming. It automatically spools
# station information on shoutcast.com, which this plugin can read out. But
# since the website format is often changing, we now use PyQuery HTML parsing
# in favour of regular expression (which still work, are faster, but not as
# reliable).
#
# This was previously a built-in channel plugin. It just recently was converted
# from a glade predefined GenericChannel into a ChannelPlugin.
#
#
# NOTES
#
# Just found out what Tunapie uses:
#    http://www.shoutcast.com/sbin/newxml.phtml?genre=Top500
# It's a simpler list format, no need to parse HTML. However, it also lacks
# homepage links. But maybe useful as alternate fallback...
# Also:
#   http://www.shoutcast.com/sbin/newtvlister.phtml?alltv=1
#   http://www.shoutcast.com/sbin/newxml.phtml?search=
#
#
#


import http
import urllib
import re
from pq import pq
from config import conf
#from channels import *    # works everywhere but in this plugin(???!)
import channels
__print__ = channels.__print__



# SHOUTcast data module                                          ----------------------------------------
class shoutcast(channels.ChannelPlugin):

        # desc
        api = "streamtuner2"
        module = "shoutcast"
        title = "SHOUTcast"
        version = 1.2
        homepage = "http://www.shoutcast.com/" 
        base_url = "http://shoutcast.com/"
        listformat = "audio/x-scpls"

        # settings
        config = [
            dict(name="pyquery", type="boolean", value=0, description="Use more reliable PyQuery HTML parsing\ninstead of faster regular expressions."),
            dict(name="debug", type="boolean", value=0, description="enable debug output"),
        ]
        
        # categories
        categories = ['Alternative', ['Adult Alternative', 'Britpop', 'Classic Alternative', 'College', 'Dancepunk', 'Dream Pop', 'Emo', 'Goth', 'Grunge', 'Hardcore', 'Indie Pop', 'Indie Rock', 'Industrial', 'Modern Rock', 'New Wave', 'Noise Pop', 'Power Pop', 'Punk', 'Ska', 'Xtreme'], 'Blues', ['Acoustic Blues', 'Chicago Blues', 'Contemporary Blues', 'Country Blues', 'Delta Blues', 'Electric Blues'], 'Classical', ['Baroque', 'Chamber', 'Choral', 'Classical Period', 'Early Classical', 'Impressionist', 'Modern', 'Opera', 'Piano', 'Romantic', 'Symphony'], 'Country', ['Americana', 'Bluegrass', 'Classic Country', 'Contemporary Bluegrass', 'Contemporary Country', 'Honky Tonk', 'Hot Country Hits', 'Western'], 'Decades', ['30s', '40s', '50s', '60s', '70s', '80s', '90s'], 'Easy Listening', ['Exotica', 'Light Rock', 'Lounge', 'Orchestral Pop', 'Polka', 'Space Age Pop'], 'Electronic', ['Acid House', 'Ambient', 'Big Beat', 'Breakbeat', 'Dance', 'Demo', 'Disco', 'Downtempo', 'Drum and Bass', 'Electro', 'Garage', 'Hard House', 'House', 'IDM', 'Jungle', 'Progressive', 'Techno', 'Trance', 'Tribal', 'Trip Hop'], 'Folk', ['Alternative Folk', 'Contemporary Folk', 'Folk Rock', 'New Acoustic', 'Traditional Folk', 'World Folk'], 'Inspirational', ['Christian', 'Christian Metal', 'Christian Rap', 'Christian Rock', 'Classic Christian', 'Contemporary Gospel', 'Gospel', 'Southern Gospel', 'Traditional Gospel'], 'International', ['African', 'Arabic', 'Asian', 'Bollywood', 'Brazilian', 'Caribbean', 'Celtic', 'Chinese', 'European', 'Filipino', 'French', 'Greek', 'Hindi', 'Indian', 'Japanese', 'Jewish', 'Klezmer', 'Korean', 'Mediterranean', 'Middle Eastern', 'North American', 'Russian', 'Soca', 'South American', 'Tamil', 'Worldbeat', 'Zouk'], 'Jazz', ['Acid Jazz', 'Avant Garde', 'Big Band', 'Bop', 'Classic Jazz', 'Cool Jazz', 'Fusion', 'Hard Bop', 'Latin Jazz', 'Smooth Jazz', 'Swing', 'Vocal Jazz', 'World Fusion'], 'Latin', ['Bachata', 'Banda', 'Bossa Nova', 'Cumbia', 'Latin Dance', 'Latin Pop', 'Latin Rock', 'Mariachi', 'Merengue', 'Ranchera', 'Reggaeton', 'Regional Mexican', 'Salsa', 'Tango', 'Tejano', 'Tropicalia'], 'Metal', ['Black Metal', 'Classic Metal', 'Extreme Metal', 'Grindcore', 'Hair Metal', 'Heavy Metal', 'Metalcore', 'Power Metal', 'Progressive Metal', 'Rap Metal'], 'Misc', [], 'New Age', ['Environmental', 'Ethnic Fusion', 'Healing', 'Meditation', 'Spiritual'], 'Pop', ['Adult Contemporary', 'Barbershop', 'Bubblegum Pop', 'Dance Pop', 'Idols', 'JPOP', 'Oldies', 'Soft Rock', 'Teen Pop', 'Top 40', 'World Pop'], 'Public Radio', ['College', 'News', 'Sports', 'Talk'], 'Rap', ['Alternative Rap', 'Dirty South', 'East Coast Rap', 'Freestyle', 'Gangsta Rap', 'Hip Hop', 'Mixtapes', 'Old School', 'Turntablism', 'West Coast Rap'], 'Reggae', ['Contemporary Reggae', 'Dancehall', 'Dub', 'Ragga', 'Reggae Roots', 'Rock Steady'], 'Rock', ['Adult Album Alternative', 'British Invasion', 'Classic Rock', 'Garage Rock', 'Glam', 'Hard Rock', 'Jam Bands', 'Piano Rock', 'Prog Rock', 'Psychedelic', 'Rockabilly', 'Surf'], 'Soundtracks', ['Anime', 'Kids', 'Original Score', 'Showtunes', 'Video Game Music'], 'Talk', ['BlogTalk', 'Comedy', 'Community', 'Educational', 'Government', 'News', 'Old Time Radio', 'Other Talk', 'Political', 'Scanner', 'Spoken Word', 'Sports', 'Technology'], 'Themes', ['Adult', 'Best Of', 'Chill', 'Eclectic', 'Experimental', 'Female', 'Heartache', 'Instrumental', 'LGBT', 'Party Mix', 'Patriotic', 'Rainy Day Mix', 'Reality', 'Sexy', 'Shuffle', 'Travel Mix', 'Tribute', 'Trippy', 'Work Mix']]
        #["default", [], 'TopTen', [], 'Alternative', ['College', 'Emo', 'Hardcore', 'Industrial', 'Punk', 'Ska'], 'Americana', ['Bluegrass', 'Blues', 'Cajun', 'Folk'], 'Classical', ['Contemporary', 'Opera', 'Symphonic'], 'Country', ['Bluegrass', 'New Country', 'Western Swing'], 'Electronic', ['Acid Jazz', 'Ambient', 'Breakbeat', 'Downtempo', 'Drum and Bass', 'House', 'Trance', 'Techno'], 'Hip Hop', ['Alternative', 'Hardcore', 'New School', 'Old School', 'Turntablism'], 'Jazz', ['Acid Jazz', 'Big Band', 'Classic', 'Latin', 'Smooth', 'Swing'], 'Pop/Rock', ['70s', '80s', 'Classic', 'Metal', 'Oldies', 'Pop', 'Rock', 'Top 40'], 'R&B/Soul', ['Classic', 'Contemporary', 'Funk', 'Smooth', 'Urban'], 'Spiritual', ['Alternative', 'Country', 'Gospel', 'Pop', 'Rock'], 'Spoken', ['Comedy', 'Spoken Word', 'Talk'], 'World', ['African', 'Asian', 'European', 'Latin', 'Middle Eastern', 'Reggae'], 'Other/Mixed', ['Eclectic', 'Film', 'Instrumental']]
        current = ""
        default = "Alternative"
        empty = ""

        
        # redefine
        streams = {}
        
            
        # extracts the category list from shoutcast.com,
        # sub-categories are queried per 'AJAX'
        def update_categories(self):
            html = http.get(self.base_url)
            self.categories = ["default"]
            __print__( html )

            # <h2>Radio Genres</h2>
	    rx_main = re.compile(r'<li class="prigen" id="(\d+)".+?<a href="/radio/([\w\s]+)">[\w\s]+</a></li>', re.S)
	    rx_sub = re.compile(r'<a href="/radio/([\w\s\d]+)">[\w\s\d]+</a></li>')
            for uu in rx_main.findall(html):
                __print__(uu)
		(id,name) = uu
                name = urllib.unquote(name)

                # main category
                self.categories.append(name)

                # sub entries
                html = http.ajax("http://shoutcast.com/genre.jsp", {"genre":name, "id":id})
                __print__(html)
                sub = rx_sub.findall(html)
                self.categories.append(sub)

            # it's done
            __print__(self.categories)
            conf.save("cache/categories_shoutcast", self.categories)
            pass



        #def strip_tags(self, s):
        #    rx = re.compile(""">(\w+)<""")
        #    return " ".join(rx.findall(s))

        # downloads stream list from shoutcast for given category
        def update_streams(self, cat, search=""):

            if (not cat or cat == self.empty):
                __print__("nocat")
                return []
            ucat = urllib.quote(cat)


            # loop
            entries = []
            next = 0
            max = int(conf.max_streams)
            count = max
            rx_stream = None
            rx_next = re.compile("""onclick="showMoreGenre""")

            try:
               while (next < max):

                  # page
                  url = "http://www.shoutcast.com/genre-ajax/" + ucat
                  referer = url.replace("/genre-ajax", "/radio")
                  params = { "strIndex":"0", "count":str(count), "ajax":"true", "mode":"listeners", "order":"desc" }
                  html = http.ajax(url, params, referer)   #,feedback=self.parent.status)

                  __print__(html)

                  # regular expressions
                  if not conf.get("pyquery") or not pq:
                  
                      # new extraction regex
                      if not rx_stream:
                          rx_stream = re.compile(
                              """
                              <a\s+class="?playbutton\d?[^>]+id="(\d+)".+?
                              <a\s+class="[\w\s]*title[\w\s]*"[^>]+href="(http://[^">]+)"[^>]*>([^<>]+)</a>.+?
                              (?:Recently\s*played|Coming\s*soon|Now\s*playing):\s*([^<]*).+?
                              ners">(\d*)<.+?
                              bitrate">(\d*)<.+?
                              type">([MP3AAC]*)
                              """,
                              re.S|re.I|re.X
                          )

                      # extract entries
                      self.parent.status("parsing document...")
                      __print__("loop-rx")
                      for m in rx_stream.findall(html):
                          (id, homepage, title, playing, ls, bit, fmt) = m
                          __print__(uu)
                          entries += [{
                              "title": self.entity_decode(title),
                              "url": "http://yp.shoutcast.com/sbin/tunein-station.pls?id=" + id,
                              "homepage": http.fix_url(homepage),
                              "playing": self.entity_decode(playing),
                              "genre": cat, #self.strip_tags(uu[4]),
                              "listeners": int(ls),
                              "max": 0, #int(uu[6]),
                              "bitrate": int(bit),
                              "format": self.mime_fmt(fmt),
                          }]

                  # PyQuery parsing
                  else:
                      # iterate over DOM
                      for div in (pq(e) for e in pq(html).find("div.dirlist")):

                          entries.append({
                               "title": div.find("a.playbutton,a.playbutton1").attr("title"),
                               "url": div.find("a.playbutton,a.playbutton1").attr("href"),
                               "homepage": http.fix_url(div.find("a.div_website").attr("href")),
                               "playing": div.find("div.playingtext").attr("title"),
   #                            "title": div.find("a.clickabletitleGenre, div.stationcol a").attr("title"),
   #                            "url": div.find("a.playbutton, a.playbutton1, a.playimage").attr("href"),
   #                            "homepage": http.fix_url(div.find("a.playbutton.clickabletitle, a[target=_blank], a.clickabletitleGenre, a.clickabletitle, div.stationcol a, a").attr("href")),
   #                            "playing": div.find("div.playingtextGenre, div.playingtext").attr("title"),
                               "listeners": int(div.find("div.dirlistners").text()),
                               "bitrate": int(div.find("div.dirbitrate").text()),
                               "format": self.mime_fmt(div.find("div.dirtype").text()),
                               "max": 0,
                               "genre": cat,
                              # "title2": e.find("a.playbutton").attr("name"),
                          })


                  # display partial results (not strictly needed anymore, because we fetch just one page)
                  self.parent.status()
                  self.update_streams_partially_done(entries)
                  
                  # more pages to load?
                  if (re.search(rx_next, html)):
                     next += count
                  else:
                     next = 99999
                     
            except:
               return entries
            
            #fin
            __print__(entries)
            return entries


