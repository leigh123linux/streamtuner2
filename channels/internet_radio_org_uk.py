#
# api: streamtuner2
# title: Internet-Radio.com
# description: Broad list of webradios from all genres.
# type: channel
# category: radio
# version: 0.2
# priority: standard
#
#
# Might become new main plugin
#
#
#



from channels import *
import re
from config import conf, __print__, dbg
import ahttp as http
from pq import pq




# streams and gui
class internet_radio_org_uk (ChannelPlugin):


    # description
    title = "InternetRadio"
    module = "internet_radio_org_uk"
    homepage = "http://www.internet-radio.org.uk/"
    listformat = "audio/x-scpls"
    
    # settings
    config = [
        {"name":"internetradio_max_pages", "type":"int", "value":5, "description":"How many pages to fetch and read."},
    ]
    

    # category map
    categories = []
    current = ""
    default = ""


    # load genres
    def update_categories(self):
    
        html = http.get(self.homepage)
        rx = re.compile("""<option[^>]+value="/stations/[-+&.\w\s%]+/">([^<]+)</option>""")
        
        self.categories = rx.findall(html)





    # fetch station lists
    def update_streams(self, cat, force=0):    
    
        entries = []
        if cat not in self.categories:
            return []
            
        # regex
        #rx_div = re.compile('<tr valign="top" class="stream">(.+?)</tr>', re.S)
        rx_data = re.compile("""
		(?:M3U|PLS)',\s*'(http://[^']+)'
		.*?
		<br><br>([^\n]*?)</td>
		.*?
		(?:href="(http://[^"]+)"[^>]+target="_blank"[^>]*)?
		>\s*
		<b>\s*(\w[^<]+)[<\n]
		.*?
		playing\s*:\s*([^<\n]+)
		.*?
                (\d+)\s*Kbps
                (?:<br>(\d+)\s*Listeners)?
        """, re.S|re.X)
        #rx_homepage = re.compile('href="(http://[^"]+)"[^>]+target="_blank"')
        rx_pages = re.compile('href="/stations/[-+\w%\d\s]+/page(\d+)">\d+</a>')
        rx_numbers = re.compile("(\d+)")
        self.parent.status("downloading category pages...")


        # multiple pages
        page = 1
        max = int(conf.internetradio_max_pages)
        max = (max if max > 1 else 1)
        while page <= max:
        
            # fetch
            html = http.get(self.homepage + "stations/" + cat.lower().replace(" ", "%20") + "/" + ("page"+str(page) if page>1 else ""))


            # regex parsing?
            if not conf.pyquery:            
                # step through
                for uu in rx_data.findall(html):
                    (url, genre, homepage, title, playing, bitrate, listeners) = uu
                    
                    # transform data
                    entries.append({
                        "url": url,
                        "genre": self.strip_tags(genre),
                        "homepage": http.fix_url(homepage),
                        "title": title,
                        "playing": playing,
                        "bitrate": int(bitrate),
                        "listeners": int(listeners if listeners else 0),
                        "format": "audio/mpeg", # there is no stream info on that, but internet-radio.org.uk doesn't seem very ogg-friendly anyway, so we assume the default here
                    })

            # DOM parsing
            else:
                # the streams are arranged in table rows
                doc = pq(html)
                for dir in (pq(e) for e in doc("tr.stream")):
                    
                    bl = dir.find("td[align=right]").text()
                    bl = rx_numbers.findall(str(bl) + " 0 0")
                    
                    entries.append({
                        "title": dir.find("b").text(),
                        "homepage": http.fix_url(dir.find("a.url").attr("href")),
                        "url": dir.find("a").eq(2).attr("href"),
                        "genre": dir.find("td").eq(0).text(),
                        "bitrate": int(bl[0]),
                        "listeners": int(bl[1]),
                        "format": "audio/mpeg",
                        "playing": dir.find("td").eq(1).children().remove().end().text()[13:].strip(),
                    })
            
            # next page?
            if str(page+1) not in rx_pages.findall(html):
                max = 0
            else:
                page = page + 1

            # keep listview updated while searching
            self.update_streams_partially_done(entries)
            try: self.parent.status(float(page)/float(max))
            except: """there was a div by zero bug report despite max=1 precautions"""
            
        # fin
        self.parent.status()
        return entries


