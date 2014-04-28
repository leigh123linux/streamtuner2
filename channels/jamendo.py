
# api: streamtuner2
# title: jamendo browser
#
# For now this is really just a browser, doesn't utilizt the jamendo API yet.
# Requires more rework of streamtuner2 list display to show album covers.
#
# Recently required an API key as well. Thus probably will remain a stub.
#
#


import re
import ahttp as http
from config import conf
from channels import *
from xml.sax.saxutils import unescape














# jamendo CC music sharing site
class jamendo (ChannelPlugin):

    # description
    title = "Jamendo"
    module = "jamendo"
    homepage = "http://www.jamendo.com/"
    version = 0.2

    base = "http://www.jamendo.com/en/"
    listformat = "url/http"

    categories = []  #"top 100", "reload category tree!", ["menu > channel > reload.."]]
    titles = dict( title="Artist", playing="Album/Song", bitrate=False, listeners=False )
 
    config = [
        {"name":"jamendo_stream_format", "value":"ogg2", "type":"text", "description":"streaming format, 'ogg2' or 'mp31'"}
    ]    
    



    # refresh category list
    def update_categories(self):

        html = http.get(self.base + "tags")

        rx_current = re.compile(r"""
             <a\s[^>]+rel="tag"[^>]+href="(http://www.jamendo.com/\w\w/tag/[\w\d]+)"[^>]*>([\w\d]+)</a>
        """, re.S|re.X)


        #-- categories
        tags = []
        for uu in rx_current.findall(html):
            (href, title) = uu
            tags.append(title)
            
        self.categories = [
           "radios",
#           "tags", tags
        ]
        


    # download links from dmoz listing
    def update_streams(self, cat, force=0):

        entries = []
        
        # return a static list for now
        if cat == "radios":
        
            entries = [
                {"title": "Pop", "url": "http://streaming.radionomy.com/JamPop", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios"},
                {"title": "Rock", "url": "http://streaming.radionomy.com/JamRock", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios"},
                {"title": "Lounge", "url": "http://streaming.radionomy.com/JamLounge", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios"},
                {"title": "Electro", "url": "http://streaming.radionomy.com/JamElectro", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios"},
                {"title": "HipHop", "url": "http://streaming.radionomy.com/JamHipHop", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios"},
                {"title": "World", "url": "http://streaming.radionomy.com/JamWorld", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios"},
                {"title": "Jazz", "url": "http://streaming.radionomy.com/JamJazz", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios"},
                {"title": "Metal", "url": "http://streaming.radionomy.com/JamMetal", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios"},
                {"title": "Soundtrack", "url": "http://streaming.radionomy.com/JamSoundtrack", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios"},
                {"title": "Relaxation", "url": "http://streaming.radionomy.com/JamRelaxation", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios"},
                {"title": "Classical", "url": "http://streaming.radionomy.com/JamClassical", "playing": "", "format": "audio/mpeg", "homepage": "http://www.jamendo.com/en/radios"},
            ]
        
        return entries
    
        # top list
        if cat == "top" or cat == "top 100":
            html = http.get(self.base + "top")

	    rx_top = re.compile("""
		<img[^>]+src="(http://imgjam.com/albums/[\w\d]+/\d+/covers/1.\d+.jpg)"
		.*?
		<a\stitle="([^"]+)\s*-\s*([^"]+)"\s+class="track_name"\s+href="(http://www.jamendo.com/\w+/track/(\d+))"
	    """, re.X|re.S)

	    for uu in rx_top.findall(html):
		(cover, title, artist, track, track_id) = uu
		entries.append({
		    "title": artist,
		    "playing": title,
		    "homepage": track,
		    "url": self.track_url(track_id, conf.jamendo_stream_format),
		    "favicon": self.cover(cover),
		    "format": self.stream_mime(),
		})
		
		
        # genre list            
        else:
            html = http.get(self.base + "tag/" + cat)
            
            rx_tag = re.compile("""
		<a\s+title="([^"]+)\s*-\s*([^"]+)"
		\s+href="(http://www.jamendo.com/\w+/album/(\d+))"\s*>
		\s*<img[^>]+src="(http://imgjam.com/albums/[\w\d]+/\d+/covers/1.\d+.jpg)"
		.*? /tag/([\w\d]+)"
            """, re.X|re.S)

	    for uu in rx_tag.findall(html):
		(artist, title, album, album_id, cover, tag) = uu
		entries.append({
		    "title": artist,
		    "playing": title,
		    "homepage": album,
		    "url": self.track_url(album_id, conf.jamendo_stream_format, "album"),
		    "favicon": self.cover(cover),
		    "genre": tag,
		    "format": self.stream_mime(),
		})
 
        # done    
        return entries
        
        
    # smaller album link
    def cover(self, url):
        return url.replace(".100",".50").replace(".130",".50")
     
    # track id to download url   
    def track_url(self, track_id, fmt="ogg2", track="track", urltype="redirect"):
        # track = "album"
        # fmt = "mp31"
        # urltype = "m3u"
	return "http://api.jamendo.com/get2/stream/"+track+"/"+urltype+"/?id="+track_id+"&streamencoding="+fmt

    # audio/*
    def stream_mime(self):
        if conf.jamendo_stream_format.find("og") >= 0:
            return "audio/ogg"
        else:
            return "audio/mp3"


