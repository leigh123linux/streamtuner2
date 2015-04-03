# api: streamtuner2
# title: Internet-Radio
# description: Broad list of webradios from all genres.
# type: channel
# category: radio
# version: 1.2
# url: http://www.internet-radio.org.uk/
# config:
#    { name: internetradio_max_pages,  type: int,  value: 5,  category: limit,  description: How many pages to fetch and read. }
# priority: standard
# png:
#   iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAaZJREFUOI2N0j1PlEEUBeBnlsVoRJcCPwINxIJGAoWVFbVK4g8w
#   oUUTFRNbG3+FhVErK36BhcYCrTR8FS4mRGUXFEKCUizRwLXgnfV1Awk3mUzmnHPvPXNnUkSE40RKFYxhHKMYxFb1GIlnMLVN/etBUjuGWDm6wEHHyQbLW/Qd
#   JTu8QEq9mJlnogz3sHOJV3iHz2iKzuDiH+bm+J3XD74EU5Gc7pSn/4aYUi14s8BIhkZ5puKhvdgpNFVccaA5oaP7TO66SCuYKnG9weMmjaz5yadqqfvkPE/z
#   8TLTIp4U3I01ljY5f/gQu1LPGvWS7Rel5NtLzOzRlfk+Ngd4i48Ke9PZVpNGUCvwawvsZm6db8GtoLt9s4iIFotZFEwXybU1VjO+z4egv/MVKlIaqTMMJ2nh
#   eeH0wQYX4BwbiQkRTSmdktJ1KY3lGYznuw3zWsS2lLo2WMl4P49ycjCbn3k0pfuVg5m1432e4zr9UGMbLwv8avmP/OJOBQOlAsvF3hYNMititzg2Kuxn7iyr
#   VbSG/tltFHt3CVvATRBRH0lpEvfwXXL3L9zE/NEe0EfHAAAAAElFTkSuQmCC
#
# Internet-Radio.co.uk/.com is one of the largest stream directories.
# Available music genre classifications are mirrored verbatim and flatly.
#
# The new version of this plugin alternates between PyQuery and Regex
# station extraction. Both overlook some paid or incomplete entries.
# HTTP retrieval happens in one batch, determined by the number of pages
# setting, rather than the global max_streams option.
#


from channels import *
import re
from config import conf, __print__, dbg
import ahttp as http
from pq import pq




# streams and gui
class internet_radio (ChannelPlugin):


    # description
    title = "InternetRadio"
    module = "internet_radio"
    homepage = "http://www.internet-radio.org.uk/"
    listformat = "audio/x-scpls"
    
    # category map
    categories = []
    current = ""
    default = ""


    # load genres
    def update_categories(self):
    
        html = http.get(self.homepage)
        rx = re.compile("""="/stations/[-+&.\w\s%]+/">([^<]+)<""")
        cats = rx.findall(html)
        cats = list(set(cats))
        cats = [s.capitalize() for s in cats]
        self.categories = sorted(cats)


    # fetch station lists
    def update_streams(self, cat):
    
        entries = []
        if cat not in self.categories:
            return []

        rx_pages = re.compile('href="/stations/[-+\w%\d\s]+/page(\d+)">\d+</a>')

        # Fetch multiple pages at once
        html = []
        max_pages = max(int(conf.internetradio_max_pages), 1)
        for page in range(1, max_pages):
        
            # Append HTML source
            html.append(
                http.get(
                    self.homepage + "stations/" +
                    cat.lower().replace(" ", "%20") +
                    "/" + ("page"+str(page) if page>1 else "")
                )
            )

            # Is there a next page?
            if str(page+1) not in rx_pages.findall(html[-1]):
                break
            self.parent.status(float(page)/float(max_pages+1))

        # Alternatively try regex or pyquery parsing
        #__print__(dbg.HTTP, html)
        for use_rx in [not conf.pyquery, conf.pyquery]:
            try:
                entries = (self.with_regex(html) if use_rx else self.with_dom(html))
                if len(entries):
                    break
            except Exception as e:
                __print__(dbg.ERR, e)
                continue
            
        # fin
        return entries


    # Regex extraction
    def with_regex(self, html):
        __print__(dbg.PROC, "internet-radio, regex")
        r = []
        html = "\n".join(html)
        
        # Break up into <tr> blocks before extracting bits
        rx_tr = re.compile("""<tr[^>]*>(.+?)</tr>""", re.S)
        rx_data = re.compile(r"""
               playjp',\s*'(https?://[^'">]+)
               .*?   <h4.*?>([^<>]+)</
               .*?   <b>([^<>]*)</b>
         (?:   .*?   href="(.*?)"        )?
         (?:   .*?   Genres:((?:</?a[^>]+>|\w+|\s+)+)    )?
               .*?   (\d+)\s*Listeners
               .*?   (\d+)\s*Kbps
        """, re.S|re.X)

        for div in rx_tr.findall(html):
            if div.find('id="pagination"') < 0:
                #__print__(dbg.DATA, len(div))
                uu = rx_data.search(div)
                if uu:
                    (url, title, playing, homepage, genres, listeners, bitrate) = uu.groups()
                    
                    # transform data
                    r.append({
                        "url": url,
                        "genre": self.strip_tags(genres or ""),
                        "homepage": http.fix_url(homepage or ""),
                        "title": (title or "").strip().replace("\n", " "),
                        "playing": (playing or "").strip().replace("\n", " "),
                        "bitrate": int(bitrate or 0),
                        "listeners": int(listeners or 0),
                        "format": "audio/mpeg", # there is no stream info on that, but internet-radio.org.uk doesn't seem very ogg-friendly anyway, so we assume the default here
                    })
                else:
                    __print__(dbg.ERR, "rx missed", div)
        return r


    # DOM traversing
    def with_dom(self, html_list):
        __print__(dbg.PROC, "internet-radio, dom")
        rx_numbers = re.compile("(\d+)")
        r = []
        for html in html_list:
            # the streams are arranged in table rows
            doc = pq(html)
            for dir in (pq(e) for e in doc("tr")):
                
                # bitrate/listeners
                bl = dir.find("p").text()
                bl = rx_numbers.findall(str(bl) + " 0 0")
                
                # stream url
                url = dir.find("i").eq(0).attr("onclick")
                if url:
                    url = re.search("(http://[^\'\"\>]+)", url)
                    if url:
                        url = url.group(0)
                    else:
                        url = ""
                else:
                    url = ""
                
                r.append({
                    "title": dir.find("h4").text(),
                    "homepage": http.fix_url(dir.find("a.small").attr("href")),
                    "url": url,
                    "genre": dir.find("a[href^='/stations/']").text(),
                    "listeners": int(bl[0]),
                    "bitrate": int(bl[1]),
                    "format": "audio/mpeg",
                    "playing": dir.find("b").text(),
                })
        return r
            


