# api: streamtuner2
# title: Internet-Radio
# description: Broad list of webradios from all genres.
# type: channel
# category: radio
# version: 1.5
# url: http://www.internet-radio.com/
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
# extraction-method: regex, dom
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
from config import *
import ahttp
from pq import pq




# streams and gui
class internet_radio (ChannelPlugin):

    # control data
    listformat = "pls"
    categories = []
    base_url = "https://www.internet-radio.com/"
    has_search = True


    # load genres
    def update_categories(self):
    
        html = ahttp.get(self.base_url)
        rx = re.compile("""="/stations/[-+&.\w\s%]+/">([^<]+)<""")
        cats = rx.findall(html)
        cats = list(set(cats))
        cats = [s.capitalize() for s in cats]
        self.categories = sorted(list(set(cats)))


    # fetch station lists
    def update_streams(self, cat, search=None):
    
        entries = []
        if not search and cat not in self.categories:
            return []

        rx_pages = re.compile('href="/stations/[-+\w%\d\s]+/page(\d+)">\d+</a>')

        # Fetch multiple pages at once
        html = []
        max_pages = max(int(conf.internetradio_max_pages), 1)
        for page in range(1, max_pages):
        
            # Append HTML source
            if search:
                html.append(
                    ahttp.get("%ssearch/?radio=%s%s" % (self.base_url, search, "&page=%s" % page if page>1 else ""))
                )
            else:
                html.append(
                    ahttp.get("%sstations/%s/%s" % (self.base_url, cat.lower().replace(" ", "%20"), "page%s" % page if page>1 else ""))
                )

            # Is there a next page?
            if str(page+1) not in rx_pages.findall(html[-1]):
                break
            self.parent.status(float(page)/float(max_pages+1), timeout=1)

        # Alternatively try regex or pyquery parsing
        #log.HTTP(html)
        entries = self.from_html(html)
            
        # fin
        log.FINISHED("internet_radio.update_streams")
        return entries


    # Switch update method
    @use_rx
    def from_html(self, html, use_rx):
        if use_rx:
            return self.with_regex(html)
        else:
            return self.with_dom(html)


    # Regex extraction
    def with_regex(self, html):
        log.PROC("internet-radio, regex")
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
                #log.DATA(len(div))
                uu = rx_data.search(div)
                if uu:
                    (url, title, playing, homepage, genres, listeners, bitrate) = uu.groups()
                    
                    # transform data
                    r.append({
                        "url": url,
                        "genre": strip_tags(genres or ""),
                        "homepage": ahttp.fix_url(homepage or ""),
                        "title": nl(title or ""),
                        "playing": nl(playing or ""),
                        "bitrate": int(bitrate or 0),
                        "listeners": int(listeners or 0),
                        "format": "audio/mpeg", # there is no stream info on that, but internet-radio.org.uk doesn't seem very ogg-friendly anyway, so we assume the default here
                    })
                else:
                    log.DATA("Regex couldn't decipher entry:", div)
        return r


    # DOM traversing
    def with_dom(self, html_list):
        log.PROC("internet-radio, dom")
        rx_numbers = re.compile("(\d+)")
        r = []
        for html in html_list:
            # the streams are arranged in table rows
            doc = pq(html)
            for dir in (pq(e) for e in doc("tr")):
                #log.HTML(dir)
                
                # bitrate/listeners
                bl = dir.find("p")
                if bl:
                    bl = rx_numbers.findall(str(bl.text()) + " 0 0")
                else:
                    bl = [0, 0]
                
                # stream url
                url = dir.find("i").eq(0).parent().attr("onclick")
                if url:
                    url = re.search("(http://[^\'\"\>]+)", url)
                    if url:
                        url = url.group(0)
                    else:
                        url = ""
                else:
                    url = ""
                
                row = {
                    "title": dir.find("h4").text(),
                    "homepage": ahttp.fix_url(dir.find("a.small").attr("href") or ""),
                    "url": url,
                    "genre": dir.find("a[href^='/stations/']").text() or "",
                    "listeners": int(bl[0]),
                    "bitrate": int(bl[1]),
                    "format": "audio/mpeg",
                    "playing": dir.find("b").text(),
                }
                #log.DATA(row)
                r.append(row)
        return r
            


