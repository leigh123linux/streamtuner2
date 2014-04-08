
# api: streamtuner2
# title: jamendo browser
#
# For now this is really just a browser, doesn't utilizt the jamendo API yet.
# Requires more rework of streamtuner2 list display to show album covers.
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
           "top 100",
           "radios",
           "tags", tags
        ]
        


    # download links from dmoz listing
    def update_streams(self, cat, force=0):

        entries = []
    
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
		
		
        # static
        elif cat == "radios":

            rx = '>(\w+[-/\s]*\w+)</a>.+?/(get2/stream/track/m3u/radio_track_inradioplaylist/[?]order=numradio_asc&radio_id=\d+)"'
            for uu in re.findall(rx, http.get(self.base + "radios")):
                (name, url) = uu
                entries.append({
                    "title": name,
                    "url": self.homepage,
                    "homepage": self.base + "radios",
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


