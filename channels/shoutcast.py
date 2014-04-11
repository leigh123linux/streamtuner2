#
# api: streamtuner2
# title: shoutcast
# description: Channel/tab for Shoutcast.com directory
# depends: pq, re, http
# version: 1.3
# author: Mario
# original: Jean-Yves Lefort
#
# Shoutcast is a server software for audio streaming. It automatically spools
# station information on shoutcast.com, which this plugin can read out.
#
# After its recent aquisition the layout got slimmed down considerably. So
# there's not a lot of information to fetch left. And this plugin is now back
# to defaulting to regex extraction instead of HTML parsing & DOM extraction.
#
#
#


import ahttp as http
import re
from config import conf, __print__, dbg
from pq import pq
#from channels import *    # works everywhere but in this plugin(???!)
import channels
from compat2and3 import urllib



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
            self.categories = []
            __print__( dbg.DATA, html )

            # <h2>Radio Genres</h2>
            rx = re.compile(r'<li((?:\s+id="\d+"\s+class="files")?)><a href="\?action=sub&cat=([\w\s]+)#(\d+)">[\w\s]+</a>', re.S)
            sub = []
            for uu in rx.findall(html):
                __print__( dbg.DATA, uu )
                (main,name,id) = uu
                name = urllib.unquote(name)

                # main category
                if main:
                    if sub:
                        self.categories.append(sub)
                        sub = []
                    self.categories.append(name)
                else:
                    sub.append(name)

            # it's done
            __print__( dbg.PROC, self.categories )
            conf.save("cache/categories_shoutcast", self.categories)
            pass



        #def strip_tags(self, s):
        #    rx = re.compile(""">(\w+)<""")
        #    return " ".join(rx.findall(s))

        # downloads stream list from shoutcast for given category
        def update_streams(self, cat, search=""):

            if (not cat or cat == self.empty):
                __print__( dbg.ERR, "nocat" )
                return []
            ucat = urllib.quote(cat)


            # loop
            entries = []
            next = 0
            max = int(conf.max_streams)
            count = max
            rx_stream = None

            try:
               if (next < max):


                  #/radiolist.cfm?action=sub&string=&cat=Oldies&_cf_containerId=radiolist&_cf_nodebug=true&_cf_nocache=true&_cf_rc=0
                  #/radiolist.cfm?start=19&action=sub&string=&cat=Oldies&amount=18&order=listeners
                  # page
                  url = "http://www.shoutcast.com/radiolist.cfm?action=sub&string=&cat="+ucat+"&order=listeners&amount="+str(count)
                  __print__(dbg.HTTP, url)
                  referer = "http://www.shoutcast.com/?action=sub&cat="+ucat
                  params = {} # "strIndex":"0", "count":str(count), "ajax":"true", "mode":"listeners", "order":"desc" }
                  html = http.ajax(url, params, referer)   #,feedback=self.parent.status)

                  __print__(dbg.DATA, html)
                  #__print__(re.compile("id=(\d+)").findall(html));


                  # With the new shallow <td> lists it doesn't make much sense to use
                  # the pyquery DOM traversal. There aren't any sensible selectors to
                  # extract values; it's just counting the tags.


                  # regular expressions (default)
                  if not conf.get("pyquery") or not pq:

                      # new html
                      """ 
                      <tr>
                         <td width="6%"><a href="#" onClick="window.open('player/?radname=Schlagerhoelle%20%2D%20das%20Paradies%20fr%20Schlager%20%20und%20Discofox&stationid=14687&coding=MP3','radplayer','height=232,width=776')"><img class="icon transition" src="/img/icon-play.png" alt="Play"></a></td>
                         <td width="30%"><a class="transition" href="http://yp.shoutcast.com/sbin/tunein-station.pls?id=14687">Schlagerhoelle - das Paradies fr Schlager  und Discofox</a></td>
                         <td width="12%" style="text-align:left;" width="10%">Oldies</td>
                         <td width="12%" style="text-align:left;" width="10%">955</td>
                         <td width="12%" style="text-align:left;" width="10%">128</td>
                         <td width="12%" style="text-align:left;" width="10%">MP3</td>
                      </tr>
                      """
                  
                      # new extraction regex
                      if not rx_stream:
                          rx_stream = re.compile(
                              """
                               <a [^>]+  href="http://yp.shoutcast.com/sbin/tunein-station.pls\?
                                         id=(\d+)">   ([^<>]+)   </a>  </td>
                               \s+  <td [^>]+  >([^<>]+)</td>
                               \s+  <td [^>]+  >(\d+)</td>
                               \s+  <td [^>]+  >(\d+)</td>
                               \s+  <td [^>]+  >(\w+)</td>
                              """,
                              re.S|re.I|re.X
                          )


                      # extract entries
                      self.parent.status("parsing document...")
                      __print__(dbg.PROC, "channels.shoutcast.update_streams: regex scraping mode")

                      for m in rx_stream.findall(html):
                          #__print__(m)
                          (id, title, genre, listeners, bitrate, fmt) = m
                          entries += [{
                              "id": id,
                              "url": "http://yp.shoutcast.com/sbin/tunein-station.pls?id=" + id,
                              "title": self.entity_decode(title),
                              #"homepage": http.fix_url(homepage),
                              #"playing": self.entity_decode(playing),
                              "genre": genre,
                              "listeners": int(listeners),
                              "max": 0, #int(uu[6]),
                              "bitrate": int(bitrate),
                              "format": self.mime_fmt(fmt),
                          }]


                  # PyQuery parsing
                  else:
                      # iterate over DOM
                      for div in (pq(e) for e in pq(html).find("tr")):

                          entries.append({
                               "title": div.find("a.transition").text(),
                               "url": div.find("a.transition").attr("href"),
                               "homepage": "",
                               "listeners": int(div.find("td:eq(3)").text()),
                               "bitrate": int(div.find("td:eq(4)").text()),
                               "format": self.mime_fmt(div.find("td:eq(5)").text()),
                               "max": 0,
                               "genre": cat,
                          })


                  # display partial results (not strictly needed anymore, because we fetch just one page)
                  self.parent.status()
                  self.update_streams_partially_done(entries)
                  
                  # more pages to load?
                  next = 99999
                     
            except Exception as e:
               __print__(dbg.ERR, e)
               return entries
            
            #fin
            __print__(dbg.DATA, entries)
            return entries


