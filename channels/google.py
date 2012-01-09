#
# encoding: ISO-8859-1
# api: streamtuner2
# title: google stations
# description: Looks up web radio stations from DMOZ/Google directory
# depends: channels, re, http
# version: 0.1
# author: Mario, original: Jean-Yves Lefort
#
# This is a plugun from streamtuner1. It has been rewritten for the
# more mundane plugin API of streamtuner2 - reimplementing ST seemed
# to much work.
# Also it has been rewritten to query DMOZ directly. Google required
# the use of fake User-Agents for access, and the structure on DMOZ
# is simpler (even if less HTML-compliant). DMOZ probably is kept
# more up-to-date as well.
# PS: we need to check out //musicmoz.org/
#


# Copyright (c) 2003, 2004 Jean-Yves Lefort
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of Jean-Yves Lefort nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


import re, os, gtk
from channels import *
from xml.sax.saxutils import unescape as entity_decode, escape as xmlentities
import http


### constants #################################################################


GOOGLE_DIRECTORY_ROOT	= "http://www.dmoz.org"
CATEGORIES_URL_POSTFIX	= "/Arts/Music/Sound_Files/MP3/Streaming/Stations/"
#GOOGLE_DIRECTORY_ROOT	= "http://directory.google.com"
#CATEGORIES_URL_POSTFIX	= "/Top/Arts/Music/Sound_Files/MP3/Streaming/Stations/"
GOOGLE_STATIONS_HOME	= GOOGLE_DIRECTORY_ROOT + CATEGORIES_URL_POSTFIX

"""<li><a href="/Arts/Music/Sound_Files/MP3/Streaming/Stations/Jazz/"><b>Jazz</b></a>"""
re_category	= re.compile('<a href="(.+)">(<b>)([^:]+?)(</b>)</a>', re.I|re.M)

#re_stream	= re.compile('^<td><font face="arial,sans-serif"><a href="(.*)">(.*)</a>')
#re_description	= re.compile('^<br><font size=-1> (.*?)</font>')
"""<li><a href="http://www.atlantabluesky.com/">Atlanta Blue Sky</a> - Rock and alternative streaming audio. Live real-time requests."""
re_stream_desc	= re.compile('^<li><a href="(.*)">([^<>]+)</a>( - )?([^<>\n\r]+)', re.M|re.I)


######


# Google Stations is actually now DMOZ Stations
class google(ChannelPlugin):

    # description
    title = "Google"
    module = "google"
    homepage = GOOGLE_STATIONS_HOME
    version = 0.2
    
    # config data
    config = [
#        {"name": "theme", "type": "text", "value":"Tactile", "description":"Streamtuner2 theme; no this isn't a google-specific option. But you know, the plugin options are a new toy."},
#        {"name": "flag2", "type": "boolean", "value":1, "description":"oh see, an unused checkbox"}
    ]
    

    # category map
    categories = ['Google/DMOZ Stations', 'Alternative', 'Ambient', 'Classical', 'College', 'Country', 'Dance', 'Experimental', 'Gothic', 'Industrial', 'Jazz', 'Local', 'Lounge', 'Metal', 'New Age', 'Oldies', 'Old-Time Radio', 'Pop', 'Punk', 'Rock', '80s', 'Soundtracks', 'Talk', 'Techno', 'Urban', 'Variety', 'World']
    catmap = [('Google/DMOZ Stations', '__main', '/Arts/Radio/Internet/'), ['Alternative', 'Alternative', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/Rock/Alternative/'], ['Ambient', 'Ambient', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/Ambient/'], ['Classical', 'Classical', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/Classical/'], ['College', 'College', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/College/'], ['Country', 'Country', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/Country/'], ['Dance', 'Dance', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/Dance/'], ['Experimental', 'Experimental', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/Experimental/'], ['Gothic', 'Gothic', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/Rock/Gothic/'], ['Industrial', 'Industrial', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/Rock/Industrial/'], ['Jazz', 'Jazz', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/Jazz/'], ['Local', 'Local', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/Local/'], ['Lounge', 'Lounge', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/Lounge/'], ['Metal', 'Metal', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/Rock/Metal/'], ['New Age', 'New Age', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/New_Age/'], ['Oldies', 'Oldies', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/Rock/Oldies/'], ['Old-Time Radio', 'Old-Time Radio', '/Arts/Radio/Formats/Old-Time_Radio/Streaming_MP3_Stations/'], ['Pop', 'Pop', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/Pop/'], ['Punk', 'Punk', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/Rock/Punk/'], ['Rock', 'Rock', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/Rock/'], ['80s', '80s', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/80s/'], ['Soundtracks', 'Soundtracks', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/Soundtracks/'], ['Talk', 'Talk', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/Talk/'], ['Techno', 'Techno', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/Dance/Techno/'], ['Urban', 'Urban', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/Urban/'], ['Variety', 'Variety', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/Variety/'], ['World', 'World', '/Arts/Music/Sound_Files/MP3/Streaming/Stations/World/']]


    #def __init__(self, parent):
    #    #self.update_categories()
    #    ChannelPlugin.__init__(self, parent)


    # refresh category list
    def update_categories(self):
    
        # interim data structure for categories (label, google-id/name, url)
        categories = [
            ("Google/DMOZ Stations", "__main", "/Arts/Radio/Internet/"),
        ]
        
        # fetch and extract list
        html = http.get(GOOGLE_DIRECTORY_ROOT + CATEGORIES_URL_POSTFIX)

        for row in re_category.findall(html):
            if row:
                name = entity_decode(row[2])
                label = name

                href = entity_decode(row[0])
                if href[0] != "/":
                    href = CATEGORIES_URL_POSTFIX + href
                   
                categories.append([label, name, href])

        # return
        self.catmap = categories
        self.categories = [x[0] for x in categories]
        pass
        # actually saving this into _categories and _catmap.json would be nice
        # ...



    # download links from dmoz listing
    def update_streams(self, cat, force=0):

        # result list
        ls = []    
        
        # get //dmoz.org/HREF for category name
        try:
            (label, name, href) = [x for x in self.catmap if x[0]==cat][0]
        except:
            return ls  # wrong category

        # download
        html = http.get(GOOGLE_DIRECTORY_ROOT + href)
        
        # filter
        for row in re_stream_desc.findall(html):
            
            if row:
                row = {
                    "homepage": entity_decode(row[0]),
                    "title": entity_decode(row[1]),
                    "playing": entity_decode(row[3]),
                }
                ls.append(row)


        # final list for current category
        return ls
        


